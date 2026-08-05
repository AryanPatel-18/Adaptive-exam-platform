// This goes in the common folder
import './WorkspaceCard.css';
import { WorkspaceIcon } from './svg';
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

const ICON_COLORS = [
  '#7c3aed', '#2563eb', '#059669', '#d97706', '#dc2626',
  '#0891b2', '#7c3aed', '#db2777', '#65a30d', '#ea580c',
];

function WorkspaceCard ({
    id = 0,
    name = '',
    lastOpened = '',
    progress = 0,
    quizCount = 0,
    fileCount = 0,
    idx = 0
}) {
    return (
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

        <h2 className="va-ws-name">{name}</h2>
        <p className="va-ws-meta">Last opened {lastOpened}</p>

        {/* Progress */}
        <div className="va-ws-progress-section">
            <div className="va-ws-progress-header">
                <span className="va-ws-progress-label">Progress</span>
                <span
                    className="va-ws-progress-pct"
                    style={{
                        color: progress === 100 ? '#059669'
                            : progress >= 50 ? '#2563eb'
                                : '#d97706'
                    }}
                >
                    {progress ?? 0}%
                </span>
            </div>
            <ProgressBar value={progress ?? 0} />
        </div>

        {/* Stats row */}
        <div className="va-ws-stats">
            <span className="va-ws-stat-pill">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M9 11l3 3L22 4" /><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
                </svg>
                {quizCount ?? 0} quizzes
            </span>
            <span className="va-ws-stat-pill">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" />
                </svg>
                {fileCount ?? 0} files
            </span>
        </div>

        {/* Open button */}
        <button
            className="va-ws-open-btn"
            id={`va-open-workspace-${id ?? idx}`}
            style={{ '--accent': ICON_COLORS[idx % ICON_COLORS.length] }}
        >
            Open Workspace
        </button>
    </div>
)}

export default WorkspaceCard