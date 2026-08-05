import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../api/axios';
import Navbar from '../common/Navbar';
import './ScheduleGenerator.css';

export default function ScheduleGenerator() {
  const { workspaceId } = useParams();
  const navigate = useNavigate();

  const [step, setStep] = useState(1);
  const [quizzes, setQuizzes] = useState([]);
  const [selectedQuiz, setSelectedQuiz] = useState(null);
  
  const [attempts, setAttempts] = useState([]);
  const [selectedAttempt, setSelectedAttempt] = useState(null);

  const [studyDays, setStudyDays] = useState(7);
  const [hoursPerDay, setHoursPerDay] = useState(2.0);
  const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0]);

  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    fetchQuizzes();
  }, [workspaceId]);

  const fetchQuizzes = async () => {
    setIsLoading(true);
    try {
      const res = await api.get(`/api/workspace/${workspaceId}/quizzes/`);
      setQuizzes(res.data.data || res.data); // Adjust based on API structure
    } catch (err) {
      console.error(err);
      setErrorMsg('Failed to load quizzes for this workspace.');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAttempts = async (quizId) => {
    setIsLoading(true);
    try {
      const res = await api.get(`/api/quiz/${quizId}/attempts/`);
      setAttempts(res.data);
      setStep(2);
    } catch (err) {
      console.error(err);
      setErrorMsg('Failed to load attempts for this quiz.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectQuiz = (quiz) => {
    setSelectedQuiz(quiz);
    setSelectedAttempt(null);
    fetchAttempts(quiz.id);
  };

  const handleSelectAttempt = (attempt) => {
    setSelectedAttempt(attempt);
    setStep(3);
  };

  const handleGenerate = async () => {
    if (!selectedAttempt) return;
    setIsGenerating(true);
    setErrorMsg('');
    try {
      await api.post(`/api/schedule/generate/`, {
        attempt_id: selectedAttempt.id,
        study_days: parseInt(studyDays, 10),
        hours_per_day: parseFloat(hoursPerDay).toFixed(2),
        start_date: startDate
      }, { timeout: 300000 }); // 5 minutes timeout for LLM generation
      // Currently redirects back to workspace on success
      navigate(`/workspace/${workspaceId}`);
    } catch (err) {
      console.error(err);
      setErrorMsg(err.response?.data?.message || err.response?.data?.detail || 'Failed to generate schedule.');
      setIsGenerating(false);
    }
  };

  const renderStepIndicator = () => (
    <div className="sg-step-indicator">
      <div className={`sg-step ${step >= 1 ? (step > 1 ? 'completed' : 'active') : ''}`}>
        1. Select Quiz
      </div>
      <div className={`sg-step ${step >= 2 ? (step > 2 ? 'completed' : 'active') : ''}`}>
        2. Select Attempt
      </div>
      <div className={`sg-step ${step >= 3 ? 'active' : ''}`}>
        3. Configure
      </div>
    </div>
  );

  return (
    <div className="sg-root">
      <Navbar activePage="workspace" onNavigate={() => navigate(`/workspace/${workspaceId}`)} />
      
      <main className="sg-main">
        <div className="sg-card">
          <h1 className="sg-title">Create Study Schedule</h1>
          
          {isGenerating ? (
            <div className="sg-loading">
              <div className="sg-spinner"></div>
              <h2>Generating Your Schedule...</h2>
              <p style={{ color: '#a1a1aa', marginTop: '1rem' }}>
                Our AI is analyzing your performance and creating a personalized study plan.
                This may take a few moments.
              </p>
            </div>
          ) : (
            <>
              {renderStepIndicator()}
              
              {errorMsg && (
                <div style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                  {errorMsg}
                </div>
              )}

              {step === 1 && (
                <div>
                  <h2 className="sg-subtitle">Choose a quiz to base your schedule on</h2>
                  {isLoading ? (
                    <div style={{ padding: '2rem', textAlign: 'center', color: '#6b7280' }}>Loading quizzes...</div>
                  ) : quizzes.length === 0 ? (
                    <div style={{ padding: '2rem', textAlign: 'center', color: '#6b7280' }}>
                      No quizzes available in this workspace. Create one first!
                    </div>
                  ) : (
                    <div className="sg-list">
                      {quizzes.map(quiz => (
                        <div 
                          key={quiz.id} 
                          className="sg-list-item"
                          onClick={() => handleSelectQuiz(quiz)}
                        >
                          <div>
                            <div className="sg-list-item-title">{quiz.title}</div>
                            <div className="sg-list-item-subtitle">
                              {quiz.total_questions} Questions • Created {new Date(quiz.created_at).toLocaleDateString()}
                            </div>
                          </div>
                          <div style={{ color: '#7c3aed', fontWeight: 500 }}>Select →</div>
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="sg-actions">
                    <button className="sg-btn sg-btn-outline" onClick={() => navigate(`/workspace/${workspaceId}`)}>
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              {step === 2 && (
                <div>
                  <h2 className="sg-subtitle">Select a completed attempt for {selectedQuiz?.title}</h2>
                  {isLoading ? (
                    <div style={{ padding: '2rem', textAlign: 'center', color: '#6b7280' }}>Loading attempts...</div>
                  ) : attempts.length === 0 ? (
                    <div style={{ padding: '2rem', textAlign: 'center', color: '#6b7280' }}>
                      You haven't completed any attempts for this quiz yet. You must finish a quiz before a schedule can be generated.
                    </div>
                  ) : (
                    <div className="sg-list">
                      {attempts.map(attempt => (
                        <div 
                          key={attempt.id} 
                          className="sg-list-item"
                          onClick={() => handleSelectAttempt(attempt)}
                        >
                          <div>
                            <div className="sg-list-item-title">
                              Attempt {attempt.attempt_number}
                            </div>
                            <div className="sg-list-item-subtitle">
                              Score: {attempt.score}/{attempt.total_marks} ({attempt.percentage}%) • 
                              Completed: {new Date(attempt.completed_at).toLocaleString()}
                            </div>
                          </div>
                          <div style={{ color: '#7c3aed', fontWeight: 500 }}>Select →</div>
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="sg-actions">
                    <button className="sg-btn sg-btn-outline" onClick={() => setStep(1)}>
                      ← Back
                    </button>
                  </div>
                </div>
              )}

              {step === 3 && (
                <div>
                  <h2 className="sg-subtitle">Configure your study constraints</h2>
                  
                  <div className="sg-form-group">
                    <label className="sg-label">Study Days</label>
                    <input 
                      type="number" 
                      className="sg-input" 
                      min="1" 
                      max="90" 
                      value={studyDays}
                      onChange={(e) => setStudyDays(e.target.value)}
                    />
                    <div style={{ fontSize: '0.75rem', color: '#71717a', marginTop: '0.5rem' }}>How many days do you want this schedule to span?</div>
                  </div>

                  <div className="sg-form-group">
                    <label className="sg-label">Hours per Day</label>
                    <input 
                      type="number" 
                      className="sg-input" 
                      min="0.5" 
                      max="24" 
                      step="0.5"
                      value={hoursPerDay}
                      onChange={(e) => setHoursPerDay(e.target.value)}
                    />
                    <div style={{ fontSize: '0.75rem', color: '#71717a', marginTop: '0.5rem' }}>How many hours can you commit to studying each day?</div>
                  </div>

                  <div className="sg-form-group">
                    <label className="sg-label">Start Date</label>
                    <input 
                      type="date" 
                      className="sg-input" 
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                    />
                  </div>

                  <div className="sg-actions">
                    <button className="sg-btn sg-btn-outline" onClick={() => setStep(2)}>
                      ← Back
                    </button>
                    <button className="sg-btn sg-btn-primary" onClick={handleGenerate} disabled={!studyDays || !hoursPerDay || !startDate}>
                      Generate Schedule
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
