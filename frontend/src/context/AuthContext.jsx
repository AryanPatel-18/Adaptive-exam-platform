import { createContext, useState, useCallback, useMemo, useEffect } from "react";
import {
  loginUser,
  registerUser,
  refreshAccessToken,
  logoutUser,
} from "../api/auth";
import {
  saveTokens,
  clearAll,
  getAccessToken,
  getRefreshToken,
  getUser,
  saveUser,
  setAccessToken,
  setRefreshToken,
} from "../utils/storage";

/**
 * AuthContext
 *
 * Provides a single source of truth for authentication state across
 * the application.  Components should consume this context via the
 * `useAuth` hook rather than importing it directly.
 *
 * Exposed values:
 *   - user              : Current user object (from UserSerializer) or null.
 *   - isAuthenticated    : Boolean derived from the presence of an access token.
 *   - loading            : True while initial session restoration or a
 *                          refresh attempt is in progress.
 *   - login(credentials) : Authenticate and persist tokens + user.
 *   - register(data)     : Create a new account (does NOT auto-login).
 *   - logout()           : Clear all auth state and storage.
 *   - refreshAuthentication() : Silently refresh the access token using
 *                               the stored refresh token.
 */

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  // ─── State ─────────────────────────────────────────────────────────────────
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true); // true until initial check completes

  // Session Restoration moved below declarations to avoid ReferenceError

  // ─── Login ─────────────────────────────────────────────────────────────────
  //
  // Calls POST /api/auth/login/ which returns the custom wrapper:
  //   { success, message, data: { access, refresh, user } }
  //
  const login = useCallback(async (credentials) => {
    const response = await loginUser(credentials);
    const { access, refresh, user: userData } = response.data;

    // Persist to storage
    saveTokens({ access, refresh });
    saveUser(userData);

    // Update context state
    setUser(userData);
    setIsAuthenticated(true);

    return response;
  }, []);

  // ─── Register ──────────────────────────────────────────────────────────────
  //
  // Calls POST /api/auth/register/ which returns:
  //   { success, message, data: { id, username, email } }
  //
  // Does NOT auto-login.  The caller (e.g. the Auth component) should
  // redirect to login or call login() separately after registration.
  //
  const register = useCallback(async (data) => {
    const response = await registerUser(data);
    return response;
  }, []);

  // ─── Refresh Authentication ────────────────────────────────────────────────
  //
  // Calls POST /api/auth/token/refresh/ (raw SimpleJWT) which returns:
  //   { access: "new_token" }
  //
  // Used by ProtectedRoute to silently obtain a new access token when the
  // current one has expired but a valid refresh token still exists.
  //
  const refreshAuthentication = useCallback(async () => {
    const refreshToken = getRefreshToken();

    if (!refreshToken) {
      // No refresh token → nothing we can do.
      clearAll();
      setUser(null);
      setIsAuthenticated(false);
      return false;
    }

    try {
      const data = await refreshAccessToken(refreshToken);

      // Persist the new access token.
      setAccessToken(data.access);

      // The backend has ROTATE_REFRESH_TOKENS=True, so the endpoint
      // returns a new refresh token alongside the access token.
      // The old refresh token is blacklisted after rotation — we must
      // save the new one or subsequent refreshes will fail.
      if (data.refresh) {
        setRefreshToken(data.refresh);
      }

      // Restore user from storage (still valid — only the tokens rotated).
      const cachedUser = getUser();
      if (cachedUser) {
        setUser(cachedUser);
      }

      setIsAuthenticated(true);
      return true;
    } catch {
      // Refresh failed (token expired / blacklisted) — full cleanup.
      clearAll();
      setUser(null);
      setIsAuthenticated(false);
      return false;
    }
  }, []);

  // ─── Logout ────────────────────────────────────────────────────────────────
  //
  // Clears client-side state and storage.  When a server-side logout
  // endpoint exists, logoutUser() will POST to it first.
  //
  const logout = useCallback(async () => {
    try {
      await logoutUser();
    } finally {
      clearAll();
      setUser(null);
      setIsAuthenticated(false);
    }
  }, []);

  // ─── Session Restoration (on mount) ────────────────────────────────────────
  //
  // When the app loads, check localStorage for an existing session.
  // If a valid access token and user are present, restore the state
  // immediately so the user isn't forced to re-login on every refresh.
  //
  useEffect(() => {
    const restoreSession = async () => {
      const token = getAccessToken();
      const cachedUser = getUser();

      if (token && cachedUser) {
        setUser(cachedUser);
        setIsAuthenticated(true);
        setLoading(false);
      } else {
        const refreshToken = getRefreshToken();
        if (refreshToken) {
          // Attempt to silently refresh access token
          await refreshAuthentication();
        }
        setLoading(false);
      }
    };

    restoreSession();
  }, [refreshAuthentication]);

  // ─── Context Value ─────────────────────────────────────────────────────────

  const value = useMemo(
    () => ({
      user,
      isAuthenticated,
      loading,
      login,
      register,
      logout,
      refreshAuthentication,
    }),
    [user, isAuthenticated, loading, login, register, logout, refreshAuthentication],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
