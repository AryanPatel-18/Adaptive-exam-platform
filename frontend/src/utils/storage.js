/**
 * Storage Utility
 *
 * Single responsibility: token and user persistence in localStorage.
 * This module never makes API calls — it only manages browser storage.
 *
 * Keys mirror the backend JWT field names returned by the authentication
 * service (see backend/authentication/views.py → LoginView).
 */

const KEYS = Object.freeze({
  ACCESS_TOKEN: "access_token",
  REFRESH_TOKEN: "refresh_token",
  USER: "user",
});

// ─── Access Token ──────────────────────────────────────────────────────────────

/**
 * @returns {string|null} The stored access token, or null if absent.
 */
export const getAccessToken = () => localStorage.getItem(KEYS.ACCESS_TOKEN);

/**
 * @param {string} token - JWT access token string.
 */
export const setAccessToken = (token) =>
  localStorage.setItem(KEYS.ACCESS_TOKEN, token);

export const removeAccessToken = () =>
  localStorage.removeItem(KEYS.ACCESS_TOKEN);

// ─── Refresh Token ─────────────────────────────────────────────────────────────

/**
 * @returns {string|null} The stored refresh token, or null if absent.
 */
export const getRefreshToken = () => localStorage.getItem(KEYS.REFRESH_TOKEN);

/**
 * @param {string} token - JWT refresh token string.
 */
export const setRefreshToken = (token) =>
  localStorage.setItem(KEYS.REFRESH_TOKEN, token);

export const removeRefreshToken = () =>
  localStorage.removeItem(KEYS.REFRESH_TOKEN);

// ─── Both Tokens (convenience) ─────────────────────────────────────────────────

/**
 * Persist both tokens at once.
 *
 * @param {Object} tokens
 * @param {string} tokens.access  - JWT access token.
 * @param {string} tokens.refresh - JWT refresh token.
 */
export const saveTokens = ({ access, refresh }) => {
  setAccessToken(access);
  setRefreshToken(refresh);
};

/**
 * Remove all authentication tokens from storage.
 */
export const clearTokens = () => {
  removeAccessToken();
  removeRefreshToken();
};

// ─── User ──────────────────────────────────────────────────────────────────────

/**
 * Read the cached user object.
 *
 * The shape matches the backend's UserSerializer output:
 *   { id, username, email, account_status, created_at }
 *
 * @returns {Object|null} Parsed user object, or null if absent / corrupt.
 */
export const getUser = () => {
  try {
    const raw = localStorage.getItem(KEYS.USER);
    return raw ? JSON.parse(raw) : null;
  } catch {
    // Guard against corrupted JSON.
    localStorage.removeItem(KEYS.USER);
    return null;
  }
};

/**
 * @param {Object} user - User object to cache.
 */
export const saveUser = (user) =>
  localStorage.setItem(KEYS.USER, JSON.stringify(user));

export const clearUser = () => localStorage.removeItem(KEYS.USER);

// ─── Full Cleanup ──────────────────────────────────────────────────────────────

/**
 * Remove all authentication-related data from localStorage.
 * Called on logout and when token refresh fails.
 */
export const clearAll = () => {
  clearTokens();
  clearUser();
};
