import os

DEV_SECRET_KEY = "dev-secret-key-change-in-production"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", DEV_SECRET_KEY)
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

    # Comma-separated list of frontend origins allowed to call this API, e.g.
    # "https://expenses-chiz.vercel.app,https://app.example.com". Unset in
    # dev, which allows every origin — matches this app's previous behavior
    # when run locally.
    CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]

    # Where password-reset emails point back to. Defaults to the Vite dev
    # server so the flow works locally with zero config; set this to the
    # deployed frontend's origin (no trailing slash) in production.
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173").rstrip("/")
