import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../api/axios';
import Navbar from '../common/Navbar';
import './ScheduleView.css';

export default function ScheduleView() {
  const { id: workspaceId, scheduleId } = useParams();
  const navigate = useNavigate();

  const [schedule, setSchedule] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    fetchSchedule();
  }, [scheduleId]);

  const fetchSchedule = async () => {
    setIsLoading(true);
    try {
      const res = await api.get(`/api/schedule/${scheduleId}/`);
      setSchedule(res.data);
    } catch (err) {
      console.error(err);
      setErrorMsg('Failed to load schedule. It may have been deleted or does not exist.');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="sv-root db-root">
        <Navbar activePage="workspace" onNavigate={() => navigate(`/workspace/${workspaceId}`)} />
        <main className="sv-main db-main">
          <div style={{ margin: 'auto', textAlign: 'center', color: '#6b7280' }}>
            <div className="sv-spinner"></div>
            <p style={{ marginTop: '1rem' }}>Loading study plan...</p>
          </div>
        </main>
      </div>
    );
  }

  if (errorMsg || !schedule) {
    return (
      <div className="sv-root db-root">
        <Navbar activePage="workspace" onNavigate={() => navigate(`/workspace/${workspaceId}`)} />
        <main className="sv-main db-main">
          <div className="db-card" style={{ maxWidth: '600px', margin: '2rem auto', textAlign: 'center', padding: '3rem 2rem' }}>
            <h2 style={{ color: '#ef4444', marginBottom: '1rem' }}>Oops!</h2>
            <p style={{ color: '#6b7280', marginBottom: '2rem' }}>{errorMsg}</p>
            <button className="sv-btn-primary" onClick={() => navigate(`/workspace/${workspaceId}`)}>
              Back to Workspace
            </button>
          </div>
        </main>
      </div>
    );
  }

  const { generated_plan, start_date, end_date } = schedule;
  const summary = generated_plan?.summary || {};
  const topicsList = generated_plan?.schedule || [];

  const getPriorityColor = (priority) => {
    const p = priority?.toLowerCase() || '';
    if (p.includes('high')) return { bg: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', border: 'rgba(239, 68, 68, 0.2)' };
    if (p.includes('medium')) return { bg: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b', border: 'rgba(245, 158, 11, 0.2)' };
    return { bg: 'rgba(16, 185, 129, 0.1)', color: '#10b981', border: 'rgba(16, 185, 129, 0.2)' };
  };

  return (
    <div className="sv-root db-root">
      <Navbar activePage="workspace" onNavigate={() => navigate(`/workspace/${workspaceId}`)} />

      <main className="sv-main db-main">
        <div className="sv-container">
          
          <div className="sv-header">
            <button className="sv-back-btn" onClick={() => navigate(`/workspace/${workspaceId}`)}>
              ← Back
            </button>
            <h1 className="sv-title">Your Personalized Study Plan</h1>
            <p className="sv-subtitle">
              Generated based on your quiz performance. Spanning from <strong>{start_date}</strong> to <strong>{end_date}</strong>.
            </p>
          </div>

          <div className="sv-summary-card db-card">
            <div className="sv-summary-stats">
              <div className="sv-stat-item">
                <span className="sv-stat-value">{schedule.preparedness_score}%</span>
                <span className="sv-stat-label">Preparedness Score</span>
              </div>
              <div className="sv-stat-item">
                <span className="sv-stat-value" style={{ fontSize: '1.5rem', marginTop: '0.5rem' }}>{summary.overall_level || 'Evaluated'}</span>
                <span className="sv-stat-label">Overall Level</span>
              </div>
              <div className="sv-stat-item">
                <span className="sv-stat-value" style={{ fontSize: '1.5rem', marginTop: '0.5rem' }}>{topicsList.length}</span>
                <span className="sv-stat-label">Topics to Cover</span>
              </div>
            </div>
            {summary.recommendation && (
              <div className="sv-recommendation">
                <h3>AI Recommendation</h3>
                <p>{summary.recommendation}</p>
              </div>
            )}
          </div>

          <div className="sv-topics-container">
            {topicsList.map((topic, index) => {
              const colors = getPriorityColor(topic.priority);
              return (
                <div key={index} className="sv-topic-card db-card">
                  <div className="sv-topic-header">
                    <h3 className="sv-topic-name">{topic.topic}</h3>
                    <span 
                      className="sv-topic-priority"
                      style={{ backgroundColor: colors.bg, color: colors.color, borderColor: colors.border }}
                    >
                      {topic.priority || 'Normal'} Priority
                    </span>
                  </div>
                  
                  <div className="sv-topic-bottom">
                    {topic.reason && (
                      <p className="sv-topic-reason">{topic.reason}</p>
                    )}
                    <span className="sv-topic-duration">
                      <span className="sv-duration-icon">⏱️</span> {topic.duration_hours}h
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

        </div>
      </main>
    </div>
  );
}
