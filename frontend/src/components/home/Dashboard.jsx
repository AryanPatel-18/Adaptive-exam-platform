import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuth from '../../hooks/useAuth';
import api from '../../api/axios';
import Navbar from '../common/Navbar';
import DashboardSidebar from '../common/DashboardSidebar';
import {WorkspaceIcon,QuizeIcon,TrendingIcon,ClockIcon,TargetIcon,FlameIcon,CalenderIcon,DocumentIcon,ChevronRightIcon,InboxIcon} from '../common/svg'
import './Dashboard.css';

// ── SVG icon helpers (dashboard-specific) ─────────────────────────────────────
const Icon = {
  workspace: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 6a2 2 0 0 1 2-2h5l2 2h9a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6z" />
    </svg>
  ),
  quiz: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 11l3 3L22 4" /><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
    </svg>
  ),
  clock: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
    </svg>
  ),
  target: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="6" /><circle cx="12" cy="12" r="2" />
    </svg>
  ),
  trending: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" /><polyline points="16 7 22 7 22 13" />
    </svg>
  ),
  flame: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M8.5 14.5A2.5 2.5 0 0 0 11 17c2 0 3-1 3-3s-1.5-3.5-2-5c-.5 1-1.5 2-2 3-1 1.5-1.5 2-1.5 3z" />
      <path d="M12 2C12 2 7 8 7 13a5 5 0 0 0 10 0c0-5-5-11-5-11z" />
    </svg>
  ),
  calendar: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
    </svg>
  ),
  document: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
    </svg>
  ),
  chevronRight: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="9 18 15 12 9 6" />
    </svg>
  ),
  inbox: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="22 12 16 12 14 15 10 15 8 12 2 12" />
      <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
    </svg>
  ),
};

// ── Stat card configuration (no values – values come from props) ──────────────
const STAT_CONFIG = [
  { id: 'workspaces', label: 'Workspaces', sub: 'Active', icon: <WorkspaceIcon/>, color: '#7c3aed' },
  { id: 'quizzes', label: 'Quizzes Taken', sub: 'This Month', icon: <QuizeIcon/>, color: '#059669' },
  { id: 'accuracy', label: 'Avg. Accuracy', sub: 'This Month', icon: <TargetIcon/>, color: '#d97706' },
  { id: 'studyTime', label: 'Total Study Time', sub: 'This Month', icon: <ClockIcon/>, color: '#2563eb' },
  { id: 'questions', label: 'Questions Solved', sub: 'This Month', icon: <TrendingIcon/>, color: '#dc2626' },
];

const DAYS_OF_WEEK = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];

// ── Helper: score colour thresholds ──────────────────────────────────────────
function scoreColor(pct) {
  if (pct >= 80) return '#059669';
  if (pct >= 60) return '#d97706';
  return '#dc2626';
}

// ── Helper: format study time ──────────────────────────────────────────────────
function formatStudyTime(seconds) {
  if (!seconds) return '0m';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

// ── Progress bar ──────────────────────────────────────────────────────────────
function ProgressBar({ value = 0 }) {
  const color = value >= 75 ? '#059669' : value >= 50 ? '#2563eb' : '#d97706';
  return (
    <div className="db-progress-track">
      <div
        className="db-progress-fill"
        style={{ width: `${Math.min(Math.max(value, 0), 100)}%`, background: color }}
      />
    </div>
  );
}

// ── Empty state placeholder ───────────────────────────────────────────────────
function EmptyState({ icon, message }) {
  return (
    <li className="db-empty-state">
      <span className="db-empty-icon">{icon}</span>
      <p className="db-empty-msg">{message}</p>
    </li>
  );
}

// ═════════════════════════════════════════════════════════════════════════════
// Dashboard component
//
// Props:
//   username        {string}   – display name shown in greeting
//   stats           {object}   – { workspaces, quizzes, accuracy, studyTime, questions }
//   workspaces      {Array}    – list of workspace objects:
//                                  { id, name, lastOpened, progress (0-100), iconBg }
//   quizzes         {Array}    – list of quiz objects:
//                                  { id, name, meta, score (0-100), fraction }
//   streak          {object}   – { count, daysCompleted: boolean[7] }
//   revisions       {Array}    – { id, subject, timing, timingColor }
//   weeklyPoints    {number[]} – data points for the sparkline (Mon-Sun)
//   weekSummary     {object}   – { avgAccuracy: string, studyTime: string }
// ═════════════════════════════════════════════════════════════════════════════
export default function Dashboard({
  username = 'Student',
  weekSummary = { avgAccuracy: '--', studyTime: '--' },
  weeklyGraphImage = '',
  onViewAllWorkspaces = () => {},
  onViewAllQuizzes = () => {},
}) {
  const [activePage, setActivePage] = useState('dashboard');
  const [searchValue, setSearchValue] = useState('');
  const [dashboardData, setDashboardData] = useState(null);
  const [graphUrl, setGraphUrl] = useState('');
  
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchDashboardStats = async () => {
      try {
        const response = await api.get('/api/dashboard/stats/');
        setDashboardData(response.data);
      } catch (error) {
        console.error('Failed to fetch dashboard stats:', error);
      }
    };
    
    const fetchGraph = async () => {
      try {
        const response = await api.get('/api/dashboard/weekly-graph/', {
          responseType: 'blob'
        });
        const url = URL.createObjectURL(response.data);
        setGraphUrl(url);
      } catch (err) {
        console.error("Failed to fetch graph", err);
      }
    };

    fetchDashboardStats();
    fetchGraph();
    
    return () => {
      if (graphUrl) URL.revokeObjectURL(graphUrl);
    };
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  // Greeting based on time of day
  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
  const greetEmoji = hour < 12 ? '🌤️' : hour < 17 ? '☀️' : '🌙';
  const displayUsername = user?.username || username;

  // Only ever show the 3 most recent items
  const recentWorkspaces = dashboardData?.recent_workspaces?.slice(0, 3).map(ws => ({
    id: ws.id,
    name: ws.title,
    lastOpened: new Date(ws.created_at).toLocaleDateString(),
    progress: ws.progress || 0,
    iconBg: '#7c3aed'
  })) || [];

  const recentQuizzes = dashboardData?.recent_quizzes?.slice(0, 3).map(qz => ({
    id: qz.id,
    name: qz.title,
    meta: `${qz.total_questions} Questions`,
    score: qz.score || 0,
    fraction: `${qz.attempted_questions ?? '--'}/${qz.total_questions}`
  })) || [];
  
  const stats = dashboardData ? {
    workspaces: dashboardData.active_workspaces,
    quizzes: dashboardData.total_quizzes_taken,
    accuracy: `${dashboardData.average_accuracy}%`,
    studyTime: formatStudyTime(dashboardData.total_study_time),
    questions: dashboardData.questions_solved
  } : {};

  const streak = dashboardData?.study_streak ? {
    count: dashboardData.study_streak.count,
    daysCompleted: dashboardData.study_streak.days_completed
  } : { count: 0, daysCompleted: [false, false, false, false, false, false, false] };

  const revisions = dashboardData?.upcoming_revision ? [dashboardData.upcoming_revision] : [];

  return (
    <div className="db-root">

      {/* ── Universal Navbar ── */}
      <Navbar
        activePage={activePage}
        onNavigate={setActivePage}
        notificationCount={0}
        searchValue={searchValue}
        onSearchChange={setSearchValue}
        onLogout={handleLogout}
      />

      {/* ── Page body ── */}
      <main className="db-main">

        {/* ══ Centre column ══ */}
        <div className="db-col-main">

          {/* 1 – Hero welcome banner */}
          <section className="db-hero-card db-card" aria-label="Welcome banner">
            <div className="db-hero-text">
              <h1 className="db-greeting">
                {greeting}, {displayUsername}! <span aria-hidden="true">{greetEmoji}</span>
              </h1>
              <p className="db-greeting-sub">
                Keep going! Every question you solve is a step closer to your goals.
              </p>
            </div>
            <div className="db-hero-illus" aria-hidden="true">
              <div className="db-hero-glow" />
              <span className="db-hero-emoji">✏️</span>
              <div className="db-hero-dot db-hero-dot-1" />
              <div className="db-hero-dot db-hero-dot-2" />
              <div className="db-hero-dot db-hero-dot-3" />
            </div>
          </section>

          {/* 2 – Stats strip */}
          <section className="db-stats-row" aria-label="Key statistics">
            {STAT_CONFIG.map(s => (
              <div key={s.id} className="db-stat-card db-card" id={`stat-${s.id}`}>
                <div className="db-stat-icon" style={{ color: s.color, background: `${s.color}1a` }}>
                  {s.icon}
                </div>
                <div>
                  <p className="db-stat-label">{s.label}</p>
                  <p className="db-stat-value">{stats[s.id] ?? '—'}</p>
                  <p className="db-stat-sub">{s.sub}</p>
                </div>
              </div>
            ))}
          </section>

          {/* 3 – Workspaces + Quizzes */}
          <div className="db-bottom-row">

            {/* Most Recent Workspaces */}
            <section className="db-list-card db-card" id="db-workspaces-card" aria-label="Most recent workspaces">
              <div className="db-list-header">
                <span className="db-list-header-icon"><WorkspaceIcon/></span>
                <h2 className="db-list-title">Most Recent Workspaces</h2>
                <button className="db-view-all-btn" id="db-workspaces-view-all" onClick={onViewAllWorkspaces}>View All</button>
              </div>

              <ul className="db-list" role="list">
                {recentWorkspaces.length > 0 ? (
                  recentWorkspaces.map((ws, idx) => (
                    <li key={ws.id ?? idx} className="db-list-item" id={`workspace-item-${ws.id ?? idx}`}>
                      {/* Workspace icon – use a coloured background square */}
                      <div
                        className="db-item-icon"
                        style={{ background: ws.iconBg ?? '#7c3aed' }}
                        aria-hidden="true"
                      >
                        <WorkspaceIcon/>
                      </div>

                      <div className="db-item-info">
                        <p className="db-item-name">{ws.name}</p>
                        <p className="db-item-meta">{ws.lastOpened}</p>
                      </div>

                      <div className="db-item-progress">
                        <p className="db-progress-label">
                          Progress&nbsp;<strong>{ws.progress ?? 0}%</strong>
                        </p>
                        <ProgressBar value={ws.progress ?? 0} />
                      </div>
                    </li>
                  ))
                ) : (
                  <EmptyState icon={<InboxIcon/>} message="No workspaces yet. Create one to get started!" />
                )}
              </ul>
            </section>

            {/* Recent Quizzes */}
            <section className="db-list-card db-card" id="db-quizzes-card" aria-label="Recent quizzes">
              <div className="db-list-header">
                <span className="db-list-header-icon"><QuizeIcon/></span>
                <h2 className="db-list-title">Recent Quizzes</h2>
                <button className="db-view-all-btn" id="db-quizzes-view-all" onClick={onViewAllQuizzes}>View All</button>
              </div>

              <ul className="db-list" role="list">
                {recentQuizzes.length > 0 ? (
                  recentQuizzes.map((qz, idx) => (
                    <li key={qz.id ?? idx} className="db-list-item" id={`quiz-item-${qz.id ?? idx}`}>
                      <div className="db-item-icon db-quiz-icon-bg" aria-hidden="true">
                        <DocumentIcon/>
                      </div>

                      <div className="db-item-info">
                        <p className="db-item-name">{qz.name}</p>
                        <p className="db-item-meta">{qz.meta}</p>
                      </div>

                      <div className="db-quiz-result">
                        <span
                          className="db-score-pct"
                          style={{ color: scoreColor(qz.score ?? 0) }}
                        >
                          {qz.score ?? 0}%
                        </span>
                        <span className="db-score-frac">{qz.fraction ?? '—'}</span>
                      </div>
                    </li>
                  ))
                ) : (
                  <EmptyState icon={<InboxIcon/>}message="No quizzes taken yet. Start a quiz to see your results here!" />
                )}
              </ul>
            </section>
          </div>
        </div>

        {/* ══ Sidebar ══ */}
        <DashboardSidebar
          streak={streak}
          revisions={revisions}
          weekSummary={weekSummary}
          weeklyGraphImage={graphUrl || weeklyGraphImage}
        />
      </main>
    </div>
  );
}
