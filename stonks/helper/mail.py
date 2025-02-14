from flask import url_for
from flask_mail import Mail, Message

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
        
    def send_watchlist_report(self, receipent, report):
        msg = Message('Daily Report', recipients=receipent)
        msg.body = report
        try:
            self.mail.send(msg)
            return True
        except:
            print('Failed to send email')
            return False
        
    def send_change_mail(self, stock_symbols):
        for mail, stocks in stock_symbols.items():
            if not stocks:
                continue
            stock_list = "\n".join(f"- {stock}" for stock in stocks)
            subject = 'Stock Price Alert: Significant Change'
            body = (
                f"The following stocks have changed by more than %2:\n\n"
                f"{stock_list}\n\n"
            )
            msg = Message(subject, recipients=[mail])
            msg.body = body
            try:
                self.mail.send(msg)
            except:
                print('Failed to send email')
                return False
        return True

    def send_mail_change_verification(self, token, recipient):
        subject = 'Email Change Confirmation'
        confirm_url = f"{url_for('auth.confirm_email_change', token=token, _external=True)}"
        body = f"Click the link to confirm your email update: {confirm_url} \n This link will expire in 10 minutes"
        msg = Message(subject, recipients=[recipient], body=body)
        try:
            self.mail.send(msg)
            return True
        except:
            print('Failed to send email')
            return False