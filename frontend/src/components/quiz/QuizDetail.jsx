import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../api/axios';
import Navbar from '../common/Navbar';
import './QuizDetail.css';

const QuizDetail = () => {
  const { workspaceId } = useParams();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, [workspaceId]);

  const fetchStats = async () => {
    try {
      const response = await api.get(`/api/quiz/workspace/${workspaceId}/stats/`);
      setStats(response.data);
    } catch (error) {
      console.error("Failed to fetch quiz stats:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds) => {
    if (!seconds) return '0m';
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    if (hrs > 0) return `${hrs}h ${mins}m`;
    return `${mins}m`;
  };

  if (loading) {
    return (
      <div className="qd-layout">
        <Navbar activePage="workspaces" />
        <div className="qd-loading">
          <div className="qd-spinner"></div>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="qd-layout">
        <Navbar activePage="workspaces" />
        <div className="qd-error">Failed to load statistics.</div>
      </div>
    );
  }

  const { overview, topics, hardest_questions } = stats;

  return (
    <div className="qd-layout">
      <Navbar activePage="workspaces" />
      
      <main className="qd-main-container">
        <div className="qd-header-row">
          <button className="qd-back-btn" onClick={() => navigate(`/workspace/${workspaceId}`)}>
            ← Back to Workspace
          </button>
          <h1>Workspace Quiz Analytics</h1>
          <p>A detailed breakdown of all your quiz performances in this workspace.</p>
        </div>

        {/* Overview Cards */}
        <div className="qd-overview-grid">
          <div className="qd-card">
            <span className="qd-card-icon">📝</span>
            <div className="qd-card-info">
              <h3>{overview.total_quizzes}</h3>
              <p>Quizzes Created</p>
            </div>
          </div>
          <div className="qd-card">
            <span className="qd-card-icon">✅</span>
            <div className="qd-card-info">
              <h3>{overview.total_attempts}</h3>
              <p>Completed Attempts</p>
            </div>
          </div>
          <div className="qd-card">
            <span className="qd-card-icon">🎯</span>
            <div className="qd-card-info">
              <h3>{overview.average_score}%</h3>
              <p>Average Accuracy</p>
            </div>
          </div>
          <div className="qd-card">
            <span className="qd-card-icon">⏱️</span>
            <div className="qd-card-info">
              <h3>{formatTime(overview.total_time_spent_seconds)}</h3>
              <p>Time Spent Studying</p>
            </div>
          </div>
        </div>

        <div className="qd-content-grid">
          {/* Topic Performance */}
          <div className="qd-topics-section qd-panel">
            <h2>Topic Performance</h2>
            {topics && topics.length > 0 ? (
              <div className="qd-topic-list">
                {topics.map((t, idx) => (
                  <div key={idx} className="qd-topic-item">
                    <div className="qd-topic-header">
                      <span className="qd-topic-name">{t.topic}</span>
                      <span className="qd-topic-acc">{t.accuracy}% ({t.correct}/{t.total_questions})</span>
                    </div>
                    <div className="qd-progress-bar">
                      <div 
                        className={`qd-progress-fill ${t.accuracy >= 70 ? 'good' : t.accuracy >= 40 ? 'avg' : 'poor'}`} 
                        style={{ width: `${t.accuracy}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="qd-empty-state">No topic data available yet.</div>
            )}
          </div>

          {/* Hardest Questions */}
          <div className="qd-hardest-section qd-panel">
            <h2>Areas for Improvement (Hardest Questions)</h2>
            {hardest_questions && hardest_questions.length > 0 ? (
              <div className="qd-question-list">
                {hardest_questions.map((q, idx) => (
                  <div key={idx} className="qd-question-item">
                    <div className="qd-question-accuracy">
                      <span className="qd-acc-badge">{q.accuracy}% Correct</span>
                    </div>
                    <p className="qd-question-text">{q.question}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="qd-empty-state">No question data available yet. Take some quizzes to see areas for improvement!</div>
            )}
          </div>
        </div>

      </main>
    </div>
  );
};

export default QuizDetail;
