import { useState } from 'react';
import Dashboard from './components/home/Dashboard';
import Workspace from './components/workspace/Workspace';
import Quiz from './components/quiz/Quiz';
import ViewAllWorkspaces from './components/workspace/ViewAllWorkspaces';
import ViewAllQuizzes from './components/quiz/ViewAllQuizzes';
// import Auth from './components/auth/Auth'; // ← swap in when routing is wired up

/**
 * Top-level app shell.
 *
 * Simple state-based router – replace with React Router when the full
 * routing layer is wired up.
 *
 * Pages:
 *   'dashboard'          – main Dashboard
 *   'all-workspaces'     – View All Workspaces listing
 *   'all-quizzes'        – View All Quizzes listing
 *   'workspace'          – Individual Workspace detail
 *   'quiz'               – Quiz taking flow
 */
function App() {
  const [page, setPage] = useState('dashboard');

  // ─── Completed quiz results (persisted across navigation) ───────────────
  const [completedQuizzes, setCompletedQuizzes] = useState([]);

  /**
   * Called by Quiz when the user clicks "Back to Workspace" after finishing.
   * Receives a result object: { name, workspace, score, fraction, timeTaken, date, questions }
   * Prepends it so the newest quiz appears first, then navigates to the listing.
   */
  const handleQuizFinish = (result) => {
    setCompletedQuizzes((prev) => [{ id: Date.now(), ...result }, ...prev]);
    setPage('all-quizzes');
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
    username: 'Student',
    stats: {},
    workspaces: [],
    quizzes: completedQuizzes,
    ...sharedProps,
    onViewAllWorkspaces: () => setPage('all-workspaces'),
    onViewAllQuizzes: () => setPage('all-quizzes'),
  };
  // ─────────────────────────────────────────────────────────────────────────

  if (page === 'all-workspaces') {
    return (
      <ViewAllWorkspaces
        {...sharedProps}
        onNavigateBack={() => setPage('dashboard')}
      />
    );
  }

  if (page === 'all-quizzes') {
    return (
      <ViewAllQuizzes
        {...sharedProps}
        quizzes={completedQuizzes}
        onNavigateBack={() => setPage('dashboard')}
      />
    );
  }

  // Default: Dashboard
  // return <Dashboard {...dashboardProps} />;

  // Uncomment below to develop individual pages:
  // return <Workspace />;
  return (
    <Quiz
      quizName="Data Structures - Trees"
      workspaceName="DSA Workspace"
      onFinish={handleQuizFinish}
      onQuit={() => setPage('dashboard')}
    />
  );
  // return <Auth />;
}

export default App;
