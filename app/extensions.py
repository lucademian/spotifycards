"""Extensions module - Set up for additional libraries can go in here."""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .models import user

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.spotifylogin"

@login_manager.user_loader
def load_user(user_id):
    return user.User.query.filter(tid == user_id).first()
