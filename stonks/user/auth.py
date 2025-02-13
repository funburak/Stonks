from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, jsonify
from stonks.user.forms import SignupForm, LoginForm, ForgotPasswordForm, ChangePasswordForm, UpdateEmailForm, UpdateUsernameForm
from stonks.user.models import User, Watchlist, database
from flask_login import login_required, login_user, logout_user, current_user
from datetime import datetime
import cloudinary
import cloudinary.uploader
import logging
import os

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    # # If the user is already logged in, redirect to the homepage
    if current_user.is_authenticated:
        flash('Logout to sign up', 'info')
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
            email = email,
            created_at = datetime.now()
        )

        user.watchlist = Watchlist(user=user)
        user.set_password(password) # Hash the password
        session['autofill_username'] = user.username # Autofill username in login form

        database.session.add(user)
        database.session.commit()
        logging.info(f'User {user.username} signed up successfully')
        flash("Signed up successfully", 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/signup.html', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    # If the user is already logged in, redirect to the homepage
    if current_user.is_authenticated and not session.get('autofill_username'):
        return redirect(url_for('dashboard.homepage'))
    
    form = LoginForm(request.form)

    if 'autofill_username' in session: # Autofill username if user just signed up
        form.username.data = session['autofill_username']
        session.pop('autofill_username')

    if request.method == 'POST' and form.validate_on_submit():
        password = form.password.data

        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(password):
            login_user(user=user)
            session.permanent = True
            flash(f'Welcome to Stonks! {current_user.username}', 'success')
            logging.info(f"User {current_user.username} logged in")
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
                logging.info(f"Reset password email sent to {email}")
                flash('Reset password email sent', 'success')
            else:
                logging.info(f"Failed to send reset password email to {email}")
                flash('Failed to send email', 'danger')
        else:
            logging.info(f"Email {email} not found")
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
        logging.info(f"Password reset for user {user.username}")
        flash('Password reset successfully', 'success')
        return redirect(url_for('auth.login'))
    else:
        return render_template('auth/reset_password.html', form=form, token=token)

@auth.route('/profile')
@login_required
def profile_page():
    user = User.query.filter_by(id=current_user.id).first()
    username_form = UpdateUsernameForm()
    email_form = UpdateEmailForm()
    if user:
        return render_template('auth/profile.html', user=user, username_form=username_form, email_form=email_form)
    else:
        flash('User not found', 'danger')
        return redirect(url_for('auth.login'))

@auth.route('/upload_profile_picture', methods=['POST'])
@login_required
def upload_profile_picture():
    if 'profile_picture' not in request.files:
        flash("No file selected!", "danger")
        return redirect(url_for('auth.profile_page'))
    
    file = request.files['profile_picture']
    if file.filename == '':
        flash("No file selected!", "danger")
        return redirect(url_for('auth.profile_page'))
    
    try:
        cloudinary.config(
            cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'),
            api_key = os.getenv('CLOUDINARY_API_KEY'),
            api_secret = os.getenv('CLOUDINARY_API_SECRET'),
            secure=True
        )
        upload_result = cloudinary.uploader.upload(file, folder='profile_pictures', public_id=str(current_user.id))
        new_image_url = upload_result['secure_url']

        current_user.profile_picture = new_image_url
        database.session.commit()
        flash("Profile picture uploaded successfully", "success")
        logging.info(f"Profile picture uploaded for user {current_user.username}")
    except Exception as e:
        logging.error(f"Failed to upload profile picture for user {current_user.username}: {e}")
        flash("Failed to upload profile picture", "danger")

    return redirect(url_for('auth.profile_page'))

@auth.route('/toggle_notifications', methods=['POST'])
@login_required
def toggle_notifications():
    data = request.get_json()

    if 'notification_enabled' in data:
        current_user.notification_enabled = data['notification_enabled']
        database.session.commit()
        return jsonify({'success': True}), 200
    
    return jsonify({'error': False}), 400

@auth.route('/update_user/<field>', methods=['POST'])
@login_required
def update_user(field):
    if field == 'username':
        form = UpdateUsernameForm(request.form)
    elif field == 'email':
        form = UpdateEmailForm(request.form)
        flash('Email update not supported yet', 'danger')
        return redirect(url_for('auth.profile_page'))
    else:
        return redirect(url_for('auth.profile_page'))
    
    if form.validate_on_submit():
        new_value = form.data[field]

        if User.query.filter(getattr(User, field) == new_value).first():
            flash(f'{field.capitalize()} already taken', 'danger')
            return redirect(url_for('auth.profile_page'))
        
        setattr(current_user, field, new_value)
        database.session.commit()
        flash(f'{field.capitalize()} updated successfully', 'success')
        logging.info(f"{field.capitalize()} updated for user {current_user.username}")
    else:
        flash('Invalid input', 'danger')
        return redirect(url_for('auth.profile_page'))
    
    return redirect(url_for('auth.profile_page'))

@auth.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user = User.query.filter_by(id=current_user.id).first()
    if user:
        try:
            cloudinary.config(
                cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'),
                api_key = os.getenv('CLOUDINARY_API_KEY'),
                api_secret = os.getenv('CLOUDINARY_API_SECRET'),
                secure=True
            )
            cloudinary.uploader.destroy(f'profile_pictures/{user.id}') # Delete the profile picture from Cloudinary
            logout_user()
            database.session.delete(user)
            database.session.commit()
            flash('Account deleted successfully', 'success')
            logging.info(f"{user.username} deleted account")
            return render_template('auth/signup.html', form=SignupForm())
        except Exception as e:
            logging.error(f"Failed to delete account for user {user.username}: {e}")
            flash('Failed to delete account', 'danger')
    else:
        logging.info(f"User not found")
        flash('User not found', 'danger')
        return redirect(url_for('auth.login'), 404)
    
@auth.route('/logout', methods=['POST'])
@login_required
def logout():
    logging.info(f"{current_user.username} loggedd out")
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('auth.login'))
