import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api/axios';
import Navbar from '../common/Navbar';
import DashboardSidebar from '../common/DashboardSidebar';
import { WorkspaceIcon, InboxIcon } from '../common/svg';
import './ViewAllWorkspaces.css';
import '../home/Dashboard.css';

// ── Colour palette for workspace icon backgrounds ─────────────────────────────
const ICON_COLORS = [
  '#7c3aed', '#2563eb', '#059669', '#d97706', '#dc2626',
  '#0891b2', '#7c3aed', '#db2777', '#65a30d', '#ea580c',
];

function ProgressBar({ value = 0 }) {
  const color = value >= 75 ? '#059669' : value >= 50 ? '#2563eb' : '#d97706';
  return (
    <div className="va-progress-track">
      <div
        className="va-progress-fill"
        style={{ width: `${Math.min(Math.max(value, 0), 100)}%`, background: color }}
      />
    </div>
  );
}

function formatLastOpened(isoDateString) {
  if (!isoDateString) return 'Unknown';
  const date = new Date(isoDateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now - date) / 1000);
  
  if (diffInSeconds < 60) return 'Just now';
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
  if (diffInSeconds < 172800) return 'Yesterday';
  
  const diffInDays = Math.floor(diffInSeconds / 86400);
  if (diffInDays < 30) return `${diffInDays} days ago`;
  
  const diffInMonths = Math.floor(diffInDays / 30);
  if (diffInMonths === 1) return 'Last month';
  if (diffInMonths < 12) return `${diffInMonths} months ago`;
  
  return 'Over a year ago';
}

const FILTER_OPTIONS = ['All', 'In Progress', 'Completed', 'Just Started'];

function getFilteredWorkspaces(workspaces, filter, search) {
  let list = workspaces;
  if (search.trim()) {
    list = list.filter(ws =>
      ws.name.toLowerCase().includes(search.toLowerCase())
    );
  }
  switch (filter) {
    case 'Completed': return list.filter(ws => ws.progress === 100);
    case 'In Progress': return list.filter(ws => ws.progress > 0 && ws.progress < 100);
    case 'Just Started': return list.filter(ws => ws.progress === 0);
    default: return list;
  }
}

export default function ViewAllWorkspaces({
  onNavigateBack,
}) {
  const [workspaces, setWorkspaces] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activePage, setActivePage] = useState('workspaces');
  const [searchValue, setSearchValue] = useState('');
  const [activeFilter, setActiveFilter] = useState('All');
  const [sortBy, setSortBy] = useState('recent');
  
  const [dashboardData, setDashboardData] = useState(null);
  const [graphUrl, setGraphUrl] = useState('');
  
  const navigate = useNavigate();

  useEffect(() => {
    const fetchWorkspaces = async () => {
      try {
        const response = await api.get('/api/workspace/list/');
        // Map backend structure to frontend structure
        const mappedData = response.data.data.map(ws => ({
          id: ws.id,
          name: ws.title,
          lastOpened: formatLastOpened(ws.updated_at),
          progress: ws.progress || 0,
          quizCount: ws.quiz_count || 0,
          fileCount: ws.file_count || 0,
          updated_at: new Date(ws.updated_at).getTime() // For sorting
        }));
        setWorkspaces(mappedData);
      } catch (err) {
        console.error("Failed to fetch workspaces", err);
      } finally {
        setIsLoading(false);
      }
    };

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

    fetchWorkspaces();
    fetchDashboardStats();
    fetchGraph();
    
    return () => {
      if (graphUrl) URL.revokeObjectURL(graphUrl);
    };
  }, []);

  const streak = dashboardData?.study_streak ? {
    count: dashboardData.study_streak.count,
    daysCompleted: dashboardData.study_streak.days_completed
  } : { count: 0, daysCompleted: [false, false, false, false, false, false, false] };

  const revisions = dashboardData?.upcoming_revision ? [dashboardData.upcoming_revision] : [];
  
  const weekSummary = { avgAccuracy: '--', studyTime: '--' }; 
  const weeklyGraphImage = graphUrl || '';

  const filtered = getFilteredWorkspaces(workspaces, activeFilter, searchValue);

  const sorted = [...filtered].sort((a, b) => {
    if (sortBy === 'name') return a.name.localeCompare(b.name);
    if (sortBy === 'progress') return b.progress - a.progress;
    return b.updated_at - a.updated_at; // 'recent' – sort by latest updated_at
  });

  return (
    <div className="va-root db-root" id="view-all-workspaces-root">

      {/* ── Navbar ── */}
      <Navbar
        activePage={activePage}
        onNavigate={(id) => { setActivePage(id); if (id === 'home' && onNavigateBack) onNavigateBack(); }}
        notificationCount={0}
        searchValue={searchValue}
        onSearchChange={setSearchValue}
      />

      {/* ── Page body ── */}
      <main className="db-main va-main">

        {/* ══ Left / Centre column ══ */}
        <div className="db-col-main">

          {/* Page Header */}
          <div className="va-page-header">
            <div className="va-page-header-left">
              <div className="va-page-icon">
                <WorkspaceIcon />
              </div>
              <div>
                <h1 className="va-page-title">All Workspaces</h1>
                <p className="va-page-subtitle">{workspaces.length} workspace{workspaces.length !== 1 ? 's' : ''} total</p>
              </div>
            </div>

            {/* Sort control */}
            <div className="va-sort-wrap">
              <label htmlFor="va-sort-select" className="va-sort-label">Sort by</label>
              <select
                id="va-sort-select"
                className="va-sort-select"
                value={sortBy}
                onChange={e => setSortBy(e.target.value)}
              >
                <option value="recent">Most Recent</option>
                <option value="name">Name A–Z</option>
                <option value="progress">Progress</option>
              </select>
            </div>
          </div>

          {/* Filter tabs */}
          <div className="va-filter-row" role="tablist" aria-label="Filter workspaces">
            {FILTER_OPTIONS.map(f => (
              <button
                key={f}
                id={`va-filter-${f.toLowerCase().replace(' ', '-')}`}
                className={`va-filter-btn ${activeFilter === f ? 'active' : ''}`}
                role="tab"
                aria-selected={activeFilter === f}
                onClick={() => setActiveFilter(f)}
              >
                {f}
              </button>
            ))}
          </div>

          {/* Workspace grid */}
          {sorted.length > 0 ? (
            <div className="va-ws-grid" id="va-workspaces-grid">
              {sorted.map((ws, idx) => (
                <div
                  key={ws.id ?? idx}
                  id={`va-workspace-card-${ws.id ?? idx}`}
                  className="va-ws-card db-card"
                >
                  {/* Top accent strip */}
                  <div
                    className="va-ws-accent"
                    style={{ background: ICON_COLORS[idx % ICON_COLORS.length] }}
                  />

                  {/* Card body */}
                  <div className="va-ws-body">
                    <div
                      className="va-ws-icon"
                      style={{
                        background: ICON_COLORS[idx % ICON_COLORS.length],
                        boxShadow: `0 4px 14px ${ICON_COLORS[idx % ICON_COLORS.length]}44`,
                      }}
                    >
                      <WorkspaceIcon />
                    </div>

                    <h2 className="va-ws-name">{ws.name}</h2>
                    <p className="va-ws-meta">Last opened {ws.lastOpened}</p>

                    {/* Progress */}
                    <div className="va-ws-progress-section">
                      <div className="va-ws-progress-header">
                        <span className="va-ws-progress-label">Progress</span>
                        <span
                          className="va-ws-progress-pct"
                          style={{
                            color: ws.progress === 100 ? '#059669'
                              : ws.progress >= 50 ? '#2563eb'
                              : '#d97706'
                          }}
                        >
                          {ws.progress ?? 0}%
                        </span>
                      </div>
                      <ProgressBar value={ws.progress ?? 0} />
                    </div>

                    {/* Stats row */}
                    <div className="va-ws-stats">
                      <span className="va-ws-stat-pill">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M9 11l3 3L22 4" /><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
                        </svg>
                        {ws.quizCount ?? 0} quizzes
                      </span>
                      <span className="va-ws-stat-pill">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" />
                        </svg>
                        {ws.fileCount ?? 0} files
                      </span>
                    </div>

                    {/* Open button */}
                    <button
                      className="va-ws-open-btn"
                      id={`va-open-workspace-${ws.id ?? idx}`}
                      style={{ '--accent': ICON_COLORS[idx % ICON_COLORS.length] }}
                      onClick={() => navigate(`/workspace/${ws.id}`)}
                    >
                      Open Workspace
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="va-empty-state db-card" id="va-workspaces-empty">
              <span className="va-empty-icon"><InboxIcon /></span>
              <p className="va-empty-title">No workspaces found</p>
              <p className="va-empty-sub">
                {searchValue ? `No results for "${searchValue}"` : 'Create your first workspace to get started!'}
              </p>
            </div>
          )}
        </div>

        {/* ══ Sidebar (unchanged from dashboard) ══ */}
        <DashboardSidebar
          streak={streak}
          revisions={revisions}
          weekSummary={weekSummary}
          weeklyGraphImage={weeklyGraphImage}
        />

      </main>
    </div>
  );
}
