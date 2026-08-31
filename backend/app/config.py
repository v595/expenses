import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.environ.get("FLASK_DEBUG", "True") == "True"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # Social sign-in: unset in dev by default. The access token the frontend
    # gets back from Google/Facebook is verified here by asking the provider
    # who it belongs to (Google's userinfo endpoint / Facebook's Graph API)
    # rather than doing our own JWT/signature verification.
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    FACEBOOK_APP_ID = os.environ.get("FACEBOOK_APP_ID")
    FACEBOOK_APP_SECRET = os.environ.get("FACEBOOK_APP_SECRET")
