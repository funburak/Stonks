from flask import Flask
from stonks.helper.config import config
from stonks.helper.mail import MailHandler
from flask_wtf.csrf import CSRFProtect
from stonks.user.models import Stock,database
from stonks.helper.extensions import cache, login_manager, scheduler
import yfinance as yf
from datetime import datetime
from stonks.stocks.stock import update_stock_prices_daily

def create_app():
    app = Flask(__name__, template_folder='../templates')
    csrf = CSRFProtect(app)
    register_config(app)
    start_database(app)
    register_mail(app)
    register_blueprints(app)
    register_extensions(app)

    return app

def start_database(app: Flask):
    """
    Start the database with the app context

    Args:
        app (Flask): The Flask app
    """
    database.init_app(app)

    with app.app_context():
        # database.drop_all()
        database.create_all()

def register_config(app: Flask):
    """
    Register the configuration for the app

    Args:
        app (Flask): The Flask app
    """
    app.config.from_object(config)

def register_extensions(app: Flask):
    """
    Register cache and login manager extensions

    Args:
        app (Flask): The Flask app
    """
    cache.init_app(app) # Initialize cache for the stock news at the homepage
    login_manager.init_app(app) # Initialize the login manager

    with app.app_context():
        scheduler.add_job(update_stock_prices_daily, 'interval', days=1, args=[app])
        scheduler.start()

def register_mail(app: Flask):
    """
    Register the mail handler extension

    Args:
        app (Flask): The Flask app
    """
    mail_handler = MailHandler(app)
    app.extensions['mail_handler'] = mail_handler

def register_blueprints(app: Flask):
    """
    Register the blueprints for the app

    Args:
        app (Flask): The Flask app
    """
    from stonks.dashboard import dashboard
    from stonks.user.auth import auth
    from stonks.stocks.stock import stock

    app.register_blueprint(dashboard)
    app.register_blueprint(auth)
    app.register_blueprint(stock)
