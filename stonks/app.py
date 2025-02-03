from flask import Flask
from stonks.config import config
from stonks.mail import MailHandler
from flask_wtf.csrf import CSRFProtect
from stonks.models import Stock, database
from stonks.extensions import cache


def create_app():
    app = Flask(__name__, template_folder='../templates')
    csrf = CSRFProtect(app)
    register_config(app)
    start_database(app)
    register_mail(app)
    register_blueprints(app)
    register_cache(app)

    return app

def start_database(app: Flask):
    database.init_app(app)

    with app.app_context():
        database.create_all()

        # Dummy data
        # apple_stock = Stock(symbol='AAPL', current_price=120.0, change=1.0, percent_change=0.5,
        #                     high_price_day=121.0, low_price_day=119.0, open_price_day=119.5)
        # microsoft_stock = Stock(symbol='MSFT', current_price=220.0, change=2.0, percent_change=1.0,
        #                         high_price_day=221.0, low_price_day=219.0, open_price_day=219.5)
        # google_stock = Stock(symbol='GOOGL', current_price=1800.0, change=10.0, percent_change=0.5,
        #                      high_price_day=1810.0, low_price_day=1790.0, open_price_day=1795.0)
        # tesla_stock = Stock(symbol='TSLA', current_price=800.0, change=10.0, percent_change=1.0,
        #                     high_price_day=810.0, low_price_day=790.0, open_price_day=795.0)

        # database.session.add(apple_stock)
        # database.session.add(microsoft_stock)
        # database.session.add(google_stock)
        # database.session.add(tesla_stock)
        # database.session.commit()

def register_config(app: Flask):
    app.config.from_object(config)

def register_cache(app: Flask):
    cache.init_app(app)

def register_mail(app: Flask):
    mail_handler = MailHandler(app)
    app.extensions['mail_handler'] = mail_handler

def register_blueprints(app: Flask):
    from stonks.main import main
    from stonks.auth import auth
    from stonks.stock import stock

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(stock)
    

if __name__ == '__main__':
    app = create_app()
    cache.init_app(app)
    app.run(debug=True)