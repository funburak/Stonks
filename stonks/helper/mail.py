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
            stock_list = ', '.join(stocks)
            subject = 'Stock Price Change'
            body = f"The following stocks have changed by more than %1: {stock_list}"
            msg = Message(subject, recipients=[mail])
            msg.body = body
            try:
                self.mail.send(msg)
            except:
                print('Failed to send email')
                return False
        return True
