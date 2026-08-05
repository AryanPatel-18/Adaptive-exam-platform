//Also goes in the common. to use for search result
import ScoreRing,{DocumentIcon} from './svg'
import './QuizCard.css'

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

export default function QuizCard({
    score = 0,
    name = '',
    workspace = '',
    timeTaken = '',
    fraction = '',
    date = '',
    id = 0,
    idx = 0
}) {
    return (
        <div
            key={id ?? idx}
            id={`vaq-quiz-card-${id ?? idx}`}
            className="vaq-card db-card">
            {/* Score ring */}
            <div className="vaq-card-top">
                <ScoreRing pct={score ?? 0} />
                <span
                    className="vaq-score-badge"
                    style={{ background: `${scoreColor(score)}18`, color: scoreColor(score) }}
                >
                    {scoreLabel(score)}
                </span>
            </div>

            {/* Quiz info */}
            <div className="vaq-card-icon" aria-hidden="true">
                <DocumentIcon />
            </div>
            <h2 className="vaq-card-name">{name}</h2>
            <p className="vaq-card-workspace">{workspace}</p>

            {/* Meta pills */}
            <div className="vaq-meta-row">
                <span className="vaq-meta-pill">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
                    </svg>
                    {timeTaken}
                </span>
                <span className="vaq-meta-pill">
                    {fraction} correct
                </span>
            </div>

            <p className="vaq-card-date">{date}</p>

            {/* Retake button */}
            <button
                className="vaq-retake-btn"
                id={`vaq-retake-${id ?? idx}`}
            >
                Retake Quiz
            </button>
        </div>
    )

}