from flask import Flask, render_template
from stonks.helper.config import config
from stonks.helper.mail import MailHandler
from flask_wtf.csrf import CSRFProtect
from stonks.user.models import database
from stonks.helper.extensions import cache, login_manager, scheduler, limiter, log_next_run_time
from stonks.stocks.stock import update_stock_prices_daily, generate_daily_report
from apscheduler.triggers.cron import CronTrigger
from flask_migrate import Migrate

def create_app():
    app = Flask(__name__, template_folder='../templates')
    csrf = CSRFProtect(app)
    register_config(app)
    start_database(app)
    register_mail(app)
    register_blueprints(app)
    register_extensions(app)
    register_error_pages(app)

    log_next_run_time()
    return app

def start_database(app: Flask):
    """
    Start the database with the app context

    Args:
        app (Flask): The Flask app
    """
    database.init_app(app)

    with app.app_context():
        database.create_all()
    
    migrate = Migrate(app, database)

def register_config(app: Flask):
    """
    Register the configuration for the app

    Args:
        app (Flask): The Flask app
    """
    app.config.from_object(config)

def register_extensions(app: Flask):
    """
    Register cache, login manager and scheduler extensions

    Args:
        app (Flask): The Flask app
    """
    cache.init_app(app) # Initialize cache for the stock news at the homepage
    login_manager.init_app(app) # Initialize the login manager

    with app.app_context():
        scheduler.add_job(func=update_stock_prices_daily,
                          trigger=CronTrigger(hour=10, minute=0),
                          args=[app]) # Update stock prices daily at 10:00 AM
        scheduler.add_job(func=generate_daily_report,
                          trigger=CronTrigger(hour=10, minute=5),
                          args=[app]) # Generate daily report at 10:05 AM
        
        scheduler.start()
    
    limiter.init_app(app) # Limiter for the rate limiting

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


def register_error_pages(app: Flask):
    """
    Register the error pages for the app

    Args:
        app (Flask): The Flask app
    """
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return render_template('errors/429.html'), 429
