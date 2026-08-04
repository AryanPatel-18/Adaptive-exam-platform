import React from 'react';
import { FlameIcon, CalenderIcon, ChevronRightIcon } from './svg';
import '../home/Dashboard.css';

const DAYS_OF_WEEK = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];

/**
 * DashboardSidebar – reusable right-hand sidebar used on Dashboard,
 * ViewAllWorkspaces and ViewAllQuizzes pages.
 *
 * Props:
 *   streak        {object}  – { count, daysCompleted: boolean[7] }
 *   revisions     {Array}   – [{ id, subject, timing, timingColor }]
 *   weekSummary   {object}  – { avgAccuracy: string, studyTime: string }
 *   weeklyGraphImage {string} – URL/path for the weekly chart image
 */
export default function DashboardSidebar({
  streak = { count: 0, daysCompleted: [false, false, false, false, false, false, false] },
  revisions = [],
  weekSummary = { avgAccuracy: '--', studyTime: '--' },
  weeklyGraphImage = '',
}) {
  return (
    <aside className="db-sidebar">

      {/* Study Streak */}
      <section className="db-card db-sidebar-card" id="db-streak-card" aria-label="Study streak">
        <div className="db-streak-header">
          <span className="db-flame" aria-hidden="true"><FlameIcon /></span>
          <h2 className="db-sidebar-title">Study Streak</h2>
        </div>
        <div className="db-streak-count">
          <span className="db-streak-num">{streak.count}</span>
          <span className="db-streak-unit">days</span>
        </div>
        <p className="db-streak-tagline">
          {streak.count > 0 ? "You're on fire! Keep it up!" : 'Start studying to build your streak!'}
        </p>
        <div className="db-streak-days" aria-label="Days studied this week">
          {DAYS_OF_WEEK.map((d, i) => {
            const done = streak.daysCompleted?.[i] ?? false;
            return (
              <div key={i} className="db-streak-day">
                <span className="db-day-lbl">{d}</span>
                <div className={`db-day-dot ${done ? 'done' : ''}`} aria-label={done ? 'Studied' : 'Not studied'}>
                  {done && (
                    <svg viewBox="0 0 10 10" fill="none" aria-hidden="true">
                      <polyline points="2,5 4.5,7.5 8,3" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Upcoming Revision */}
      <section className="db-card db-sidebar-card" id="db-revision-card" aria-label="Upcoming revisions">
        <div className="db-sidebar-hdr">
          <span className="db-list-header-icon" aria-hidden="true"><CalenderIcon /></span>
          <h2 className="db-sidebar-title">Upcoming Revision</h2>
        </div>
        <ul className="db-revision-list" role="list">
          {revisions.length > 0 ? (
            revisions.map((r, idx) => (
              <li key={r.id ?? idx} className="db-revision-item" id={`revision-${r.id ?? idx}`}>
                <span className="db-revision-subject">{r.subject}</span>
                <span className="db-revision-timing" style={{ color: r.timingColor ?? '#6b7280' }}>
                  {r.timing}
                </span>
              </li>
            ))
          ) : (
            <li className="db-empty-state db-revision-empty">
              <p className="db-empty-msg">No upcoming revisions scheduled.</p>
            </li>
          )}
        </ul>
        <button className="db-study-plan-btn" id="db-view-study-plan-btn">
          View Study Plan
          <span className="db-btn-chevron" aria-hidden="true"><ChevronRightIcon /></span>
        </button>
      </section>

      {/* This Week Overview */}
      <section className="db-card db-sidebar-card" id="db-week-overview-card" aria-label="This week overview">
        <h2 className="db-sidebar-title">This Week Overview</h2>
        <div className="db-week-chart-wrap">
          <img
            src={weeklyGraphImage}
            alt="Weekly study overview"
            className="db-week-chart-image"
            loading="lazy"
            draggable={false}
          />
          <div className="db-week-x-labels">
            {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(d => (
              <span key={d}>{d}</span>
            ))}
          </div>
        </div>
        <div className="db-week-stats">
          <div className="db-week-stat">
            <p className="db-week-val">{weekSummary.avgAccuracy}</p>
            <p className="db-week-lbl">Avg. Accuracy</p>
          </div>
          <div className="db-week-stat">
            <p className="db-week-val">{weekSummary.studyTime}</p>
            <p className="db-week-lbl">Study Time</p>
          </div>
        </div>
      </section>

    </aside>
  );
}
