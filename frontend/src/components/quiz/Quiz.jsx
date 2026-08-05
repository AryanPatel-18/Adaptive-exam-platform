import React, { useState, useEffect, useRef } from 'react';
import api from '../../api/axios';
import './Quiz.css';

// ── SVG Icons ────────────────────────────────────────────────────────────────
const Icon = {
  chevronLeft: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="15 18 9 12 15 6" />
    </svg>
  ),
  chevronRight: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="9 18 15 12 9 6" />
    </svg>
  ),
  check: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  ),
  trophy: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6" />
      <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18" />
      <path d="M4 22h16" />
      <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22" />
      <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22" />
      <path d="M18 2H6v7a6 6 0 0 0 12 0V2z" />
    </svg>
  ),
  alert: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  ),
  spinner: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="spin">
      <line x1="12" y1="2" x2="12" y2="6" />
      <line x1="12" y1="18" x2="12" y2="22" />
      <line x1="4.93" y1="4.93" x2="7.76" y2="7.76" />
      <line x1="16.24" y1="16.24" x2="19.07" y2="19.07" />
      <line x1="2" y1="12" x2="6" y2="12" />
      <line x1="18" y1="12" x2="22" y2="12" />
      <line x1="4.93" y1="19.07" x2="7.76" y2="16.24" />
      <line x1="16.24" y1="7.76" x2="19.07" y2="4.93" />
    </svg>
  )
};

export default function Quiz({
  quiz,
  workspaceName = 'General',
  onQuit,
  onFinish
}) {
  const [attempt, setAttempt] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [currentQuestionData, setCurrentQuestionData] = useState(null);
  
  const [isLoadingQuestion, setIsLoadingQuestion] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [userAnswers, setUserAnswers] = useState({});
  const [submittedAnswers, setSubmittedAnswers] = useState({});
  const [errorMsg, setErrorMsg] = useState('');

  // ── Timer ──────────────────────────────────────────────────────────────────
  const startTimeRef = useRef(Date.now());
  const questionStartTimeRef = useRef(Date.now());
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const timerRef = useRef(null);

  // Modal dialog states
  const [showQuitModal, setShowQuitModal] = useState(false);
  const [isFinished, setIsFinished] = useState(false);
  const [quizResult, setQuizResult] = useState(null);

  useEffect(() => {
    if (attempt && !isFinished) {
      startTimeRef.current = Date.now();
      const initialTime = attempt.time_spent_seconds || 0;
      setElapsedSeconds(initialTime);
      timerRef.current = setInterval(() => {
        setElapsedSeconds(initialTime + Math.floor((Date.now() - startTimeRef.current) / 1000));
      }, 1000);
    }
    return () => clearInterval(timerRef.current);
  }, [attempt, isFinished]);

  /** Format seconds → "Xm Ys" */
  function formatTime(secs) {
    if (!secs || isNaN(secs)) return '0m 00s';
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}m ${String(s).padStart(2, '0')}s`;
  }

  const totalQuestions = quiz?.actual_question_count || quiz?.total_questions || 1;
  const isFirstQuestion = currentIndex === 0;
  const isLastQuestion = currentIndex === totalQuestions - 1;

  // Initialize Attempt
  useEffect(() => {
    const startAttempt = async () => {
      try {
        const endpoint = quiz.isContinuing 
          ? `/api/quiz/${quiz.id}/resume/` 
          : `/api/quiz/${quiz.id}/start/`;
        const res = await api.post(endpoint);
        setAttempt(res.data);
      } catch (err) {
        console.error("Failed to start/resume quiz attempt", err);
        setErrorMsg("Failed to load quiz. Please try again.");
      }
    };
    if (quiz && !attempt) {
      startAttempt();
    }
  }, [quiz]);

  // Fetch Current Question
  useEffect(() => {
    const fetchQuestion = async () => {
      if (!attempt) return;
      setIsLoadingQuestion(true);
      setErrorMsg('');
      try {
        const res = await api.get(`/api/quiz/attempt/${attempt.id}/question/${currentIndex + 1}/`);
        setCurrentQuestionData(res.data);
        
        if (res.data.selected_option_id) {
          setUserAnswers(prev => ({ ...prev, [currentIndex]: res.data.selected_option_id }));
          setSubmittedAnswers(prev => ({ ...prev, [currentIndex]: true }));
        }
        
        // Reset question timer when loaded
        questionStartTimeRef.current = Date.now();
      } catch (err) {
        console.error("Failed to fetch question", err);
        setErrorMsg("Failed to load question.");
      } finally {
        setIsLoadingQuestion(false);
      }
    };
    fetchQuestion();
  }, [attempt, currentIndex]);

  // Option select handler
  const handleSelectOption = (optionId) => {
    if (submittedAnswers[currentIndex] || isSubmitting || isFinished) return; 
    setUserAnswers(prev => ({ ...prev, [currentIndex]: optionId }));
  };

  const submitAnswerIfNeeded = async () => {
    const selectedId = userAnswers[currentIndex];
    if (selectedId && !submittedAnswers[currentIndex]) {
      setIsSubmitting(true);
      const timeSpentOnQuestion = Math.floor((Date.now() - questionStartTimeRef.current) / 1000);
      try {
        await api.post(`/api/quiz/attempt/${attempt.id}/answer/`, {
          question_id: currentQuestionData.question_id,
          selected_option_id: selectedId,
          time_spent_seconds: timeSpentOnQuestion
        });
        setSubmittedAnswers(prev => ({ ...prev, [currentIndex]: true }));
        return true;
      } catch (err) {
        console.error("Failed to submit answer", err);
        if (err.response?.status === 400 && err.response.data?.detail?.includes('answered')) {
          setSubmittedAnswers(prev => ({ ...prev, [currentIndex]: true }));
          return true;
        } else {
          alert(err.response?.data?.message || err.response?.data?.detail || "Failed to submit answer.");
          return false;
        }
      } finally {
        setIsSubmitting(false);
      }
    }
    return true; // already submitted or nothing selected
  };

  // Navigation handlers
  const handlePrevious = async () => {
    if (isSubmitting) return;
    const success = await submitAnswerIfNeeded();
    if (success && !isFirstQuestion) {
      setCurrentIndex((prev) => prev - 1);
    }
  };

  const handleNext = async () => {
    if (isSubmitting) return;
    const success = await submitAnswerIfNeeded();
    if (success && !isLastQuestion) {
      setCurrentIndex((prev) => prev + 1);
    }
  };

  const handleFinishQuiz = async () => {
    if (!attempt || isSubmitting) return;
    const success = await submitAnswerIfNeeded();
    if (!success) return;

    clearInterval(timerRef.current);
    try {
      const res = await api.post(`/api/quiz/attempt/${attempt.id}/submit/`);
      setQuizResult(res.data);
      setIsFinished(true);
    } catch (err) {
      console.error("Failed to finish quiz", err);
      alert("Failed to finish quiz.");
    }
  };

  const handleConfirmQuit = async () => {
    if (attempt && !isFinished) {
      const timeSpentOnQuestion = Math.floor((Date.now() - questionStartTimeRef.current) / 1000);
      try {
        await api.post(`/api/quiz/attempt/${attempt.id}/pause/`, {
           time_spent_seconds: timeSpentOnQuestion
        });
      } catch (err) {
        console.error("Failed to pause quiz", err);
      }
    }
    setShowQuitModal(false);
    if (onQuit) onQuit();
  };

  if (errorMsg && !attempt) {
    return (
      <div className="quiz-root db-root" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="db-card" style={{ padding: '2rem', textAlign: 'center' }}>
          <h2 style={{ color: '#ef4444' }}>Error</h2>
          <p>{errorMsg}</p>
          <button className="ws-action-btn ws-btn-primary" style={{ marginTop: '1rem' }} onClick={onQuit}>Go Back</button>
        </div>
      </div>
    );
  }

  if (!attempt) {
    return (
      <div className="quiz-root db-root" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ color: '#3b82f6', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div style={{ width: '40px', height: '40px', marginBottom: '1rem' }}>{Icon.spinner}</div>
          <h3>Starting Quiz...</h3>
          <style>{`.spin { animation: spin 1s linear infinite; } @keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
        </div>
      </div>
    );
  }

  return (
    <div className="quiz-root db-root" id="quiz-page-root">
      {/* ── Top Bar: Quit | Quiz Info | Timer ── */}
      <div className="quiz-top-bar" id="quiz-top-bar">

        {/* Left: Quit */}
        <button
          className="quiz-quit-btn"
          id="quiz-quit-button"
          onClick={() => setShowQuitModal(true)}
          aria-label="Quit quiz"
        >
          <span>Quit</span>
        </button>

        {/* Centre: Workspace breadcrumb + Quiz name */}
        <div className="quiz-header-info" id="quiz-header-info">
          <span className="quiz-header-workspace" id="quiz-header-workspace">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <rect x="2" y="7" width="20" height="14" rx="2" />
              <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" />
            </svg>
            {workspaceName}
          </span>
          <p className="quiz-header-title" id="quiz-header-title">{quiz.title}</p>
        </div>

        {/* Right: Live timer */}
        <div className="quiz-header-timer" id="quiz-header-timer" aria-label="Time elapsed">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          <span id="quiz-timer-display">{formatTime(elapsedSeconds)}</span>
        </div>

      </div>

      <main className="quiz-main" id="quiz-main-container">
        
        {/* ── Main Quiz Card Container ── */}
        <div className="quiz-card db-card" id="quiz-card-container">
          
          {/* Progress Line */}
          <div className="quiz-progress-bar-track">
            <div
              className="quiz-progress-bar-fill"
              style={{ width: `${((currentIndex + 1) / totalQuestions) * 100}%`, transition: 'width 0.3s ease' }}
            />
          </div>

          {isLoadingQuestion || !currentQuestionData ? (
             <div style={{ padding: '4rem', textAlign: 'center', color: '#6b7280' }}>
               <div style={{ width: '32px', height: '32px', margin: '0 auto 1rem', color: '#3b82f6' }}>{Icon.spinner}</div>
               <p>Loading question...</p>
             </div>
          ) : (
            <>
              {/* Question Text */}
              <div className="quiz-question-box" id="quiz-question-box">
                <h2 className="quiz-question-text" id="quiz-question-text">
                  {currentQuestionData.question_text}
                </h2>
              </div>

              {/* Options List */}
              <div className="quiz-options-list" id="quiz-options-list" role="radiogroup">
                {currentQuestionData.options.map((option, optIdx) => {
                  const isSelected = userAnswers[currentIndex] === option.id;
                  const isLocked = !!submittedAnswers[currentIndex]; // Has this question been submitted?
                  const optionLetter = String.fromCharCode(65 + optIdx); // A, B, C, D

                  return (
                    <button
                      key={option.id}
                      className={`quiz-option-item ${isSelected ? 'selected' : ''} ${isLocked && !isSelected ? 'locked-unselected' : ''}`}
                      id={`quiz-option-${optIdx}`}
                      onClick={() => handleSelectOption(option.id)}
                      disabled={isLocked || isSubmitting}
                      role="radio"
                      aria-checked={isSelected}
                      style={{
                        opacity: (isLocked && !isSelected) ? 0.6 : 1,
                        cursor: (isLocked || isSubmitting) ? 'not-allowed' : 'pointer'
                      }}
                    >
                      <span className="quiz-option-badge">{optionLetter}</span>
                      <span className="quiz-option-text">{option.text}</span>
                      <span className="quiz-option-radio-dot">
                        {isSelected && <span className="quiz-radio-inner" />}
                      </span>
                    </button>
                  );
                })}
              </div>
            </>
          )}

          {/* Bottom Navigation Bar */}
          <div className="quiz-footer-nav" id="quiz-footer-nav">
            {/* Previous Button */}
            <button
              className="quiz-nav-btn quiz-btn-prev"
              id="quiz-prev-btn"
              onClick={handlePrevious}
              disabled={isFirstQuestion || isLoadingQuestion}
            >
              <span className="quiz-btn-icon">{Icon.chevronLeft}</span>
              <span>Previous</span>
            </button>

            {/* Counter (1/10) */}
            <div id="quiz-counter">
              <span className="quiz-counter-text">
                {currentIndex + 1}/{totalQuestions}
              </span>
            </div>

            {/* Next / Finish Button */}
            {isLastQuestion ? (
              <button
                className="quiz-nav-btn quiz-btn-finish"
                id="quiz-finish-btn"
                onClick={handleFinishQuiz}
                disabled={isLoadingQuestion || isSubmitting || !userAnswers[currentIndex]}
              >
                <span>Finish</span>
                <span className="quiz-btn-icon">{Icon.check}</span>
              </button>
            ) : (
              <button
                className="quiz-nav-btn quiz-btn-next"
                id="quiz-next-btn"
                onClick={handleNext}
                disabled={isLoadingQuestion || !userAnswers[currentIndex]}
              >
                <span>Next</span>
                <span className="quiz-btn-icon">{Icon.chevronRight}</span>
              </button>
            )}
          </div>

        </div>

      </main>

      {/* ── Quit Confirmation Modal ── */}
      {showQuitModal && (
        <div className="quiz-modal-overlay" id="quiz-quit-modal-overlay">
          <div className="quiz-modal-card db-card" id="quiz-quit-modal">
            <div className="quiz-modal-icon quit-icon">{Icon.alert}</div>
            <h2 className="quiz-modal-title">Quit Quiz?</h2>
            <p className="quiz-modal-text">
              Are you sure you want to quit? Your progress for this quiz attempt will be saved but the timer keeps running.
            </p>
            <div className="quiz-modal-actions">
              <button
                className="quiz-modal-btn quiz-btn-cancel"
                onClick={() => setShowQuitModal(false)}
                id="btn-cancel-quit"
              >
                Cancel
              </button>
              <button
                className="quiz-modal-btn quiz-btn-danger"
                onClick={handleConfirmQuit}
                id="btn-confirm-quit"
              >
                Confirm Quit
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Finished / Results Summary Modal ── */}
      {isFinished && quizResult && (
        <div className="quiz-modal-overlay" id="quiz-results-modal-overlay">
          <div className="quiz-modal-card db-card quiz-results-card" id="quiz-results-modal">
            <div className="quiz-modal-icon trophy-icon">{Icon.trophy}</div>
            <h2 className="quiz-modal-title">Quiz Completed!</h2>
            <p className="quiz-modal-subtitle">Great effort on completing the quiz!</p>
            
            <div className="quiz-results-stats">
              <div className="quiz-stat-box">
                <span className="quiz-stat-val">{quizResult.score}/{totalQuestions}</span>
                <span className="quiz-stat-lbl">Score</span>
              </div>
              <div className="quiz-stat-box">
                <span className="quiz-stat-val">{quizResult.percentage}%</span>
                <span className="quiz-stat-lbl">Accuracy</span>
              </div>
            </div>

            <div className="quiz-modal-actions">
              <button
                className="quiz-modal-btn quiz-btn-primary"
                onClick={() => {
                  setIsFinished(false);
                  if (onFinish) onFinish();
                }}
                id="btn-back-to-workspace"
                style={{ width: '100%' }}
              >
                Back to Workspace
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
