import { Navigate, Outlet } from "react-router-dom";
import useAuth from "../hooks/useAuth";

/**
 * PublicRoute
 *
 * Route guard for authentication pages (/login, /register).
 *
 * Behaviour:
 *   - If the user is already authenticated → redirect to /dashboard
 *     (prevents authenticated users from seeing login/register pages).
 *   - If the user is not authenticated → render the child route normally.
 *   - While the auth layer is still loading (session restore), render a
 *     minimal loading indicator to prevent a flash of the public page.
 */
const PublicRoute = () => {
  const { isAuthenticated, loading } = useAuth();

  // Wait for session restore before making a decision.
  if (loading) {
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
        Loading…
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
};

export default PublicRoute;
