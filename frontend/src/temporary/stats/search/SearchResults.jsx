import React, { useState } from 'react';
import Navbar from '../common/Navbar';
import { WorkspaceIcon, QuizeIcon, InboxIcon } from '../common/svg';
import './SearchResults.css';
import '../home/Dashboard.css';

/**
 * SearchResults – Generic search results page.
 *
 * Props:
 *   query     {string}  – Pre-filled in the search bar
 *   results   {Array}   – Array of result objects:
 *
 *     Workspace: { type: 'workspace', id, name, meta, tag, progress, color? }
 *     Quiz:      { type: 'quiz',      id, name, meta, tag, score, fraction   }
 *
 *   isLoading {boolean} – show skeleton shimmer while fetching
 *   onClose   {fn}      – called when the user clears the search
 */
export default function SearchResults({
  query = '',
  results = [],
  isLoading = false,
  onClose = () => {},
}) {
  const [searchValue, setSearchValue] = useState(query);
  const [activeFilter, setActiveFilter] = useState('All');
  const [activePage, setActivePage] = useState('search');

  const filtered = results.filter(r => {
    if (activeFilter === 'Workspaces') return r.type === 'workspace';
    if (activeFilter === 'Quizzes')    return r.type === 'quiz';
    return true;
  });

  const workspaceCount = results.filter(r => r.type === 'workspace').length;
  const quizCount      = results.filter(r => r.type === 'quiz').length;

  return (
    <div className="sr-root db-root">

      {/* ── Navbar with query pre-filled ── */}
      <Navbar
        activePage={activePage}
        onNavigate={setActivePage}
        notificationCount={0}
        searchValue={searchValue}
        onSearchChange={setSearchValue}
      />

      <div className="sr-page-body">

        {/* ── Result count + filter pills in one bar ── */}
        <div className="sr-toolbar">

          <div className="sr-filter-row">
            {['All', 'Workspaces', 'Quizzes'].map(f => (
              <button
                key={f}
                className={`sr-filter-btn ${activeFilter === f ? 'active' : ''}`}
                onClick={() => setActiveFilter(f)}
              >
                {f === 'Workspaces' && <WorkspaceIcon />}
                {f === 'Quizzes'    && <QuizeIcon />}
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* ── Result cards ── */}
        {isLoading ? (
          <div className="sr-grid">
            {[1, 2, 3, 4, 5, 6].map(i => <SkeletonCard key={i} />)}
          </div>
        ) : filtered.length === 0 ? (
          <EmptyState query={query} filter={activeFilter} />
        ) : (
          <div className="sr-grid">
            {filtered.map((item, idx) =>
              item.type === 'workspace'
                ? <WorkspaceCard key={item.id ?? idx} item={item} />
                : <QuizCard      key={item.id ?? idx} item={item} />
            )}
          </div>
        )}

      </div>
    </div>
  );
}

// ── Workspace result card ─────────────────────────────────────────────────────
const WS_COLORS = ['#7c3aed', '#2563eb', '#059669', '#d97706', '#dc2626', '#0891b2'];

function WorkspaceCard({ item }) {
  const accentColor = item.color ?? WS_COLORS[(item.id ?? 0) % WS_COLORS.length];
  const progress    = item.progress ?? 0;
  const barColor    = progress === 100 ? '#059669' : progress >= 50 ? '#2563eb' : '#d97706';

  return (
    <div className="sr-card sr-ws-card db-card">
      <div className="sr-ws-accent" style={{ background: accentColor }} />

      <div className="sr-card-body">
        <div className="sr-card-top">
          <div className="sr-ws-icon" style={{ background: accentColor, boxShadow: `0 4px 14px ${accentColor}44` }}>
            <WorkspaceIcon />
          </div>
          <span className="sr-type-badge sr-type-ws">Workspace</span>
        </div>

        {item.tag && <span className="sr-subject-tag">{item.tag}</span>}
        <h3 className="sr-card-name">{item.name}</h3>
        <p className="sr-card-meta">{item.meta}</p>

        <div className="sr-progress-section">
          <div className="sr-progress-header">
            <span className="sr-progress-label">Progress</span>
            <span className="sr-progress-pct" style={{ color: barColor }}>{progress}%</span>
          </div>
          <div className="sr-progress-track">
            <div className="sr-progress-fill" style={{ width: `${progress}%`, background: barColor }} />
          </div>
        </div>

        <button className="sr-open-btn" style={{ background: accentColor }}>
          Open Workspace
        </button>
      </div>
    </div>
  );
}

// ── Quiz result card ──────────────────────────────────────────────────────────
function scoreColor(pct) {
  if (pct >= 80) return '#059669';
  if (pct >= 60) return '#d97706';
  return '#dc2626';
}

function QuizCard({ item }) {
  const score = item.score ?? 0;
  const color = scoreColor(score);

  return (
    <div className="sr-card sr-quiz-card db-card">
      <div className="sr-ws-accent" style={{ background: color }} />

      <div className="sr-card-body">
        <div className="sr-card-top">
          <div className="sr-quiz-icon" style={{ background: `${color}15`, color }}>
            <QuizeIcon />
          </div>
          <span className="sr-type-badge sr-type-quiz">Quiz</span>
        </div>

        {item.tag && <span className="sr-subject-tag">{item.tag}</span>}
        <h3 className="sr-card-name">{item.name}</h3>
        <p className="sr-card-meta">{item.meta}</p>

        <div className="sr-score-row">
          <span className="sr-score-pct" style={{ color }}>{score}%</span>
          {item.fraction && <span className="sr-score-frac">{item.fraction}</span>}
          <div className="sr-score-bar-track">
            <div className="sr-score-bar-fill" style={{ width: `${score}%`, background: color }} />
          </div>
        </div>

        <button className="sr-open-btn" style={{ background: color }}>
          View Results
        </button>
      </div>
    </div>
  );
}

// ── Skeleton shimmer card ─────────────────────────────────────────────────────
function SkeletonCard() {
  return (
    <div className="sr-card sr-skeleton db-card">
      <div className="sr-skel-strip" />
      <div className="sr-card-body">
        <div className="sr-skel-icon" />
        <div className="sr-skel-line sr-skel-tag" />
        <div className="sr-skel-line sr-skel-title" />
        <div className="sr-skel-line sr-skel-meta" />
        <div className="sr-skel-line sr-skel-bar" />
        <div className="sr-skel-line sr-skel-btn" />
      </div>
    </div>
  );
}

// ── Empty state ───────────────────────────────────────────────────────────────
function EmptyState({ query, filter }) {
  return (
    <div className="sr-empty db-card">
      <span className="sr-empty-icon"><InboxIcon /></span>
      <p className="sr-empty-title">
        {filter === 'All'
          ? `No results for "${query}"`
          : `No ${filter.toLowerCase()} match "${query}"`}
      </p>
      <p className="sr-empty-sub">Try a different keyword or check your spelling.</p>
    </div>
  );
}
