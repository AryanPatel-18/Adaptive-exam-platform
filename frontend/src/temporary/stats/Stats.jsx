import React, { useState } from 'react';
import Navbar from '../common/Navbar';
import DashboardSidebar from '../common/DashboardSidebar';
import {
  WorkspaceIcon,
  QuizeIcon,
  ClockIcon,
  TargetIcon,
  TrendingIcon,
} from '../common/svg';
import './Stats.css';

/**
 * Stats – User Statistics page.
 *
 * All data is currently static placeholder values.
 * Replace the constant blocks below with real API data when the backend is ready.
 *
 * Props:
 *   streak        {object}  – { count, daysCompleted: boolean[7] }
 *   revisions     {Array}   – [{ id, subject, timing, timingColor }]
 *   weekSummary   {object}  – { avgAccuracy: string, studyTime: string }
 *   weeklyGraphImage {string}
 */
export default function Stats({
  streak = { count: 0, daysCompleted: [false, false, false, false, false, false, false] },
  revisions = [],
  weekSummary = { avgAccuracy: '--', studyTime: '--' },
  weeklyGraphImage = '',
}) {
  const [activeTab, setActiveTab] = useState('all'); // 'all' | 'week' | 'workspaces'

  // ── Placeholder data (swap with API responses) ──────────────────────────
  const allTimeStats = {
    totalQuizzes: '--',
    avgAccuracy: '--',
    totalHours: '--',
    questionsSolved: '--',
    activeDays: '--',
    completionRate: 0,
    successRate: 0,
  };

  const weeklyActivity = [
    { day: 'Mon', hours: 0 },
    { day: 'Tue', hours: 0 },
    { day: 'Wed', hours: 0 },
    { day: 'Thu', hours: 0 },
    { day: 'Fri', hours: 0 },
    { day: 'Sat', hours: 0 },
    { day: 'Sun', hours: 0 },
  ];

  const workspaceStats = [
    // { id, name, quizzesCount, avgAccuracy (0-100), studyTime, questionsCount, color }
  ];
  // ────────────────────────────────────────────────────────────────────────

  const maxWeeklyHours = Math.max(...weeklyActivity.map(d => d.hours), 1);

  return (
    <div className="db-root">
      <main className="db-main">
        <div className="db-col-main">

          {/* ── Hero banner ── */}
          <section className="stats-hero db-card">
            <div className="stats-hero-text">
              <span className="stats-badge">Performance Analytics</span>
              <h1 className="stats-title">Your Learning Analytics</h1>
              <p className="stats-subtitle">
                Review your study patterns, workspace performance, and quiz accuracy.
              </p>
            </div>
            <div className="stats-hero-graphic">
              <div className="stats-glow" />
              <span className="stats-emoji">📊</span>
            </div>
          </section>

          {/* ── Tabs ── */}
          <div className="stats-tabs-row" role="tablist">
            {[
              { id: 'all',        label: 'All-Time Summary' },
              { id: 'week',       label: "This Week's Activity" },
              { id: 'workspaces', label: 'Workspace Breakdown' },
            ].map(t => (
              <button
                key={t.id}
                role="tab"
                aria-selected={activeTab === t.id}
                className={`stats-tab-btn ${activeTab === t.id ? 'active' : ''}`}
                onClick={() => setActiveTab(t.id)}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* ══ TAB: ALL-TIME ══ */}
          {activeTab === 'all' && (
            <div className="stats-tab-content fade-in">
              {/* Stat cards */}
              <div className="stats-grid">
                <StatMiniCard
                  icon={<QuizeIcon />}
                  colorClass="violet-bg"
                  label="Quizzes Taken"
                  value={allTimeStats.totalQuizzes}
                  sub="All-time"
                />
                <StatMiniCard
                  icon={<TargetIcon />}
                  colorClass="green-bg"
                  label="Avg. Accuracy"
                  value={allTimeStats.avgAccuracy}
                  sub="All-time"
                />
                <StatMiniCard
                  icon={<ClockIcon />}
                  colorClass="blue-bg"
                  label="Total Study Time"
                  value={allTimeStats.totalHours === '--' ? '--' : `${allTimeStats.totalHours} hrs`}
                  sub={`${allTimeStats.activeDays} active days`}
                />
                <StatMiniCard
                  icon={<TrendingIcon />}
                  colorClass="orange-bg"
                  label="Questions Solved"
                  value={allTimeStats.questionsSolved}
                  sub="All-time"
                />
              </div>

              {/* Progress bars */}
              <div className="stats-insight-card db-card">
                <h3 className="stats-section-title">All-Time Achievements</h3>
                <div className="stats-progress-box-grid">
                  <ProgressBox
                    label="Overall Quiz Completion"
                    value={allTimeStats.completionRate}
                    fillClass="violet-fill"
                  />
                  <ProgressBox
                    label="Success Rate"
                    value={allTimeStats.successRate}
                    fillClass="green-fill"
                  />
                </div>
              </div>
            </div>
          )}

          {/* ══ TAB: THIS WEEK ══ */}
          {activeTab === 'week' && (
            <div className="stats-tab-content fade-in">
              <div className="stats-weekly-grid">
                {/* Bar chart */}
                <div className="stats-chart-card db-card">
                  <h3 className="stats-section-title">Hours Studied per Day</h3>
                  <div className="stats-bar-chart">
                    {weeklyActivity.map((d, i) => (
                      <div key={i} className="stats-chart-column">
                        <div className="stats-bar-wrapper">
                          <span className="stats-bar-tooltip">{d.hours} hrs</span>
                          <div
                            className="stats-chart-bar"
                            style={{ height: `${(d.hours / maxWeeklyHours) * 100}%` }}
                          />
                        </div>
                        <span className="stats-chart-label">{d.day}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Weekly summary */}
                <div className="stats-metrics-card db-card">
                  <h3 className="stats-section-title">Weekly Summary</h3>
                  <ul className="stats-metrics-list">
                    <MetricItem
                      dotClass="violet-bg"
                      name="Avg. Accuracy"
                      desc="This week"
                      value={weekSummary.avgAccuracy}
                      fontClass="font-violet"
                    />
                    <MetricItem
                      dotClass="blue-bg"
                      name="Study Time"
                      desc="This week"
                      value={weekSummary.studyTime}
                      fontClass="font-blue"
                    />
                    <MetricItem
                      dotClass="orange-bg"
                      name="Active Streak"
                      desc="Consecutive days"
                      value={`${streak.count} ${streak.count === 1 ? 'day' : 'days'} 🔥`}
                      fontClass="font-orange"
                    />
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* ══ TAB: WORKSPACES ══ */}
          {activeTab === 'workspaces' && (
            <div className="stats-tab-content fade-in">
              {workspaceStats.length === 0 ? (
                <div className="stats-empty-state db-card">
                  <span className="stats-empty-icon">📂</span>
                  <p className="stats-empty-msg">No workspace data yet. Complete some quizzes to see stats here.</p>
                </div>
              ) : (
                <div className="workspaces-stats-list">
                  {workspaceStats.map(ws => (
                    <div key={ws.id} className="workspace-stat-item db-card">
                      <div className="workspace-stat-header">
                        <div className="workspace-stat-title-group">
                          <span
                            className="workspace-stat-icon-wrapper"
                            style={{ color: ws.color, backgroundColor: `${ws.color}15` }}
                          >
                            <WorkspaceIcon />
                          </span>
                          <div>
                            <h4 className="workspace-stat-name">{ws.name}</h4>
                            <p className="workspace-stat-meta">
                              {ws.quizzesCount} Quizzes taken • {ws.studyTime} spent
                            </p>
                          </div>
                        </div>
                        <span className="workspace-stat-acc-val" style={{ color: ws.color }}>
                          {ws.avgAccuracy}% Accuracy
                        </span>
                      </div>
                      <div className="workspace-stat-body">
                        <div className="workspace-stat-bar-track">
                          <div
                            className="workspace-stat-bar-fill"
                            style={{ width: `${ws.avgAccuracy}%`, backgroundColor: ws.color }}
                          />
                        </div>
                        <div className="workspace-stat-info-row">
                          <span>{ws.questionsCount} Questions Solved</span>
                          <span>Avg. Score: {(ws.avgAccuracy * 0.1).toFixed(1)} / 10</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

        </div>

        {/* ── Sidebar ── */}
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

// ── Small helper components ───────────────────────────────────────────────────

function StatMiniCard({ icon, colorClass, label, value, sub }) {
  return (
    <div className="stats-mini-card db-card">
      <div className={`stats-mini-icon ${colorClass}`}>{icon}</div>
      <div className="stats-mini-info">
        <p className="stats-mini-label">{label}</p>
        <p className="stats-mini-value">{value}</p>
        <span className="stats-mini-sub">{sub}</span>
      </div>
    </div>
  );
}

function ProgressBox({ label, value, fillClass }) {
  return (
    <div className="stats-progress-box">
      <div className="stats-progress-box-header">
        <span>{label}</span>
        <span>{value}%</span>
      </div>
      <div className="stats-progress-track">
        <div className={`stats-progress-fill ${fillClass}`} style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

function MetricItem({ dotClass, name, desc, value, fontClass }) {
  return (
    <li className="stats-metric-item">
      <span className={`stats-metric-dot ${dotClass}`} />
      <div className="stats-metric-details">
        <span className="stats-metric-name">{name}</span>
        <span className="stats-metric-desc">{desc}</span>
      </div>
      <span className={`stats-metric-val ${fontClass}`}>{value}</span>
    </li>
  );
}
