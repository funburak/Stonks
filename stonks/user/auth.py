from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from stonks.user.forms import SignupForm, LoginForm, ForgotPasswordForm, ChangePasswordForm
from stonks.user.models import User, Watchlist, database

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():

    # If user is already logged in, redirect to homepage
    if 'username' in session:
        return redirect(url_for('dashboard.homepage'))
    
    form = SignupForm(request.form)
    if request.method == 'POST' and form.validate_on_submit():
        email = form.email.data
        username = form.username.data
        password = form.password.data

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already taken', 'danger')
            return redirect(url_for('auth.signup'))
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'danger')
            return redirect(url_for('auth.signup'))
        
        user = User(
            username=username,
            email = email
        )

        user.watchlist = Watchlist(user=user)
        user.set_password(password) # Hash the password
        session['autofill_username'] = user.username # Autofill username in login form

        database.session.add(user)
        database.session.commit()
        flash("Signed up successfully", 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/signup.html', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to homepage
    if 'username' in session:
        return redirect(url_for('dashboard.homepage'))
    
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
            return redirect(url_for('dashboard.homepage'))
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
        
    return render_template('auth/login.html', form=form)

@auth.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm(request.form)

    if request.method == 'POST' and form.validate_on_submit():
        email = form.email.data

        user = User.query.filter_by(email=email).first()
        if user:
            token = user.generate_reset_token(app=current_app)
            mail_handler = current_app.extensions['mail_handler']

            if mail_handler.send_reset_email(token, [email]):
                flash('Reset password email sent', 'success')
            else:
                flash('Failed to send email', 'danger')
        else:
            flash('Email not found', 'danger')
            return redirect(url_for('auth.forgot_password'))
        
    return render_template('auth/forgot_password.html', form=form)

@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.check_token(token=token, app=current_app)
    if not user:
        flash('Invalid or expired token', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    form = ChangePasswordForm(request.form)

    if request.method == 'POST' and form.validate_on_submit():
        new_password = form.new_password.data
        confirm_password = form.confirm_password.data

        if new_password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        
        user.set_password(new_password)
        database.session.commit()

        flash('Password reset successfully', 'success')
        return redirect(url_for('auth.login'))
    else:
        return render_template('auth/reset_password.html', form=form, token=token)
    
@auth.route('/logout')
def logout():
    if 'username' in session:
        session.pop('username')
        flash('Logged out successfully', 'success')

    return redirect(url_for('auth.login'))
