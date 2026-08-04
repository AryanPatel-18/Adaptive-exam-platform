import React, { useState, useEffect, useRef } from 'react';
import Navbar from '../common/Navbar';
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
  )
};

// ── 10 Dummy Questions Data ──────────────────────────────────────────────────
const DUMMY_QUESTIONS = [
  {
    id: 1,
    question: "What is the average time complexity of searching for an element in a balanced Binary Search Tree (BST)?",
    options: [
      "O(1)",
      "O(log n)",
      "O(n)",
      "O(n log n)"
    ],
    correctAnswer: 1
  },
  {
    id: 2,
    question: "Which data structure follows the First-In, First-Out (FIFO) principle?",
    options: [
      "Stack",
      "Heap",
      "Queue",
      "Tree"
    ],
    correctAnswer: 2
  },
  {
    id: 3,
    question: "In React, which hook is primarily used for handling side effects such as fetching data?",
    options: [
      "useState",
      "useMemo",
      "useEffect",
      "useCallback"
    ],
    correctAnswer: 2
  },
  {
    id: 4,
    question: "What is the HTTP status code representing 'Not Found'?",
    options: [
      "200 OK",
      "401 Unauthorized",
      "404 Not Found",
      "500 Internal Server Error"
    ],
    correctAnswer: 2
  },
  {
    id: 5,
    question: "Which sorting algorithm has a typical average-case time complexity of O(n log n)?",
    options: [
      "Bubble Sort",
      "Insertion Sort",
      "Quick Sort",
      "Selection Sort"
    ],
    correctAnswer: 2
  },
  {
    id: 6,
    question: "In JavaScript, which operator is used for strict equality comparison without type coercion?",
    options: [
      "==",
      "===",
      "=",
      "!="
    ],
    correctAnswer: 1
  },
  {
    id: 7,
    question: "What does CSS stand for in web application development?",
    options: [
      "Creative Style Sheets",
      "Computer Style Sheets",
      "Cascading Style Sheets",
      "Colorful Style Sheets"
    ],
    correctAnswer: 2
  },
  {
    id: 8,
    question: "Which of the following data structures is non-linear?",
    options: [
      "Array",
      "Linked List",
      "Tree",
      "Queue"
    ],
    correctAnswer: 2
  },
  {
    id: 9,
    question: "What is the primary purpose of creating a database index?",
    options: [
      "To reduce disk space requirements",
      "To speed up data retrieval operations",
      "To encrypt sensitive table data",
      "To enforce foreign key constraints"
    ],
    correctAnswer: 1
  },
  {
    id: 10,
    question: "Which keyword in JavaScript declares a block-scoped variable whose reference cannot be reassigned?",
    options: [
      "var",
      "let",
      "const",
      "static"
    ],
    correctAnswer: 2
  }
];

export default function Quiz({
  questions = DUMMY_QUESTIONS,
  quizName = 'Practice Quiz',
  workspaceName = 'General',
  onQuit,
  onFinish
}) {
  const [activePage, setActivePage] = useState('quiz');
  const [searchValue, setSearchValue] = useState('');

  const [currentIndex, setCurrentIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState({});

  // ── Timer ──────────────────────────────────────────────────────────────────
  const startTimeRef = useRef(Date.now());
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const timerRef = useRef(null);

  useEffect(() => {
    timerRef.current = setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - startTimeRef.current) / 1000));
    }, 1000);
    return () => clearInterval(timerRef.current);
  }, []);

  /** Format seconds → "Xm Ys" */
  function formatTime(secs) {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}m ${String(s).padStart(2, '0')}s`;
  }

  // Modal dialog states
  const [showQuitModal, setShowQuitModal] = useState(false);
  const [isFinished, setIsFinished] = useState(false);

  const totalQuestions = questions.length;
  const currentQuestion = questions[currentIndex];
  const selectedOption = userAnswers[currentIndex];

  const isFirstQuestion = currentIndex === 0;
  const isLastQuestion = currentIndex === totalQuestions - 1;

  // Option select handler
  const handleSelectOption = (optionIdx) => {
    setUserAnswers((prev) => ({
      ...prev,
      [currentIndex]: optionIdx
    }));
  };

  // Navigation handlers
  const handlePrevious = () => {
    if (!isFirstQuestion) {
      setCurrentIndex((prev) => prev - 1);
    }
  };

  const handleNext = () => {
    if (!isLastQuestion) {
      setCurrentIndex((prev) => prev + 1);
    }
  };

  const handleFinishQuiz = () => {
    clearInterval(timerRef.current);
    setIsFinished(true);
  };

  // Calculate score on finish
  const calculateScore = () => {
    let score = 0;
    questions.forEach((q, idx) => {
      if (userAnswers[idx] === q.correctAnswer) {
        score++;
      }
    });
    return score;
  };

  const score = calculateScore();
  const percentage = Math.round((score / totalQuestions) * 100);

  return (
    <div className="quiz-root db-root" id="quiz-page-root">
      {/* ── Universal Navbar ── */}
      {/* <Navbar
        activePage={activePage}
        onNavigate={setActivePage}
        notificationCount={0}
        searchValue={searchValue}
        onSearchChange={setSearchValue}
      /> */}

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
          <p className="quiz-header-title" id="quiz-header-title">{quizName}</p>
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
              style={{ width: `${((currentIndex + 1) / totalQuestions) * 100}%` }}
            />
          </div>

          {/* Question Text */}
          <div className="quiz-question-box" id="quiz-question-box">
            <h2 className="quiz-question-text" id="quiz-question-text">
              {currentQuestion.question}
            </h2>
          </div>

          {/* Options List */}
          <div className="quiz-options-list" id="quiz-options-list" role="radiogroup">
            {currentQuestion.options.map((optionText, optIdx) => {
              const isSelected = selectedOption === optIdx;
              const optionLetter = String.fromCharCode(65 + optIdx); // A, B, C, D

              return (
                <button
                  key={optIdx}
                  className={`quiz-option-item ${isSelected ? 'selected' : ''}`}
                  id={`quiz-option-${optIdx}`}
                  onClick={() => handleSelectOption(optIdx)}
                  role="radio"
                  aria-checked={isSelected}
                >
                  <span className="quiz-option-badge">{optionLetter}</span>
                  <span className="quiz-option-text">{optionText}</span>
                  <span className="quiz-option-radio-dot">
                    {isSelected && <span className="quiz-radio-inner" />}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Bottom Navigation Bar */}
          <div className="quiz-footer-nav" id="quiz-footer-nav">
            {/* Previous Button */}
            <button
              className="quiz-nav-btn quiz-btn-prev"
              id="quiz-prev-btn"
              onClick={handlePrevious}
              disabled={isFirstQuestion}
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
              >
                <span>Finish</span>
                <span className="quiz-btn-icon">{Icon.check}</span>
              </button>
            ) : (
              <button
                className="quiz-nav-btn quiz-btn-next"
                id="quiz-next-btn"
                onClick={handleNext}
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
              Are you sure you want to quit? Your progress for this quiz attempt will be lost.
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
                onClick={() => {
                  setShowQuitModal(false);
                  if (onQuit) onQuit();
                }}
                id="btn-confirm-quit"
              >
                Confirm Quit
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Finished / Results Summary Modal ── */}
      {isFinished && (
        <div className="quiz-modal-overlay" id="quiz-results-modal-overlay">
          <div className="quiz-modal-card db-card quiz-results-card" id="quiz-results-modal">
            <div className="quiz-modal-icon trophy-icon">{Icon.trophy}</div>
            <h2 className="quiz-modal-title">Quiz Completed!</h2>
            <p className="quiz-modal-subtitle">Great effort on completing the quiz!</p>
            
            <div className="quiz-results-stats">
              <div className="quiz-stat-box">
                <span className="quiz-stat-val">{score}/{totalQuestions}</span>
                <span className="quiz-stat-lbl">Score</span>
              </div>
              <div className="quiz-stat-box">
                <span className="quiz-stat-val">{percentage}%</span>
                <span className="quiz-stat-lbl">Accuracy</span>
              </div>
            </div>

            <div className="quiz-modal-actions">
              <button
                className="quiz-modal-btn quiz-btn-cancel"
                onClick={() => {
                  setUserAnswers({});
                  setCurrentIndex(0);
                  setIsFinished(false);
                }}
                id="btn-retake-quiz"
              >
                Retake Quiz
              </button>
              <button
                className="quiz-modal-btn quiz-btn-primary"
                onClick={() => {
                  setIsFinished(false);
                  const result = {
                    name: quizName,
                    workspace: workspaceName,
                    score: percentage,
                    fraction: `${score}/${totalQuestions}`,
                    questions: totalQuestions,
                    timeTaken: formatTime(elapsedSeconds),
                    date: 'Just now',
                  };
                  if (onFinish) onFinish(result);
                  else if (onQuit) onQuit();
                }}
                id="btn-back-to-workspace"
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
