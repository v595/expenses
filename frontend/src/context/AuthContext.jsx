import { createContext, useContext, useState } from "react";

import {
  loginUser,
  loginWithFacebook as apiLoginWithFacebook,
  loginWithFirebase as apiLoginWithFirebase,
  loginWithGoogle as apiLoginWithGoogle,
  logoutUser,
  registerUser,
  updateProfile as apiUpdateProfile,
  updateSettings as apiUpdateSettings,
} from "../services/api";
import { firebaseEnabled, registerWithEmail, signInWithEmail } from "../services/firebase";

const AuthContext = createContext(null);

// Read any previously saved session so refreshing the page doesn't log you out.
function loadStoredAuth() {
  const token = localStorage.getItem("token");
  const userJson = localStorage.getItem("user");
  if (!token || !userJson) return { token: null, user: null };
  return { token, user: JSON.parse(userJson) };
}

export function AuthProvider({ children }) {
  const [{ token, user }, setAuth] = useState(loadStoredAuth);

  function persist(token, user) {
    localStorage.setItem("token", token);
    localStorage.setItem("user", JSON.stringify(user));
    setAuth({ token, user });
  }

  async function loginWithFirebaseToken(idToken) {
    const data = await apiLoginWithFirebase(idToken);
    persist(data.token, data.user);
  }

  // When Firebase Auth is configured (see services/firebase.js), email/password
  // sign-in goes through it too — Firebase checks the password, we just verify
  // the resulting token. Falls back to this app's own auth when it isn't set up.
  async function login(email, password) {
    if (firebaseEnabled) {
      const idToken = await signInWithEmail(email, password);
      return loginWithFirebaseToken(idToken);
    }
    const data = await loginUser({ email, password });
    persist(data.token, data.user);
  }

  async function register(name, email, password) {
    if (firebaseEnabled) {
      const idToken = await registerWithEmail(name, email, password);
      return loginWithFirebaseToken(idToken);
    }
    const data = await registerUser({ name, email, password });
    persist(data.token, data.user);
  }

  async function loginWithGoogle(accessToken) {
    const data = await apiLoginWithGoogle(accessToken);
    persist(data.token, data.user);
  }

  async function loginWithFacebook(accessToken) {
    const data = await apiLoginWithFacebook(accessToken);
    persist(data.token, data.user);
  }

  async function logout() {
    if (token) {
      await logoutUser(token).catch(() => {}); // best-effort; log out locally regardless
    }
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setAuth({ token: null, user: null });
  }

  async function updateProfile(data) {
    const result = await apiUpdateProfile(data, token);
    localStorage.setItem("user", JSON.stringify(result.user));
    setAuth((prev) => ({ ...prev, user: result.user }));
    return result;
  }

  async function updateSettings(data) {
    const result = await apiUpdateSettings(data, token);
    localStorage.setItem("user", JSON.stringify(result.user));
    setAuth((prev) => ({ ...prev, user: result.user }));
    return result;
  }

  const value = {
    token,
    user,
    isAuthenticated: Boolean(token),
    login,
    register,
    loginWithGoogle,
    loginWithFacebook,
    loginWithFirebaseToken,
    logout,
    updateProfile,
    updateSettings,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Custom hook so components just call useAuth() instead of importing
// useContext + AuthContext everywhere.
export function useAuth() {
  return useContext(AuthContext);
}
