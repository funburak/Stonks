from flask import Flask, render_template, request, redirect, url_for, session, flash

from stonks.forms import SignupForm, LoginForm, ForgotPasswordForm, ChangePasswordForm
from stonks.models import User, Stock, Watchlist, database
from stonks.config import config
from stonks.mail import MailHandler
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__, template_folder="../templates")

app.config.from_object(config)

csrf = CSRFProtect(app)

mail_handler = MailHandler(app)

database.init_app(app)

with app.app_context():
    database.create_all()

    # Dummy data
    # apple_stock = Stock(symbol='AAPL', current_price=120.0, change=1.0, percent_change=0.5,
    #                     high_price_day=121.0, low_price_day=119.0, open_price_day=119.5)
    # microsoft_stock = Stock(symbol='MSFT', current_price=220.0, change=2.0, percent_change=1.0,
    #                         high_price_day=221.0, low_price_day=219.0, open_price_day=219.5)
    # google_stock = Stock(symbol='GOOGL', current_price=1800.0, change=10.0, percent_change=0.5,
    #                      high_price_day=1810.0, low_price_day=1790.0, open_price_day=1795.0)
    # tesla_stock = Stock(symbol='TSLA', current_price=800.0, change=10.0, percent_change=1.0,
    #                     high_price_day=810.0, low_price_day=790.0, open_price_day=795.0)

    # database.session.add(apple_stock)
    # database.session.add(microsoft_stock)
    # database.session.add(google_stock)
    # database.session.add(tesla_stock)
    # database.session.commit()

@app.route('/')
def homepage():
    if 'username' in session:
        return render_template('homepage.html')
    else:
        flash("You must be logged in to view this page", 'danger')
        return redirect(url_for('login'))

@app.route('/watchlist', methods=['GET', 'POST'])
def watchlist_page():
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()

        if not user.watchlist:
            user.watchlist = Watchlist(user=user)
            database.session.commit()
        user_watchlist = user.watchlist
        if request.method == 'POST':
            stock_symbol = request.form.get('stock')

            stock = Stock.query.filter_by(symbol=stock_symbol).first()
            if stock:
                if stock in user_watchlist.stocks:
                    flash('Stock already in watchlist', 'danger')
                    return redirect(url_for('watchlist_page'))
                else:
                    user_watchlist.stocks.append(stock)
                    database.session.commit()
            else:
                flash('Stock not found', 'danger')
            
            return redirect(url_for('watchlist_page'))
        
        return render_template('stock/watchlist.html', watchlist=user_watchlist)
    else:
        flash('Please login to view your watchlist', 'danger')
        return redirect(url_for('login'))

@app.route('/delete_stock/<int:stock_id>', methods=['POST'])
def delete_stock(stock_id):
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()

        user_watchlist = user.watchlist

        if not user_watchlist:
            flash('Watchlist not found', 'danger')
            return redirect(url_for('watchlist_page'))
        
        # Delete stock from watchlist
        stock = Stock.query.filter_by(id=stock_id).first()

        if stock in user_watchlist.stocks:
            user_watchlist.stocks.remove(stock)
            database.session.commit()
    else:
        flash('Please login to view your watchlist', 'danger')
        return redirect(url_for('login'))
    
    return redirect(url_for('watchlist_page'))

@app.route('/stock_details/<int:stock_id>')
def stock_details(stock_id):
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()

        user_watchlist = user.watchlist

        if not user_watchlist:
            flash('Watchlist not found', 'danger')
            return redirect(url_for('watchlist_page'))
        
        stock = Stock.query.filter(Stock.id == stock_id, Stock.watchlists.contains(user_watchlist)).first()

        if stock:
            return render_template('stock/stock_details.html', stock=stock)
        else:
            flash('Stock not found', 'danger')
            return redirect(url_for('watchlist_page'))
    else:
        flash('Please login to view stock details', 'danger')
        return redirect(url_for('login'))        

@app.route('/signup', methods=['GET', 'POST'])
def signup():

    # If user is already logged in, redirect to homepage
    if 'username' in session:
        return redirect(url_for('homepage'))

    form = SignupForm(request.form)
    if request.method == 'POST' and form.validate_on_submit():
        email = form.email.data
        username = form.username.data
        password = form.password.data

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already taken', 'danger')
            return redirect(url_for('signup'))

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'danger')
            return redirect(url_for('signup'))
                
        user = User(
            username=username,
            email=email,
        )

        user.watchlist = Watchlist(user=user)
        user.set_password(password) # Hash the password
        session['autofill_username'] = user.username # Autofill username in login form

        database.session.add(user)
        database.session.commit()
        flash("Signed up successfully", 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():

    # If user is already logged in, redirect to homepage
    if 'username' in session:
        return redirect(url_for('homepage'))

    form = LoginForm(request.form)

    if 'autofill_username' in session: # Autofill username if user just signed up
        form.username.data = session['autofill_username']
        session.pop('autofill_username')

    if request.method == 'POST' and form.validate_on_submit():
        password = form.password.data

        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(password):
            session['username'] = user.username
            flash('Logged in successfully', 'success')
            return redirect(url_for('homepage'))
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        
    return render_template('auth/login.html', form=form)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm(request.form)

    if request.method == 'POST' and form.validate_on_submit():
        email = form.email.data

        user = User.query.filter_by(email=email).first()
        if user:
            token = user.generate_reset_token(app=app)

            if mail_handler.send_reset_email(token, [email]):
                flash('Reset password link sent to your email', 'success')
            else:
                flash('Failed to send email', 'danger')
        else:
            flash('Email not found', 'danger')
            return redirect(url_for('forgot_password'))
    
    return render_template('auth/forgot_password.html', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.check_token(token=token, app=app)
    if not user:
        flash('Invalid or expired reset token', 'danger')
        return redirect(url_for('login'))
    
    form = ChangePasswordForm(request.form)

    if request.method == 'POST' and form.validate_on_submit():
        new_password = form.new_password.data
        confirm_password = form.confirm_password.data
        
        user.set_password(new_password)
        database.session.commit()

        flash('Password reset successfully', 'success')
        return redirect(url_for('login'))
    else:
        return render_template('auth/reset_password.html', form=form, token=token)

@app.route('/logout')
def logout():
    if 'username' in session:
        session.pop('username')
        flash('Logged out successfully', 'success')

    return redirect(url_for('login'))
