import axios from "axios";
import { getAccessToken, getRefreshToken, setAccessToken, clearAll } from "../utils/storage";

/**
 * Pre-configured Axios instance.
 *
 * Responsibilities (current):
 *  1. Read `VITE_API_URL` from the Vite environment.
 *  2. Set sensible defaults (timeout, JSON content-type).
 *  3. Attach the current access token to every outgoing request
 *     via a request interceptor.
 *  4. Automatic 401 response interceptor to silently refresh tokens.
 *     Redirects to login if refresh token is expired or invalid.
 */

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  timeout: 15_000,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

// ─── Request Interceptor: Attach Bearer Token ──────────────────────────────────

api.interceptors.request.use(
  (config) => {
    const token = getAccessToken();

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error),
);

// ─── Response Interceptor: Handle 401 & Token Refresh ──────────────────────────

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If error is 401 and we haven't retried yet, and it's not an auth route
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      originalRequest.url !== '/api/auth/login/' &&
      originalRequest.url !== '/api/auth/token/refresh/'
    ) {
      originalRequest._retry = true;
      const refreshToken = getRefreshToken();

      if (refreshToken) {
        try {
          // Attempt refresh using a raw axios instance to prevent interceptor loops
          const response = await axios.post(`${api.defaults.baseURL}/api/auth/token/refresh/`, {
            refresh: refreshToken
          });
          
          const newAccess = response.data.access;
          setAccessToken(newAccess);
          
          // Retry original request
          originalRequest.headers.Authorization = `Bearer ${newAccess}`;
          return api(originalRequest);
        } catch (refreshError) {
          // Refresh failed (expired or invalid refresh token)
          clearAll();
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      } else {
        // No refresh token available
        clearAll();
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export default api;
