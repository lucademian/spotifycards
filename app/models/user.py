from app.extensions import db
from app.services.github import GitHub
import uuid, os, requests, datetime, base64
from flask import session

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer(), primary_key=True)
    tid = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(255), unique=True)
    display_name = db.Column(db.String(255), nullable=True)
    access_token = db.Column(db.String(255), nullable=True)
    refresh_token = db.Column(db.String(255), nullable=True)
    token_expires_at = db.Column(db.DateTime, nullable=True)

    def __init__(self, email, display_name, access_token, refresh_token, token_expires_at):
        # Generate a random UID for refreshable authentication storage
        self.tid = uuid.uuid4().hex
        self.email = username
        self.display_name = display_name
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expires_at = token_expires_at
    
    @property
    def auth_token(self):
        if self.token_expires_at is None or datetime.now() > self.token_expires_at:
            refresh_tokens()
        
        return self.access_token

    def refresh_tokens(self):
        r = requests.post(
            "https://accounts.spotify.com/api/token", 
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            },
            auth=(os.getenv('SPOTIFY_CLIENT_ID', default=''), os.getenv('SPOTIFY_CLIENT_SECRET', default='')))

        
        if r.status_code == 200:
            data = r.json()
            self.access_token = data["access_token"]
            if "refresh_token" in data:
                self.refresh_token = data["refresh_token"]
            token_expires_at = datetime.datetime.now() + datetime.timedelta(seconds=data["expires_in"])
        else:
            raise ValueError("Response from Spotify wasn't 200.")

    @staticmethod
    def get_anonymous_access_token():
        if "app_access_token" in session and "app_access_expiration" in session and session["app_access_expiration"] > datetime.datetime.now().timestamp():
            return session["app_access_token"]
        else:
            r = requests.post(
                "https://accounts.spotify.com/api/token", 
                data = {
                    "grant_type": "client_credentials",
                },
                auth=(os.getenv('SPOTIFY_CLIENT_ID', default=''), os.getenv('SPOTIFY_CLIENT_SECRET', default='')))
        
            if r.status_code == 200:
                data = r.json()
                access_token = data["access_token"]
                token_expires_at = datetime.datetime.now() + datetime.timedelta(seconds=data["expires_in"])
                session["app_access_token"] = access_token
                session["app_access_expiration"] = token_expires_at.timestamp()
                return access_token
            else:
                print(str(r.status_code), r.text)
                raise ValueError("Response from Spotify wasn't 200.")

    @staticmethod
    def create_from_authorization_code(auth_code, redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI', default='')):
        r = requests.post(
            "https://accounts.spotify.com/api/token", 
            data = {
                "grant_type": "authorization_code",
                "code": auth_code,
                "redirect_uri": redirect_uri
            },
            auth=(os.getenv('SPOTIFY_CLIENT_ID', default=''), os.getenv('SPOTIFY_CLIENT_SECRET', default='')))
        
        if r.status_code == 200:
            data = r.json()
            access_token = data["access_token"]
            if "refresh_token" in data:
                refresh_token = data["refresh_token"]
            token_expires_at = datetime.datetime.now() + datetime.timedelta(seconds=data["expires_in"])
        else:
            raise ValueError("Response from Spotify wasn't 200.")
        
        r = requests.get("https://api.spotify.com/v1/me", headers={"Authorization": access_token})

        if r.status_code == 200:            
            user_data = r.json()
        
            instance = User.query.filter_by(email=user_data['email']).first()

            if not instance:
                instance = User(user_data["email"], user_data["display_name"], access_token, refresh_token, token_expires_at)
                db.session.add(instance)
                db.session.commit()

            return instance
        else:
            raise ValueError("User Info response from Spotify wasn't 200.")
    
    def get_id(self):
        return unicode(self.tid)

    @property
    def is_authenticated(self):
        return self.access_token is not None and self.refresh_token is not None

    @property
    def is_active(self):
        return True
    
    @property
    def is_anonymous(self):
        return self.access_token is None and self.refresh_token is None

    def __repr__(self):
        return "<User: {}>".format(self.display_name)
