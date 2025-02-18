from sqlalchemy.orm import Mapped, mapped_column, relationship
import bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
import jwt
import logging

database = SQLAlchemy()

# Association table for the many-to-many relationship between watchlist and stock
watchlist_stock_association = database.Table(
    'watchlist_stock',
    database.Column('watchlist_id', database.Integer, database.ForeignKey('watchlist.id'), primary_key=True),
    database.Column('stock_id', database.Integer, database.ForeignKey('stock.id'), primary_key=True)
)

class User(UserMixin, database.Model):
    """
    User model for the database

    Attributes:
        id (int): The user ID
        username (str): The username of the user
        email (str): The email of the user
        email_verified (bool): Whether the email is verified
        created_at (datetime): Date of account creation
        profile_picture (str): URL to the profile picture
        notification_enabled (bool): Whether to send notifications to the user
        password (str): The hashed password of the user
        watchlist (Watchlist): The watchlist of the user

    Methods:
        set_password: Set the password of the user
        check_password: Check if the password is correct
        generate_reset_token: Generate a token for resetting the password
        check_token: Check if the token is valid
        generate_email_change_token: Generate a token for changing the email
        check_email_change_token: Check if the email change token is valid
    """
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(database.String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(database.String(120), unique=True, nullable=False)
    email_verified: Mapped[bool] = mapped_column(database.Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(database.DateTime, default=datetime.now) # Date of account creation
    profile_picture: Mapped[str] = mapped_column(database.String(255), nullable=True) # URL to the profile picture
    notification_enabled: Mapped[bool] = mapped_column(database.Boolean, default=True) # Whether to send notifications to the user
    password:  Mapped[str] = mapped_column(database.String(256), nullable=False)
    watchlist = relationship('Watchlist', uselist=False, back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password):
        """
        Hash the password and set it for the user

        Args:
            password (str): The password to hash
        """
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        """
        Check if the password is correct

        Args:
            password (str): The password to check
        """
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
    
    def generate_reset_token(self,app=None, expire_time=600):
        """
        Generate a token for resetting the password

        Args:
            app (Flask): The Flask app
            expire_time (int): Time in seconds for the token to expire

        Returns:
            str: The token for resetting the password
        """
        if app is None:
            raise ValueError('app must be provided')
        
        payload = {
            'user_id': self.id,
            'exp': datetime.now() + timedelta(seconds=expire_time)
        }
        return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    
    @staticmethod
    def check_token(token,app=None):
        """
        Check if the token is valid

        Args:
            token (str): The token to check
            app (Flask): The Flask app

        Returns:
            User: The user if the token is valid
        """
        if app is None:
            raise ValueError('app must be provided')
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            return User.query.get(payload['user_id'])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        
    def generate_email_change_token(self, new_email, app=None, expire_time=600):
        """
        Generate a token for changing the email

        Args:
            new_email (str): The new email
            app (Flask): The Flask app
            expire_time (int): Time in seconds for the token to expire

        Returns:
            str: The token for changing the email
        """
        if app is None:
            raise ValueError('app must be provided')
        
        payload = {
            'user_id': self.id,
            'new_email': new_email,
            'exp': datetime.now() + timedelta(seconds=expire_time)
        }
        return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    
    @staticmethod
    def check_email_change_token(token, app=None):
        """
        Check if the email change token is valid

        Args:
            token (str): The token to check
            app (Flask): The Flask app
        
        Returns:
            Tuple[User, str]: The user and the new email if the token is valid 
        """
        if app is None:
            raise ValueError('app must be provided')

        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            user = User.query.filter_by(id=payload.get('user_id')).first()

            if user:
                return user, payload.get('new_email')  # Return the user and the new email
            return None, None

        except jwt.ExpiredSignatureError:
            logging.error('Token expired')
            return None, None  # Token expired
        except jwt.DecodeError:
            logging.error('Invalid token: Decode Error')
            return None, None  # Invalid token
        except jwt.InvalidTokenError:
            logging.error('Invalid token')
            return None, None  # Other JWT-related issues

class Watchlist(database.Model):
    """
    Watchlist model for the database

    Attributes:
        id (int): The watchlist ID
        user_id (int): The user ID
        user (User): The user of the watchlist
        stocks (List[Stock]): The stocks in the watchlist
    """
    __tablename__ = 'watchlist'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id = mapped_column(database.Integer, database.ForeignKey('user.id'))
    user = relationship('User', back_populates='watchlist')
    stocks = relationship('Stock', secondary=watchlist_stock_association, back_populates='watchlists')

class Stock(database.Model):
    """
    Stock model for the database

    Attributes:
        id (int): The stock ID
        symbol (str): Stock symbol
        current_price (float): Current price of the stock
        percent_change (float): Percent change in price
        last_updated_at (datetime): Date of last update of the stock price
        watchlists (List[Watchlist]): The watchlists containing the stock
    """
    __tablename__ = 'stock'

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(unique=True, nullable=False) # Stock symbol
    current_price: Mapped[float] = mapped_column(nullable=False) # Current price of the stock
    percent_change: Mapped[float] = mapped_column(nullable=False) # Percent change in price
    last_updated_at: Mapped[datetime] = mapped_column(nullable=False) # Date of last update of the stock price

    watchlists = relationship('Watchlist', secondary=watchlist_stock_association, back_populates='stocks')