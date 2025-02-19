import os
import secrets
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or secrets.token_hex(16)
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI') or 'sqlite:///stonks.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 465
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_DEFAULT_SENDER = "stonks@example.com"

    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 600 # 10 minutes

    SCHEDULAR_API_ENABLED = True

    PERMANENT_SESSION_LIFETIME = timedelta(minutes=10)
    SESSION_COOKIE_SECURE = True # Set to True for production
    SESSION_COOKIE_HTTPONLY = True # Prevent JavaScript access to cookies
    SESSION_COOKIE_SAMESITE = 'Lax' # Prevent CSRF attacks

config = Config()
