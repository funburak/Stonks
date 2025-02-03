from flask_mail import Mail, Message
from flask import url_for

class MailHandler:

    def __init__(self,app):
        self.mail = Mail(app)

    def send_reset_email(self, token, recipient):
        msg = Message('Reset Password', recipients=recipient)
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        msg.body = f"Click the link to reset your password \n {reset_url} \n This link will expire in 10 minutes"
        try:
            self.mail.send(msg)
            return True
        except:
            print('Failed to send email')
            return False