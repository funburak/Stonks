from sqlalchemy.orm import Mapped, mapped_column, relationship
import bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
import jwt

database = SQLAlchemy()


watchlist_stock_association = database.Table(
    'watchlist_stock',
    database.Column('watchlist_id', database.Integer, database.ForeignKey('watchlist.id'), primary_key=True),
    database.Column('stock_id', database.Integer, database.ForeignKey('stock.id'), primary_key=True)
)


class User(UserMixin, database.Model):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(database.String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(database.String(120), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(database.DateTime, default=datetime.now) # Date of account creation
    profile_picture: Mapped[str] = mapped_column(database.String(255), nullable=True) # URL to the profile picture
    password:  Mapped[str] = mapped_column(database.String(256), nullable=False)
    watchlist = relationship('Watchlist', uselist=False, back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
    
    def generate_reset_token(self,app=None, expire_time=600):
        if app is None:
            raise ValueError('app must be provided')
        
        payload = {
            'user_id': self.id,
            'exp': datetime.now() + timedelta(seconds=expire_time) - timedelta(hours=3)
        }
        return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    
    @staticmethod
    def check_token(token,app=None):
        if app is None:
            raise ValueError('app must be provided')
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            return User.query.get(payload['user_id'])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

class Watchlist(database.Model):
    __tablename__ = 'watchlist'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id = mapped_column(database.Integer, database.ForeignKey('user.id'))
    user = relationship('User', back_populates='watchlist')
    stocks = relationship('Stock', secondary=watchlist_stock_association, back_populates='watchlists')

class Stock(database.Model):
    __tablename__ = 'stock'

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(unique=True, nullable=False) # Stock symbol
    current_price: Mapped[float] = mapped_column(nullable=False) # Current price of the stock
    percent_change: Mapped[float] = mapped_column(nullable=False) # Percent change in price
    last_updated_at: Mapped[datetime] = mapped_column(nullable=False) # Date of last update of the stock price

    watchlists = relationship('Watchlist', secondary=watchlist_stock_association, back_populates='stocks')