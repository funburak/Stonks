from flask import url_for
from flask_mail import Mail, Message

class MailHandler:

    def __init__(self,app):
        """
        Initialize the mail handler
        """
        self.mail = Mail(app)

    def send_reset_email(self, token, recipient):
        """
        Sends the reset password email to the user

        Args:
            token (str): The token for resetting the password
            recipient (str): The email of the recipient

        Returns:
            bool: Whether the email was sent successfully
        """
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
        """
        Sends the daily report to the user

        Args:
            receipent (str): The email of the recipient
            report (str): The daily report

        Returns:
            bool: Whether the email was sent successfully
        """
        msg = Message('Daily Report', recipients=receipent)
        msg.body = report
        try:
            self.mail.send(msg)
            return True
        except:
            print('Failed to send email')
            return False
        
    def send_change_mail(self, stock_symbols):
        """
        Sends a notification email to the users if the stock price changes by more than 2%

        Args:
            stock_symbols (Dict[str, List[str]]): The stock symbols and their percentage changes

        Returns:
            bool: Whether the email was sent successfully
        """
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
        """
        Sends the email change verification email to the user

        Args:
            token (str): The token for changing the email
            recipient (str): The email of the recipient

        Returns:    
            bool: Whether the email was sent successfully
        """
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
        
    def send_otp_mail(self, otp, recipient):
        """
        Sends the OTP verification email to the user

        Args:
            otp (str): The OTP for verification
            recipient (str): The email of the recipient

        Returns:
            bool: Whether the email was sent successfully
        """
        subject = 'OTP Verification'
        body = f"Your OTP is: {otp} \n This OTP will expire in 10 minutes"
        msg = Message(subject, recipients=[recipient], body=body)
        try:
            self.mail.send(msg)
            return True
        except:
            print('Failed to send email')
            return False