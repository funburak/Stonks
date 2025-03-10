from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, jsonify
from stonks.user.forms import SignupForm, LoginForm, ForgotPasswordForm, ChangePasswordForm, UpdateEmailForm, UpdateUsernameForm, VerifyPasswordForm, OTPForm
from stonks.user.models import User, Watchlist, database
from flask_login import login_required, login_user, logout_user, current_user
from datetime import datetime
import cloudinary
import cloudinary.uploader
import logging
import os
import pyotp
import bcrypt

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    Page for signing up a new user
    """
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
        
        if not generate_otp(username, email, password):
            flash('Failed to send OTP', 'danger')
        
        flash('OTP sent to email', 'success')
        return redirect(url_for('auth.verify_otp'))
        
    return render_template('auth/signup.html', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    Page for logging in a user
    """
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
        if user and user.check_password(password) and user.email_verified:
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
    """
    Page for resetting a user's password
    """
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
    """
    Page for resetting a user's password
    """
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
    """
    Page for the user's profile
    """
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
    """
    Upload the profile picture to Cloudinary for the user
    """
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
    """
    Toggle the notification settings for the user

    Returns:
        JSON: A JSON response with the success status
    """
    data = request.get_json()

    if 'notification_enabled' in data:
        current_user.notification_enabled = data['notification_enabled']
        database.session.commit()
        return jsonify({'success': True}), 200
    
    return jsonify({'error': False}), 400

@auth.route('/update_username', methods=['POST'])
@login_required
def update_username():
    """
    Update the username for the user
    """
    form = UpdateUsernameForm(request.form)

    if form.validate_on_submit():
        new_username = form.username.data

        if User.query.filter_by(username=new_username).first():
            flash('Username already taken', 'danger')
            return redirect(url_for('auth.profile_page'))
        
        current_user.username = new_username
        database.session.commit()
        flash('Username updated successfully', 'success')
        logging.info(f"Username updated for user {current_user.username}")
    else:
        flash('Invalid input', 'danger')
        return redirect(url_for('auth.profile_page'))
    
    return redirect(url_for('auth.profile_page'))

@auth.route('/update_email', methods=['POST'])
@login_required
def update_email():
    """
    Update the email for the user and send a verification email
    """
    form = UpdateEmailForm(request.form)

    if form.validate_on_submit():
        new_email = form.email.data

        if current_user.email == new_email:
            return redirect(url_for('auth.profile_page'))

        if User.query.filter_by(email=new_email).first():
            flash('Email already taken', 'danger')
            return redirect(url_for('auth.profile_page'))
        
        token = User.generate_email_change_token(current_user, new_email, app=current_app)
        mail_handler = current_app.extensions['mail_handler']

        if mail_handler.send_mail_change_verification(token, new_email):
            flash('Email change verification sent', 'success')
            logging.info(f"Email change verification sent to {new_email}")
        else:
            flash('Failed to send email', 'danger')
            return redirect(url_for('auth.profile_page'))
    else:
        flash('Invalid input', 'danger')
        return redirect(url_for('auth.profile_page'))
    
    return redirect(url_for('auth.profile_page'))

@auth.route('/confirm_email_change/<token>', methods=['GET', 'POST'])
@login_required
def confirm_email_change(token):
    """
    Confirm the email change for the user
    """
    user, new_email = User.check_email_change_token(token, app=current_app)
        
    if not user:
        flash('Invalid or expired token', 'danger')
        return redirect(url_for('auth.profile_page'))
    
    form = VerifyPasswordForm(request.form)

    if request.method == 'POST' and form.validate_on_submit():
        password = form.password.data

        if not user.check_password(password):
            flash('Invalid password', 'danger')
            return redirect(url_for('auth.confirm_email_change', token=token))
        
        user.email = new_email
        database.session.commit()
        flash('Email updated successfully', 'success')
        logging.info(f"Email updated for user {user.username}")
        return redirect(url_for('auth.profile_page'))
    
    return render_template('auth/verify_password.html', form=form, token=token)

@auth.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    """
    Delete the account for the user
    """
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
    
def generate_otp(username, email, password):
    """
    Generate an OTP and send it to the user's email. Also store the user's details in the session.
    """
    totp = pyotp.TOTP(pyotp.random_base32(), interval=300) # Generate a TOTP with a 5 minute interval
    otp = totp.now()
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    session['pending_user'] = {
        'username': username,
        'email': email,
        'password': hashed_password,
        'otp': otp,
        'otp_generated_at': datetime.now().astimezone().isoformat()
    }

    mail_handler = current_app.extensions['mail_handler']

    if mail_handler.send_otp_mail(otp, email):
        logging.info(f"OTP sent to {email}")
        return True
    
    logging.info(f"Failed to send OTP to {email}")
    return False

@auth.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    """
    Verify the OTP sent to the user's email
    """
    if 'pending_user' not in session:
        flash('No pending user', 'danger')

    form = OTPForm(request.form)

    if request.method == 'POST' and form.validate_on_submit():
        otp = form.otp.data

        pending_user_info = session['pending_user']

        # Check if OTP is valid
        otp_generated_at = datetime.fromisoformat(pending_user_info['otp_generated_at']).astimezone()

        current_time = datetime.now().astimezone()

        if (current_time - otp_generated_at).total_seconds() > 300:
            flash('OTP expired', 'danger')
            session.pop('pending_user')
            return redirect(url_for('auth.signup'))
        
        if otp == pending_user_info['otp']:
            user = User(
                username=pending_user_info['username'],
                email = pending_user_info['email'],
                password = pending_user_info['password'],
                created_at = datetime.now(),
                email_verified = True
            )

            user.watchlist = Watchlist(user=user)
            session['autofill_username'] = user.username
            database.session.add(user)
            database.session.commit()
            logging.info(f'User {user.username} signed up successfully')
            flash("Signed up successfully", 'success')
            session.pop('pending_user')
            return redirect(url_for('auth.login'))
        else:
            flash('Invalid OTP', 'danger')
            return redirect(url_for('auth.verify_otp'))
        
    return render_template('auth/otp_verify.html', form=form)

@auth.route('/logout', methods=['POST'])
@login_required
def logout():
    """
    Logout the user
    """
    logging.info(f"{current_user.username} logged out")
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('auth.login'))
