import { useState } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import Dashboard from './components/home/Dashboard';
import Workspace from './components/workspace/Workspace';
import Quiz from './components/quiz/Quiz';
import ViewAllWorkspaces from './components/workspace/ViewAllWorkspaces';
import ViewAllQuizzes from './components/quiz/ViewAllQuizzes';
import Auth from './components/auth/Auth';
import useAuth from './hooks/useAuth';

// ─── Route Guards ──────────────────────────────────────────────────────────

/**
 * ProtectedRoute
 * Ensures the user is authenticated before rendering the children.
 * If not authenticated, redirects to the login page.
 */
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ display: 'flex', height: '100vh', width: '100vw', alignItems: 'center', justifyContent: 'center', backgroundColor: '#09090b', color: 'white' }}>
        <div style={{ fontSize: '1.25rem' }}>Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

/**
 * AuthRoute
 * Ensures an authenticated user doesn't access the login/register page.
 * If authenticated, redirects to the dashboard.
 */
const AuthRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ display: 'flex', height: '100vh', width: '100vw', alignItems: 'center', justifyContent: 'center', backgroundColor: '#09090b', color: 'white' }}>
        <div style={{ fontSize: '1.25rem' }}>Loading...</div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

// ─── Main App Component ────────────────────────────────────────────────────

function App() {
  const navigate = useNavigate();

  // ─── Completed quiz results (persisted across navigation) ───────────────
  const [completedQuizzes, setCompletedQuizzes] = useState([]);

  /**
   * Called by Quiz when the user clicks "Back to Workspace" after finishing.
   * Receives a result object: { name, workspace, score, fraction, timeTaken, date, questions }
   * Prepends it so the newest quiz appears first, then navigates to the listing.
   */
  const handleQuizFinish = (result) => {
    setCompletedQuizzes((prev) => [{ id: Date.now(), ...result }, ...prev]);
    navigate('/quizzes');
  };

  // ─── Shared sidebar / stats props (replace with API data) ───────────────
  const sharedProps = {
    streak: { count: 0, daysCompleted: [false, false, false, false, false, false, false] },
    revisions: [],
    weekSummary: { avgAccuracy: '--', studyTime: '--' },
    weeklyGraphImage: '',
  };

  // ─── Dashboard-specific props ────────────────────────────────────────────
  const dashboardProps = {
    username: 'Student', // Later: useAuth().user?.username
    stats: {},
    workspaces: [],
    quizzes: completedQuizzes,
    ...sharedProps,
    onViewAllWorkspaces: () => navigate('/workspaces'),
    onViewAllQuizzes: () => navigate('/quizzes'),
  };
  // ─────────────────────────────────────────────────────────────────────────

  return (
    <Routes>
      {/* Root path redirects to the dashboard automatically */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      {/* Authentication Route */}
      <Route
        path="/login"
        element={
          <AuthRoute>
            <Auth />
          </AuthRoute>
        }
      />

      {/* ─── Protected Routes ─── */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard {...dashboardProps} />
          </ProtectedRoute>
        }
      />

      <Route
        path="/workspaces"
        element={
          <ProtectedRoute>
            <ViewAllWorkspaces
              {...sharedProps}
              onNavigateBack={() => navigate('/dashboard')}
            />
          </ProtectedRoute>
        }
      />

      <Route
        path="/workspace/:id"
        element={
          <ProtectedRoute>
            <Workspace />
          </ProtectedRoute>
        }
      />

      <Route
        path="/quizzes"
        element={
          <ProtectedRoute>
            <ViewAllQuizzes
              {...sharedProps}
              quizzes={completedQuizzes}
              onNavigateBack={() => navigate('/dashboard')}
            />
          </ProtectedRoute>
        }
      />

      <Route
        path="/quiz/:id"
        element={
          <ProtectedRoute>
            <Quiz
              quizName="Data Structures - Trees"
              workspaceName="DSA Workspace"
              onFinish={handleQuizFinish}
              onQuit={() => navigate('/dashboard')}
            />
          </ProtectedRoute>
        }
      />

      {/* Catch-all route redirects to dashboard */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default App;
