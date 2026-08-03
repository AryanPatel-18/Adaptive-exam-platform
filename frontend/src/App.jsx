import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from './routes/ProtectedRoute';
import PublicRoute from './routes/PublicRoute';
import Auth from './components/auth/Auth';
import Dashboard from './components/home/Dashboard';

/**
 * Top-level app shell.
 *
 * Defines the application's route structure using ProtectedRoute and
 * PublicRoute as layout wrappers that enforce authentication rules.
 *
 * Route structure:
 *   /login, /register  → PublicRoute  → Auth component
 *   /dashboard          → ProtectedRoute → Dashboard component
 *   /                   → redirects to /dashboard
 */
function App() {
  return (
    <Routes>
      {/* ─── Public Routes (redirect to dashboard if already logged in) ─── */}
      <Route element={<PublicRoute />}>
        <Route path="/login" element={<Auth />} />
        <Route path="/register" element={<Auth />} />
      </Route>

      {/* ─── Protected Routes (redirect to login if not authenticated) ──── */}
      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<Dashboard />} />
      </Route>

      {/* ─── Fallback: redirect unknown paths to dashboard ──────────────── */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default App;
