import api from "./axios";

/**
 * Authentication Service
 *
 * All HTTP requests related to authentication live here.
 * No UI logic, no storage logic, no context logic.
 *
 * ──────────────────────────────────────────────────────────────────────
 * Backend endpoints consumed (see backend/config/urls.py):
 *
 *   POST /api/auth/register/       → RegisterView  (custom wrapper)
 *   POST /api/auth/login/          → LoginView      (custom wrapper)
 *   POST /api/auth/token/refresh/  → TokenRefreshView (raw SimpleJWT)
 *
 * Custom wrapper responses follow:
 *   { success: true, message: "...", data: { ... } }
 *
 * Token refresh returns raw SimpleJWT:
 *   { access: "..." }
 * ──────────────────────────────────────────────────────────────────────
 */

/**
 * Register a new user.
 *
 * @param {Object} credentials
 * @param {string} credentials.username
 * @param {string} credentials.email
 * @param {string} credentials.password
 * @param {string} credentials.confirm_password
 *
 * @returns {Promise<Object>} Backend envelope:
 *   { success, message, data: { id, username, email } }
 */
export const registerUser = async (credentials) => {
  const response = await api.post("/api/auth/register/", credentials);
  return response.data;
};

/**
 * Authenticate an existing user.
 *
 * @param {Object} credentials
 * @param {string} credentials.username
 * @param {string} credentials.password
 *
 * @returns {Promise<Object>} Backend envelope:
 *   { success, message, data: { access, refresh, user } }
 *
 * `user` shape (from UserSerializer):
 *   { id, username, email, account_status, created_at }
 */
export const loginUser = async (credentials) => {
  const response = await api.post("/api/auth/login/", credentials);
  return response.data;
};

/**
 * Request a new access token using a valid refresh token.
 *
 * This endpoint uses the standard SimpleJWT `TokenRefreshView` and does
 * NOT wrap its response in the project's custom envelope.
 *
 * @param {string} refreshToken - A valid JWT refresh token.
 *
 * @returns {Promise<Object>} Raw SimpleJWT response:
 *   { access: "new_access_token" }
 */
export const refreshAccessToken = async (refreshToken) => {
  const response = await api.post("/api/auth/token/refresh/", {
    refresh: refreshToken,
  });
  return response.data;
};

/**
 * Logout placeholder.
 *
 * The backend currently uses Simple JWT with token blacklisting enabled
 * (`BLACKLIST_AFTER_ROTATION: True` in settings).  A dedicated logout
 * endpoint that blacklists the refresh token can be added later.
 *
 * For now, logout is handled client-side by clearing stored tokens and
 * user data (see AuthContext.logout).
 *
 * @returns {Promise<void>}
 */
export const logoutUser = async () => {
  // Future: POST /api/auth/logout/ with { refresh } to blacklist the
  // token server-side.  Until that endpoint exists, this is a no-op
  // on the network layer.
  return Promise.resolve();
};
