from flask_caching import Cache
from flask_login import LoginManager
from flask_apscheduler.scheduler import BackgroundScheduler
from stonks.user.models import User
import logging
from pytz import timezone
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

logging.basicConfig(level=logging.INFO)

cache = Cache()

login_manager = LoginManager()

timezone = os.getenv("TZ", "Etc/GMT-3")
scheduler = BackgroundScheduler(timezone=timezone)

limiter = Limiter(get_remote_address, default_limits=["100 per day", "20 per hour"])

login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access Stonks"
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

def log_next_run_time():
    """
    Log the next run time for each job in the scheduler
    """
    for job in scheduler.get_jobs():
        logging.info(f"Next run time for {job.name}: {job.next_run_time}")
