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
        
    def send_change_mail(self, receipent, stock_symbol):
        msg = Message('Stock Price Change', recipients=receipent)
        url = url_for('stock.watchlist', _external=True)
        msg.body = f"The stock price at your watchlist for {stock_symbol} has changed more than 5%\n Check it out at {url}"
        try:
            self.mail.send(msg)
            return True
        except:
            print('Failed to send email')
            return False
