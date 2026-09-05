import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, signInWithPopup } from "firebase/auth";

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

export const firebaseEnabled = Boolean(firebaseConfig.apiKey && firebaseConfig.projectId);

let authInstance = null;

function getFirebaseAuth() {
  if (!firebaseEnabled) return null;
  if (!authInstance) {
    const app = initializeApp(firebaseConfig);
    authInstance = getAuth(app);
  }
  return authInstance;
}

// Returns a fresh Firebase ID token — that's the only thing the backend
// needs; it verifies the token itself (see
// app/services/auth_service.py:login_with_firebase) rather than trusting
// anything else the client sends.
//
// Google is deliberately the only Firebase sign-in method here. Email/password
// stays on our own backend so that accounts created before Firebase existed
// keep working; see the note in context/AuthContext.jsx.
export async function signInWithGooglePopup() {
  const auth = getFirebaseAuth();
  const result = await signInWithPopup(auth, new GoogleAuthProvider());
  return result.user.getIdToken();
}
