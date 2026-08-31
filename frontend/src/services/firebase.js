import { initializeApp } from "firebase/app";
import {
  createUserWithEmailAndPassword,
  getAuth,
  GoogleAuthProvider,
  signInWithEmailAndPassword,
  signInWithPopup,
  updateProfile,
} from "firebase/auth";

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

// Every helper below returns a fresh Firebase ID token — that's the only
// thing the backend needs; it verifies the token itself (see
// app/services/auth_service.py:login_with_firebase) rather than trusting
// anything else the client sends.

export async function signInWithGooglePopup() {
  const auth = getFirebaseAuth();
  const result = await signInWithPopup(auth, new GoogleAuthProvider());
  return result.user.getIdToken();
}

export async function signInWithEmail(email, password) {
  const auth = getFirebaseAuth();
  const result = await signInWithEmailAndPassword(auth, email, password);
  return result.user.getIdToken();
}

export async function registerWithEmail(name, email, password) {
  const auth = getFirebaseAuth();
  const result = await createUserWithEmailAndPassword(auth, email, password);
  if (name) {
    await updateProfile(result.user, { displayName: name });
  }
  return result.user.getIdToken();
}
