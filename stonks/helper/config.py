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

    SWAGGER = {
        "swagger": "2.0",
        "info": {
            "title": "Stonks API",
            "description": "API Documentation",
            "version": "1.0.0"
        },
        "headers":[],
        "specs": [
            {
                "endpoint": 'apispec_1',
                "route": '/apispec_1.json',
                "rule_filter": lambda rule: True,  # all in
                "model_filter": lambda tag: True,  # all in
            }
        ],
        'ui_params': {
            'supportedSubmitMethods': [],
        },
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/"
    }

config = Config()
