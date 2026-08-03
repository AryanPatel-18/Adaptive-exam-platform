import { useContext } from "react";
import { AuthContext } from "../context/AuthContext";

/**
 * useAuth
 *
 * Convenience hook that wraps AuthContext and provides a clean
 * developer experience.  Throws if used outside of <AuthProvider>.
 *
 * Usage:
 *   const { user, isAuthenticated, login, logout } = useAuth();
 */
const useAuth = () => {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used within an <AuthProvider>. " +
        "Wrap your component tree with <AuthProvider> in main.jsx.",
    );
  }

  return context;
};

export default useAuth;
