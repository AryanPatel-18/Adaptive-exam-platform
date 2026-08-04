import React, { useState } from 'react';
import Navbar from '../common/Navbar';
import DashboardSidebar from '../common/DashboardSidebar';
import { QuizeIcon, DocumentIcon, InboxIcon } from '../common/svg';
import './ViewAllQuizzes.css';
import '../home/Dashboard.css';

// ── Score colour helper ───────────────────────────────────────────────────────
function scoreColor(pct) {
  if (pct >= 80) return '#059669';
  if (pct >= 60) return '#d97706';
  return '#dc2626';
}

function scoreLabel(pct) {
  if (pct >= 80) return 'Excellent';
  if (pct >= 60) return 'Good';
  if (pct >= 40) return 'Fair';
  return 'Needs Work';
}

// ── Donut chart (SVG) ─────────────────────────────────────────────────────────
function ScoreRing({ pct }) {
  const r = 28;
  const circ = 2 * Math.PI * r;
  const fill = (pct / 100) * circ;
  const color = scoreColor(pct);
  return (
    <svg className="vaq-ring" viewBox="0 0 72 72" aria-hidden="true">
      <circle cx="36" cy="36" r={r} fill="none" stroke="#e5e7eb" strokeWidth="7" />
      <circle
        cx="36" cy="36" r={r} fill="none"
        stroke={color} strokeWidth="7"
        strokeDasharray={`${fill} ${circ}`}
        strokeLinecap="round"
        transform="rotate(-90 36 36)"
        style={{ transition: 'stroke-dasharray 0.6s ease' }}
      />
      <text x="36" y="41" textAnchor="middle" fontSize="14" fontWeight="700" fill={color}>
        {pct}%
      </text>
    </svg>
  );
}

// ── Sample quiz data (replace with real API data) ─────────────────────────────
const SAMPLE_QUIZZES = [
  { id: 1, name: 'Operating Systems Unit 1', workspace: 'OS Workspace', date: '2 hours ago', score: 93, fraction: '14/15', questions: 15, timeTaken: '8m 32s' },
  { id: 2, name: 'DBMS Normalization', workspace: 'DBMS Workspace', date: 'Yesterday', score: 80, fraction: '16/20', questions: 20, timeTaken: '14m 05s' },
  { id: 3, name: 'Data Structures - Trees', workspace: 'DSA Workspace', date: '3 days ago', score: 60, fraction: '9/15', questions: 15, timeTaken: '10m 48s' },
  { id: 4, name: 'Computer Networks - OSI Model', workspace: 'CN Workspace', date: '5 days ago', score: 45, fraction: '9/20', questions: 20, timeTaken: '18m 22s' },
  { id: 5, name: 'Software Engineering SDLC', workspace: 'SE Workspace', date: '1 week ago', score: 88, fraction: '22/25', questions: 25, timeTaken: '20m 11s' },
  { id: 6, name: 'Theory of Computation', workspace: 'TOC Workspace', date: '2 weeks ago', score: 35, fraction: '7/20', questions: 20, timeTaken: '16m 00s' },
  { id: 7, name: 'Compiler Design - Parsing', workspace: 'CD Workspace', date: '3 weeks ago', score: 72, fraction: '18/25', questions: 25, timeTaken: '22m 40s' },
  { id: 8, name: 'Machine Learning Basics', workspace: 'ML Workspace', date: 'Last month', score: 55, fraction: '11/20', questions: 20, timeTaken: '17m 55s' },
  { id: 9, name: 'Digital Electronics', workspace: 'DE Workspace', date: '6 weeks ago', score: 91, fraction: '23/25', questions: 25, timeTaken: '19m 15s' },
];

const FILTER_OPTIONS = ['All', 'Excellent', 'Good', 'Needs Work'];

function getFiltered(quizzes, filter, search) {
  let list = quizzes;
  if (search.trim()) {
    list = list.filter(q =>
      q.name.toLowerCase().includes(search.toLowerCase()) ||
      q.workspace?.toLowerCase().includes(search.toLowerCase())
    );
  }
  switch (filter) {
    case 'Excellent': return list.filter(q => q.score >= 80);
    case 'Good': return list.filter(q => q.score >= 60 && q.score < 80);
    case 'Needs Work': return list.filter(q => q.score < 60);
    default: return list;
  }
}

/**
 * ViewAllQuizzes – full page listing all quiz attempts.
 * Keeps the same Navbar + DashboardSidebar layout as Dashboard.
 */
export default function ViewAllQuizzes({
  quizzes = [],
  streak = { count: 0, daysCompleted: [false, false, false, false, false, false, false] },
  revisions = [],
  weekSummary = { avgAccuracy: '--', studyTime: '--' },
  weeklyGraphImage = '',
  onNavigateBack,
}) {
  const [activePage, setActivePage] = useState('quizzes');
  const [searchValue, setSearchValue] = useState('');
  const [activeFilter, setActiveFilter] = useState('All');
  const [sortBy, setSortBy] = useState('recent');
  const [viewMode, setViewMode] = useState('grid'); // 'grid' | 'list'

  const filtered = getFiltered(quizzes, activeFilter, searchValue);
  const sorted = [...filtered].sort((a, b) => {
    if (sortBy === 'score-high') return b.score - a.score;
    if (sortBy === 'score-low') return a.score - b.score;
    if (sortBy === 'name') return a.name.localeCompare(b.name);
    return 0; // 'recent'
  });

  const avgScore = quizzes.length > 0
    ? Math.round(quizzes.reduce((sum, q) => sum + q.score, 0) / quizzes.length)
    : 0;

  return (
    <div className="vaq-root db-root" id="view-all-quizzes-root">

      {/* ── Navbar ── */}
      <Navbar
        activePage={activePage}
        onNavigate={(id) => { setActivePage(id); if (id === 'home' && onNavigateBack) onNavigateBack(); }}
        notificationCount={0}
        searchValue={searchValue}
        onSearchChange={setSearchValue}
      />

      {/* ── Page body ── */}
      <main className="db-main vaq-main">

        {/* ══ Centre column ══ */}
        <div className="db-col-main">

          {/* Page header */}
          <div className="vaq-page-header">
            <div className="vaq-page-header-left">
              <div className="vaq-page-icon">
                <QuizeIcon />
              </div>
              <div>
                <h1 className="vaq-page-title">All Quizzes</h1>
                <p className="vaq-page-subtitle">{quizzes.length} attempt{quizzes.length !== 1 ? 's' : ''} · Avg score {avgScore}%</p>
              </div>
            </div>

            {/* View mode + sort */}
            <div className="vaq-controls">
              {/* View toggle */}
              <div className="vaq-view-toggle" role="group" aria-label="View mode">
                <button
                  className={`vaq-view-btn ${viewMode === 'grid' ? 'active' : ''}`}
                  id="vaq-view-grid-btn"
                  onClick={() => setViewMode('grid')}
                  aria-pressed={viewMode === 'grid'}
                  title="Grid view"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" />
                    <rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" />
                  </svg>
                </button>
                <button
                  className={`vaq-view-btn ${viewMode === 'list' ? 'active' : ''}`}
                  id="vaq-view-list-btn"
                  onClick={() => setViewMode('list')}
                  aria-pressed={viewMode === 'list'}
                  title="List view"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" />
                  </svg>
                </button>
              </div>

              {/* Sort */}
              <div className="va-sort-wrap">
                <label htmlFor="vaq-sort-select" className="va-sort-label">Sort by</label>
                <select
                  id="vaq-sort-select"
                  className="va-sort-select"
                  value={sortBy}
                  onChange={e => setSortBy(e.target.value)}
                >
                  <option value="recent">Most Recent</option>
                  <option value="score-high">Highest Score</option>
                  <option value="score-low">Lowest Score</option>
                  <option value="name">Name A–Z</option>
                </select>
              </div>
            </div>
          </div>

          {/* Filter tabs */}
          <div className="va-filter-row" role="tablist" aria-label="Filter quizzes">
            {FILTER_OPTIONS.map(f => (
              <button
                key={f}
                id={`vaq-filter-${f.toLowerCase().replace(' ', '-')}`}
                className={`va-filter-btn ${activeFilter === f ? 'active' : ''}`}
                role="tab"
                aria-selected={activeFilter === f}
                onClick={() => setActiveFilter(f)}
              >
                {f}
              </button>
            ))}
          </div>

          {/* Content */}
          {sorted.length > 0 ? (
            viewMode === 'grid' ? (
              // ── GRID VIEW ──────────────────────────────────────────────────
              <div className="vaq-grid" id="vaq-quizzes-grid">
                {sorted.map((qz, idx) => (
                  <div
                    key={qz.id ?? idx}
                    id={`vaq-quiz-card-${qz.id ?? idx}`}
                    className="vaq-card db-card"
                  >
                    {/* Score ring */}
                    <div className="vaq-card-top">
                      <ScoreRing pct={qz.score ?? 0} />
                      <span
                        className="vaq-score-badge"
                        style={{ background: `${scoreColor(qz.score)}18`, color: scoreColor(qz.score) }}
                      >
                        {scoreLabel(qz.score)}
                      </span>
                    </div>

                    {/* Quiz info */}
                    <div className="vaq-card-icon" aria-hidden="true">
                      <DocumentIcon />
                    </div>
                    <h2 className="vaq-card-name">{qz.name}</h2>
                    <p className="vaq-card-workspace">{qz.workspace}</p>

                    {/* Meta pills */}
                    <div className="vaq-meta-row">
                      <span className="vaq-meta-pill">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
                        </svg>
                        {qz.timeTaken}
                      </span>
                      <span className="vaq-meta-pill">
                        {qz.fraction} correct
                      </span>
                    </div>

                    <p className="vaq-card-date">{qz.date}</p>

                    {/* Retake button */}
                    <button
                      className="vaq-retake-btn"
                      id={`vaq-retake-${qz.id ?? idx}`}
                    >
                      Retake Quiz
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              // ── LIST VIEW ──────────────────────────────────────────────────
              <div className="vaq-list" id="vaq-quizzes-list">
                {sorted.map((qz, idx) => (
                  <div
                    key={qz.id ?? idx}
                    id={`vaq-list-item-${qz.id ?? idx}`}
                    className="vaq-list-item db-card"
                  >
                    <div className="vaq-list-icon" aria-hidden="true">
                      <DocumentIcon />
                    </div>

                    <div className="vaq-list-info">
                      <p className="vaq-list-name">{qz.name}</p>
                      <p className="vaq-list-meta">{qz.workspace} · {qz.date} · {qz.timeTaken}</p>
                    </div>

                    <div className="vaq-list-stats">
                      <span className="vaq-list-fraction">{qz.fraction}</span>
                      <span
                        className="vaq-list-pct"
                        style={{ color: scoreColor(qz.score) }}
                      >
                        {qz.score}%
                      </span>
                    </div>

                    <span
                      className="vaq-list-badge"
                      style={{ background: `${scoreColor(qz.score)}18`, color: scoreColor(qz.score) }}
                    >
                      {scoreLabel(qz.score)}
                    </span>

                    <button
                      className="vaq-list-retake-btn"
                      id={`vaq-list-retake-${qz.id ?? idx}`}
                    >
                      Retake
                    </button>
                  </div>
                ))}
              </div>
            )
          ) : (
            <div className="va-empty-state db-card" id="vaq-empty-state">
              <span className="va-empty-icon"><InboxIcon /></span>
              <p className="va-empty-title">No quizzes found</p>
              <p className="va-empty-sub">
                {searchValue ? `No results for "${searchValue}"` : 'Start a quiz from any workspace to see your results here!'}
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
