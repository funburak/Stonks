from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField
from wtforms.validators import InputRequired, Length, Email, EqualTo

class SignupForm(FlaskForm):
    email = EmailField('Email', validators=[InputRequired(), Email()])
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15,
                                                                           message='Username must be between 4 and 15 characters')])
    password = PasswordField('Password', validators=[InputRequired()])

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])

class ForgotPasswordForm(FlaskForm):
    email = EmailField('Email', validators=[InputRequired(), Email()])

class ChangePasswordForm(FlaskForm):
    new_password = PasswordField('New Password', validators=[InputRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[InputRequired(), EqualTo('new_password', message='Passwords must match')])

class UpdateEmailForm(FlaskForm):
    email = EmailField('Email', validators=[InputRequired(), Email()])

class UpdateUsernameForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15,
                                                                           message='Username must be between 4 and 15 characters')])