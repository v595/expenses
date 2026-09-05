import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { firebaseEnabled, signInWithGooglePopup } from "../services/firebase";

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;
const FACEBOOK_APP_ID = import.meta.env.VITE_FACEBOOK_APP_ID;
const GOOGLE_SDK_SRC = "https://accounts.google.com/gsi/client";
const FACEBOOK_SDK_SRC = "https://connect.facebook.net/en_US/sdk.js";

function GoogleIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 48 48" aria-hidden="true">
      <path
        fill="#FFC107"
        d="M43.6 20.5h-1.6V20H24v8h11.3c-1.6 4.9-6 8-11.3 8-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.1 8 3l5.7-5.7C34.6 6.1 29.6 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.7-.4-3.5z"
      />
      <path
        fill="#FF3D00"
        d="M6.3 14.7l6.6 4.8C14.6 15.9 18.9 13 24 13c3.1 0 5.8 1.1 8 3l5.7-5.7C34.6 6.1 29.6 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"
      />
      <path
        fill="#4CAF50"
        d="M24 44c5.5 0 10.4-1.9 14.3-5.1l-6.6-5.6C29.6 35.4 26.9 36 24 36c-5.3 0-9.7-3.1-11.3-7.5l-6.6 5.1C9.6 39.6 16.3 44 24 44z"
      />
      <path
        fill="#1976D2"
        d="M43.6 20.5h-1.6V20H24v8h11.3c-.8 2.3-2.3 4.3-4.2 5.7l6.6 5.6C41.3 36.7 44 30.9 44 24c0-1.3-.1-2.7-.4-3.5z"
      />
    </svg>
  );
}

function FacebookIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="#fff"
        d="M22 12.07C22 6.51 17.52 2 12 2S2 6.51 2 12.07c0 5.02 3.66 9.18 8.44 9.93v-7.02H7.9v-2.91h2.54V9.91c0-2.51 1.49-3.89 3.77-3.89 1.09 0 2.24.2 2.24.2v2.46h-1.26c-1.24 0-1.63.77-1.63 1.56v1.87h2.78l-.45 2.91h-2.33V22c4.78-.75 8.44-4.91 8.44-9.93z"
      />
    </svg>
  );
}

// Loads a third-party SDK script at most once per page, even if this
// component mounts more than once (Login/Register both render it).
function loadScript(src) {
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${src}"]`);
    if (existing) {
      if (existing.dataset.loaded === "true") return resolve();
      existing.addEventListener("load", () => resolve());
      existing.addEventListener("error", () => reject(new Error(`Failed to load ${src}`)));
      return;
    }
    const script = document.createElement("script");
    script.src = src;
    script.async = true;
    script.defer = true;
    script.onload = () => {
      script.dataset.loaded = "true";
      resolve();
    };
    script.onerror = () => reject(new Error(`Failed to load ${src}`));
    document.head.appendChild(script);
  });
}

function SocialAuthButtons() {
  const [error, setError] = useState(null);
  const [loadingProvider, setLoadingProvider] = useState(null);
  const googleTokenClientRef = useRef(null);
  const facebookInitializedRef = useRef(false);
  const { loginWithGoogle, loginWithFacebook, loginWithFirebaseToken } = useAuth();
  const navigate = useNavigate();

  async function handleGoogle() {
    setError(null);

    // Prefer Firebase Auth's Google provider when it's configured — it
    // handles the OAuth popup itself, no separate Google Cloud Client ID
    // needed. Falls back to the standalone flow below otherwise.
    if (firebaseEnabled) {
      setLoadingProvider("google");
      try {
        const idToken = await signInWithGooglePopup();
        await loginWithFirebaseToken(idToken);
        navigate("/transactions");
      } catch (err) {
        if (err.code === "auth/popup-closed-by-user") {
          setError("Google sign-in was cancelled.");
        } else {
          setError(err.message || "Google sign-in failed.");
        }
      } finally {
        setLoadingProvider(null);
      }
      return;
    }

    if (!GOOGLE_CLIENT_ID) {
      setError("Google sign-in isn't configured yet — use email above.");
      return;
    }

    setLoadingProvider("google");
    try {
      await loadScript(GOOGLE_SDK_SRC);
      if (!googleTokenClientRef.current) {
        googleTokenClientRef.current = window.google.accounts.oauth2.initTokenClient({
          client_id: GOOGLE_CLIENT_ID,
          scope: "openid email profile",
          callback: async (response) => {
            if (response.error || !response.access_token) {
              setError("Google sign-in was cancelled.");
              setLoadingProvider(null);
              return;
            }
            try {
              await loginWithGoogle(response.access_token);
              navigate("/transactions");
            } catch (err) {
              setError(err.message);
            } finally {
              setLoadingProvider(null);
            }
          },
        });
      }
      googleTokenClientRef.current.requestAccessToken();
    } catch {
      setError("Couldn't load Google sign-in — check your connection and try again.");
      setLoadingProvider(null);
    }
  }

  async function handleFacebook() {
    setError(null);
    if (!FACEBOOK_APP_ID) {
      setError("Facebook sign-in isn't configured yet — use email above.");
      return;
    }

    setLoadingProvider("facebook");
    try {
      await loadScript(FACEBOOK_SDK_SRC);
      if (!facebookInitializedRef.current) {
        window.FB.init({ appId: FACEBOOK_APP_ID, cookie: true, xfbml: false, version: "v19.0" });
        facebookInitializedRef.current = true;
      }
      window.FB.login(
        async (response) => {
          const accessToken = response.authResponse?.accessToken;
          if (!accessToken) {
            setError("Facebook sign-in was cancelled.");
            setLoadingProvider(null);
            return;
          }
          try {
            await loginWithFacebook(accessToken);
            navigate("/transactions");
          } catch (err) {
            setError(err.message);
          } finally {
            setLoadingProvider(null);
          }
        },
        { scope: "email" }
      );
    } catch {
      setError("Couldn't load Facebook sign-in — check your connection and try again.");
      setLoadingProvider(null);
    }
  }

  return (
    <div className="social-auth-section">
      <div className="social-divider">
        <span>or continue with</span>
      </div>
      <div className="social-auth-stack">
        <button
          type="button"
          className="btn-social btn-social-google"
          onClick={handleGoogle}
          disabled={loadingProvider === "google"}
        >
          <GoogleIcon />
          {loadingProvider === "google" ? "Signing in..." : "Sign in with Google"}
        </button>
        <button
          type="button"
          className="btn-social btn-social-facebook"
          onClick={handleFacebook}
          disabled={loadingProvider === "facebook"}
        >
          <FacebookIcon />
          {loadingProvider === "facebook" ? "Signing in..." : "Continue with Facebook"}
        </button>
        {error && <p className="social-auth-notice">{error}</p>}
      </div>
    </div>
  );
}

export default SocialAuthButtons;
