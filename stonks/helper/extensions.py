from flask_caching import Cache
from flask_login import LoginManager
from stonks.user.models import User

cache = Cache()

login_manager = LoginManager()

login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access Stonks"
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)