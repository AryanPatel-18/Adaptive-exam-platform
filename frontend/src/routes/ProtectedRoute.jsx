import { useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";
import useAuth from "../hooks/useAuth";

/**
 * ProtectedRoute
 *
 * Route guard that ensures only authenticated users can access
 * the wrapped child routes.
 *
 * Decision flow:
 *   1. If the auth layer is still loading (initial mount or refresh
 *      in progress), render a loading indicator.
 *   2. If the user is authenticated, render the child route via <Outlet />.
 *   3. If not authenticated, attempt a silent refresh:
 *      a. If no refresh token exists → redirect to /login.
 *      b. If refresh succeeds       → render the child route.
 *      c. If refresh fails          → clear stale data, redirect to /login.
 *
 * This component does NOT:
 *   - Make raw HTTP requests (delegated to AuthContext → auth service).
 *   - Manipulate localStorage directly (delegated to AuthContext → storage).
 *   - Contain any axios code.
 */
const ProtectedRoute = () => {
  const { isAuthenticated, loading, refreshAuthentication } = useAuth();

  // Local state to track the one-time silent refresh attempt.
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshAttempted, setRefreshAttempted] = useState(false);

  useEffect(() => {
    // Only attempt a refresh if:
    //   - The global auth loading has completed (session restore done).
    //   - The user is NOT authenticated after session restore.
    //   - We haven't already attempted a refresh in this mount cycle.
    if (!loading && !isAuthenticated && !refreshAttempted) {
      setIsRefreshing(true);

      refreshAuthentication().finally(() => {
        setRefreshAttempted(true);
        setIsRefreshing(false);
      });
    }
  }, [loading, isAuthenticated, refreshAttempted, refreshAuthentication]);

  // ─── Loading States ──────────────────────────────────────────────────────

  if (loading || isRefreshing) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
          fontSize: "1.125rem",
          color: "#888",
        }}
      >
        Verifying authentication…
      </div>
    );
  }

  // ─── Decision ────────────────────────────────────────────────────────────

  if (isAuthenticated) {
    return <Outlet />;
  }

  // Not authenticated after all checks — send to login.
  return <Navigate to="/login" replace />;
};

export default ProtectedRoute;
