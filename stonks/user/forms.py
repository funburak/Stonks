from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField
from wtforms.validators import InputRequired, Length, Email, EqualTo

class SignupForm(FlaskForm):
    """
    Form for user registration

    Attributes:
        email: EmailField: Email of the user
        username: StringField: Username of the user
        password: PasswordField: Password of the user
    """
    email = EmailField('Email', validators=[InputRequired(), Email()])
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15,
                                                                           message='Username must be between 4 and 15 characters')])
    password = PasswordField('Password', validators=[InputRequired()])

class LoginForm(FlaskForm):
    """
    Form for user login

    Attributes:
        username: StringField: Username of the user
        password: PasswordField: Password of the user
    """
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])

class ForgotPasswordForm(FlaskForm):
    """
    Form for password reset

    Attributes:
        email: EmailField: Email of the user
    """
    email = EmailField('Email', validators=[InputRequired(), Email()])

class ChangePasswordForm(FlaskForm):
    """
    Form for changing password

    Attributes:
        new_password: PasswordField: New password of the user
        confirm_password: PasswordField: Confirm new password of the user
    """
    new_password = PasswordField('New Password', validators=[InputRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[InputRequired(), EqualTo('new_password', message='Passwords must match')])

class UpdateEmailForm(FlaskForm):
    """
    Form for updating email

    Attributes:
        email: EmailField: New email of the user
    """
    email = EmailField('Email', validators=[InputRequired(), Email()])

class UpdateUsernameForm(FlaskForm):
    """
    Form for updating username

    Attributes:
        username: StringField: New username of the user
    """
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15,
                                                                           message='Username must be between 4 and 15 characters')])
    
class VerifyPasswordForm(FlaskForm):
    """
    Form for verifying password

    Attributes:
        password: PasswordField: Password of the user
    """
    password = PasswordField('Password', validators=[InputRequired()])

class OTPForm(FlaskForm):
    """
    Form for OTP verification

    Attributes:
        otp: StringField: OTP of the user
    """
    otp = StringField('OTP', validators=[InputRequired(), Length(min=6, max=6)])