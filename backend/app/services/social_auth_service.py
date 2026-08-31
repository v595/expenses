import hashlib
import hmac

import requests

from app.config import Config
from app.services.auth_service import AuthError

GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
FACEBOOK_GRAPH_ME_URL = "https://graph.facebook.com/me"
REQUEST_TIMEOUT = 10


def verify_google_access_token(access_token):
    """Trades a Google OAuth access token (obtained client-side) for the
    profile it belongs to. Google itself validates the token when we call
    this endpoint with it, so there's no separate signature check needed."""
    if not Config.GOOGLE_CLIENT_ID:
        raise AuthError("Google sign-in isn't configured on this server yet.", 503)
    if not access_token or not isinstance(access_token, str):
        raise AuthError("Missing Google access token", 400)

    try:
        response = requests.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as e:
        raise AuthError("Could not reach Google to verify sign-in", 502) from e

    if response.status_code != 200:
        raise AuthError("Could not verify Google credential", 401)

    data = response.json()
    email = data.get("email")
    if not email or not data.get("email_verified"):
        raise AuthError("Your Google account has no verified email", 401)

    return {"email": email.strip().lower(), "name": data.get("name") or email.split("@")[0]}


def verify_facebook_access_token(access_token):
    """Same idea as verify_google_access_token, using Facebook's Graph API
    instead. appsecret_proof is added when the app secret is configured, so
    Facebook can additionally confirm the request came from this backend."""
    if not Config.FACEBOOK_APP_ID:
        raise AuthError("Facebook sign-in isn't configured on this server yet.", 503)
    if not access_token or not isinstance(access_token, str):
        raise AuthError("Missing Facebook access token", 400)

    params = {"fields": "id,name,email", "access_token": access_token}
    if Config.FACEBOOK_APP_SECRET:
        params["appsecret_proof"] = hmac.new(
            Config.FACEBOOK_APP_SECRET.encode("utf-8"), access_token.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    try:
        response = requests.get(FACEBOOK_GRAPH_ME_URL, params=params, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as e:
        raise AuthError("Could not reach Facebook to verify sign-in", 502) from e

    if response.status_code != 200:
        raise AuthError("Could not verify Facebook credential", 401)

    data = response.json()
    email = data.get("email")
    if not email:
        raise AuthError(
            "Your Facebook account has no email attached — add one on Facebook or use email sign-in.",
            401,
        )

    return {"email": email.strip().lower(), "name": data.get("name") or email.split("@")[0]}
