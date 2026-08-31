import os

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials, firestore

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CREDENTIALS_PATH = os.path.join(BACKEND_DIR, "firebase-service-account.json")

_app = None
_db = None


def _ensure_app():
    """Lazily initializes the Firebase Admin SDK, shared by both Firestore
    access and ID token verification. Credentials come from
    FIREBASE_CREDENTIALS_PATH, or the default backend/firebase-service-account.json
    (gitignored — never commit it)."""
    global _app
    if _app is not None:
        return _app

    credentials_path = os.environ.get("FIREBASE_CREDENTIALS_PATH", DEFAULT_CREDENTIALS_PATH)
    if not os.path.exists(credentials_path):
        raise RuntimeError(
            f"Firebase service account key not found at {credentials_path}. "
            "Download one from Firebase Console > Project Settings > Service accounts, "
            "and save it there (or point FIREBASE_CREDENTIALS_PATH at it)."
        )

    cred = credentials.Certificate(credentials_path)
    _app = firebase_admin.initialize_app(cred)
    return _app


def get_firestore_client():
    """Returns a shared Firestore client."""
    global _db
    if _db is None:
        _ensure_app()
        _db = firestore.client()
    return _db


def verify_firebase_id_token(id_token):
    """Verifies a Firebase Auth ID token (from either the email/password or
    Google sign-in flow — Firebase issues the same kind of token either way)
    and returns its decoded claims. Raises ValueError on an invalid/expired
    token, same as the underlying SDK call."""
    _ensure_app()
    return firebase_auth.verify_id_token(id_token)
