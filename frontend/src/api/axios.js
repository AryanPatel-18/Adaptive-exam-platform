import axios from "axios";
import { getAccessToken } from "../utils/storage";

/**
 * Pre-configured Axios instance.
 *
 * Responsibilities (current):
 *  1. Read `VITE_API_URL` from the Vite environment.
 *  2. Set sensible defaults (timeout, JSON content-type).
 *  3. Attach the current access token to every outgoing request
 *     via a request interceptor.
 *
 * Responsibilities (future — NOT implemented yet):
 *  - Automatic 401 response interceptor to silently refresh tokens.
 *    For now, refresh is handled explicitly via AuthContext /
 *    ProtectedRoute so the flow remains transparent and debuggable.
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

export default api;
