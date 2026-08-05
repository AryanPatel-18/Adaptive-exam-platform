import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../api/axios';
import Navbar from '../common/Navbar';
import Quiz from '../quiz/Quiz';
import './Workspace.css';

// ── Helper: Format standard timestamp to relative time ("X mins ago") ──────────
function formatTimeAgo(timestamp) {
  if (!timestamp) return 'Recently';

  const date = new Date(timestamp);
  if (isNaN(date.getTime())) return String(timestamp);

  const diffInSeconds = Math.floor((Date.now() - date.getTime()) / 1000);

  if (diffInSeconds < 45) return 'Just now';

  const minutes = Math.floor(diffInSeconds / 60);
  if (minutes < 60) return `${minutes} min${minutes > 1 ? 's' : ''} ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`;

  const days = Math.floor(hours / 24);
  if (days < 30) return `${days} day${days > 1 ? 's' : ''} ago`;

  const months = Math.floor(days / 30);
  if (months < 12) return `${months} month${months > 1 ? 's' : ''} ago`;

  const years = Math.floor(days / 365);
  return `${years} year${years > 1 ? 's' : ''} ago`;
}

// ── SVG icon helpers ─────────────────────────────────────────────────────────
const Icon = {
  edit: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
    </svg>
  ),
  plus: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="12" y1="5" x2="12" y2="19" />
      <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
  ),
  play: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="5 3 19 12 5 21 5 3" />
    </svg>
  ),
  stats: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  ),
  trash: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
    </svg>
  ),
  file: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  )
};

export default function Workspace({
  workspaceName: initialWorkspaceName = 'My Workspace',
  lastEdited: initialLastEdited = null
}) {
  const { id: workspaceId } = useParams();
  const navigate = useNavigate();
  const [activePage, setActivePage] = useState('workspace');
  const [searchValue, setSearchValue] = useState('');

  // Local state for workspace metadata
  const [workspaceName, setWorkspaceName] = useState(initialWorkspaceName);
  const [lastEditedTimestamp, setLastEditedTimestamp] = useState(
    initialLastEdited || new Date().toISOString()
  );
  const [isDeleted, setIsDeleted] = useState(false);
  const [activeQuiz, setActiveQuiz] = useState(null);
  const [, setTick] = useState(0);

  // Auto-refresh relative time display every 30s
  useEffect(() => {
    const timer = setInterval(() => {
      setTick((t) => t + 1);
    }, 30000);
    return () => clearInterval(timer);
  }, []);

  // Modal states
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isCreateQuizModalOpen, setIsCreateQuizModalOpen] = useState(false);
  const [isStartQuizModalOpen, setIsStartQuizModalOpen] = useState(false);
  const [isContinueQuizModalOpen, setIsContinueQuizModalOpen] = useState(false);
  const [editNameValue, setEditNameValue] = useState(workspaceName);
  const [newQuizTitle, setNewQuizTitle] = useState('');
  const [attemptableQuizzes, setAttemptableQuizzes] = useState([]);
  const [inProgressQuizzes, setInProgressQuizzes] = useState([]);
  const [isLoadingAttemptable, setIsLoadingAttemptable] = useState(false);
  const [isLoadingInProgress, setIsLoadingInProgress] = useState(false);

  // Add Files Modal
  const [isAddFilesModalOpen, setIsAddFilesModalOpen] = useState(false);
  const [questionBankFile, setQuestionBankFile] = useState(null);
  const [notesFiles, setNotesFiles] = useState([]);
  const [uploading, setUploading] = useState(false);

  // Toasts
  const [toasts, setToasts] = useState([]);

  // Fetched Workspace Data
  const [workspaceFiles, setWorkspaceFiles] = useState({ question_bank: null, notes: [] });
  const [workspaceQuizzes, setWorkspaceQuizzes] = useState([]);
  const [workspaceSchedules, setWorkspaceSchedules] = useState([]);
  const [isProcessed, setIsProcessed] = useState(false);
  const [isLoadingFiles, setIsLoadingFiles] = useState(true);
  
  // Processing state
  const [processingProgress, setProcessingProgress] = useState(null);

  // Poll progress if it's currently processing
  useEffect(() => {
    let intervalId;

    const checkProgress = async () => {
      try {
        const res = await api.get(`/api/processing/${workspaceId}/progress/`);
        setProcessingProgress(res.data);

        if (res.data.status === 'COMPLETED' || res.data.status === 'FAILED') {
          if (intervalId) clearInterval(intervalId);
          fetchWorkspaceData(); // Refresh to update isProcessed and enable buttons
        }
      } catch (err) {
        // Ignored, maybe no job exists yet
      }
    };

    if (processingProgress?.status === 'RUNNING' || processingProgress?.status === 'PENDING') {
      intervalId = setInterval(checkProgress, 2000);
    } else {
      checkProgress(); // Check once on mount or when state changes to non-running
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [workspaceId, processingProgress?.status]);

  const hasFiles = workspaceFiles.question_bank && workspaceFiles.notes.length > 0;
  const isProcessing = processingProgress?.status === 'RUNNING' || processingProgress?.status === 'PENDING';

  const handleProcessWorkspace = async () => {
    try {
      addToast("Starting processing pipeline...", "info");
      // Set to running immediately before the API call to show the loading bar
      setProcessingProgress({ status: 'RUNNING', stage: 'INITIALIZING' }); 
      
      await api.post(`/api/processing/${workspaceId}/process/`);
      // The backend now processes this in the background, so we just wait for the interval to pick up progress
    } catch (err) {
      console.error(err);
      addToast(err.response?.data?.message || "Failed to start processing", "error");
      setProcessingProgress({ status: 'FAILED' });
    }
  };

  const handleCreateQuiz = async () => {
    try {
      addToast("Creating quiz...", "info");
      await api.post('/api/quiz/create/', {
        workspace_id: workspaceId,
        title: newQuizTitle || `Quiz - ${new Date().toLocaleString()}`,
        question_count: 50
      });
      addToast("Quiz created successfully!", "success");
      setIsCreateQuizModalOpen(false);
      fetchWorkspaceData();
    } catch (err) {
      console.error(err);
      addToast(err.response?.data?.message || "Failed to create quiz", "error");
    }
  };

  const handleStartQuizClick = async () => {
    setIsStartQuizModalOpen(true);
    setIsLoadingAttemptable(true);
    try {
      const res = await api.get(`/api/quiz/workspace/${workspaceId}/attemptable/`);
      setAttemptableQuizzes(res.data);
    } catch (err) {
      console.error(err);
      addToast("Failed to load attemptable quizzes", "error");
    } finally {
      setIsLoadingAttemptable(false);
    }
  };

  const handleContinueQuizClick = async () => {
    setIsContinueQuizModalOpen(true);
    setIsLoadingInProgress(true);
    try {
      const res = await api.get(`/api/quiz/workspace/${workspaceId}/in-progress/`);
      setInProgressQuizzes(res.data);
    } catch (err) {
      console.error(err);
      addToast("Failed to load in-progress quizzes", "error");
    } finally {
      setIsLoadingInProgress(false);
    }
  };

  // Fetch files and quizzes on mount or after successful upload
  const fetchWorkspaceData = async () => {
    try {
      setIsLoadingFiles(true);
      const [workspaceRes, filesRes, quizzesRes, statusRes, schedulesRes] = await Promise.all([
        api.get(`/api/workspace/${workspaceId}/`),
        api.get(`/api/workspace/${workspaceId}/files/`),
        api.get(`/api/workspace/${workspaceId}/quizzes/`),
        api.get(`/api/processing/${workspaceId}/status/`).catch(() => ({ data: { is_processed: false } })),
        api.get(`/api/schedule/workspace/${workspaceId}/`).catch(() => ({ data: [] }))
      ]);
      
      const wsData = workspaceRes.data.data;
      setWorkspaceName(wsData.title);
      setLastEditedTimestamp(wsData.updated_at);
      setEditNameValue(wsData.title);

      setWorkspaceFiles(filesRes.data.data);
      setWorkspaceQuizzes(quizzesRes.data.data);
      setIsProcessed(statusRes.data.is_processed);
      setWorkspaceSchedules(schedulesRes.data || []);
    } catch (err) {
      console.error("Failed to fetch workspace data", err);
      if (err.response?.status === 404) {
        addToast("Workspace not found. Redirecting to dashboard...", "error");
        setTimeout(() => navigate('/dashboard'), 2000);
      } else if (err.response?.status === 403) {
        addToast("You don't have permission to view this workspace.", "error");
        setTimeout(() => navigate('/dashboard'), 2000);
      } else {
        addToast("Failed to load workspace data.", "error");
      }
    } finally {
      setIsLoadingFiles(false);
    }
  };

  useEffect(() => {
    fetchWorkspaceData();
  }, [workspaceId]);

  const addToast = (message, type = 'info') => {
    const id = Date.now() + Math.random();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4000);
  };

  // Drag and drop states
  const [isDraggingQB, setIsDraggingQB] = useState(false);
  const [isDraggingNotes, setIsDraggingNotes] = useState(false);

  const onDragOverQB = (e) => { e.preventDefault(); setIsDraggingQB(true); };
  const onDragLeaveQB = (e) => { e.preventDefault(); setIsDraggingQB(false); };
  const onDropQB = (e) => {
    e.preventDefault();
    setIsDraggingQB(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.type === "application/pdf" || file.name.endsWith('.pdf')) {
        setQuestionBankFile(file);
      }
    }
  };

  const onDragOverNotes = (e) => { e.preventDefault(); setIsDraggingNotes(true); };
  const onDragLeaveNotes = (e) => { e.preventDefault(); setIsDraggingNotes(false); };
  const onDropNotes = (e) => {
    e.preventDefault();
    setIsDraggingNotes(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const files = Array.from(e.dataTransfer.files).filter(f => f.type === "application/pdf" || f.name.endsWith('.pdf'));
      setNotesFiles(prev => [...prev, ...files]);
    }
  };

  const handleUpload = async () => {
    if (!questionBankFile || notesFiles.length === 0) return;
    setUploading(true);
    addToast("Creating upload session...", "info");
    try {
      const payload = {
        workspace_id: workspaceId,
        files: [
          {
            filename: questionBankFile.name,
            role: "QUESTION_BANK",
            size: questionBankFile.size,
            content_type: questionBankFile.type
          },
          ...notesFiles.map(f => ({
            filename: f.name,
            role: "NOTES",
            size: f.size,
            content_type: f.type
          }))
        ]
      };
      
      const sessionResponse = await api.post('/api/files/upload-request/', payload);
      const data = sessionResponse.data?.data || sessionResponse.data;
      const uploadSessionId = data.upload_session_id;
      
      addToast("Uploading files to storage...", "info");
      
      const fileMap = { [questionBankFile.name]: questionBankFile };
      notesFiles.forEach(f => fileMap[f.name] = f);

      let allSuccess = true;
      for (const instruction of data.files) {
        const uploadResp = await fetch(instruction.upload_url, {
          method: "PUT",
          headers: { "Content-Type": instruction.content_type },
          body: fileMap[instruction.original_filename]
        });
        if (!uploadResp.ok) allSuccess = false;
      }

      if (!allSuccess) throw new Error('Some files failed to upload to storage.');

      await api.post('/api/files/upload-request/finalize/', {
        upload_session_id: uploadSessionId
      });

      setIsAddFilesModalOpen(false);
      setQuestionBankFile(null);
      setNotesFiles([]);
      addToast("Files uploaded successfully!", "success");
      fetchWorkspaceData(); // Refresh files list
    } catch (err) {
      console.error("Upload failed", err);
      addToast(err.response?.data?.message || err.message || "Upload failed.", "error");
    } finally {
      setUploading(false);
    }
  };

  if (activeQuiz) {
    return <Quiz quiz={activeQuiz} workspaceName={workspaceName} onQuit={() => setActiveQuiz(null)} onFinish={() => setActiveQuiz(null)} />;
  }

  if (isDeleted) {
    return (
      <div className="ws-root db-root" id="workspace-page-root">
        <Navbar activePage={activePage} onNavigate={setActivePage} notificationCount={0} searchValue={searchValue} onSearchChange={setSearchValue} />
        <main className="ws-deleted-main">
          <div className="db-card ws-deleted-card">
            <div className="ws-deleted-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            </div>
            <h2 className="ws-deleted-title">Workspace Deleted</h2>
            <p className="ws-deleted-text">This workspace has been successfully removed. You can now navigate back to your dashboard.</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="ws-root db-root" id="workspace-page-root">
      {/* ── Universal Navbar ── */}
      <Navbar
        activePage={activePage}
        onNavigate={setActivePage}
        notificationCount={0}
        searchValue={searchValue}
        onSearchChange={setSearchValue}
      />

      <main className="db-main ws-main" id="workspace-main-content">
        {/* ══ Centre column ══ */}
        <div className="db-col-main ws-col-main">

          {/* Workspace Header */}
          <div className="ws-header db-card" id="workspace-header-section">
            <span>
              <span className="ws-title" id="workspace-title">{workspaceName}</span>
              <span className="ws-meta" id="workspace-last-edited">(Last edited: {formatTimeAgo(lastEditedTimestamp)}) </span>
            </span>
          </div>

          {/* Processing Spinner Banner */}
          {isProcessing && (
            <div className="db-card" style={{ padding: '2rem', textAlign: 'center', marginBottom: '1.5rem', background: 'rgba(59, 130, 246, 0.05)', border: '1px solid rgba(59, 130, 246, 0.2)' }}>
              <div style={{ border: '4px solid rgba(59, 130, 246, 0.2)', borderTop: '4px solid #3b82f6', borderRadius: '50%', width: '40px', height: '40px', animation: 'spin 1s linear infinite', margin: '0 auto 1rem' }}></div>
              <h3 style={{ marginBottom: '0.5rem', color: '#3b82f6' }}>Processing Workspace...</h3>
              <p style={{ color: '#6b7280', fontSize: '0.9rem' }}>Current Stage: <span style={{ fontWeight: 600 }}>{processingProgress?.stage || 'Initializing'}</span></p>
              <style>{`
                @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
              `}</style>
            </div>
          )}

          <div className="ws-sections db-card" id="workspace-content-cards">
            {/* Quizzes Section */}
            <section className="ws-section" id="workspace-quizzes-section">
              <h2 className="ws-section-title">Quizzes</h2>
              {isLoadingFiles ? (
                <div style={{ color: '#a1a1aa' }}>Loading quizzes...</div>
              ) : (
                <div className="ws-list-container" id="workspace-quizzes-grid">
                  {workspaceQuizzes.map((quiz) => (
                    <div 
                      key={quiz.id} 
                      className="ws-list-card" 
                      style={{ borderColor: 'rgba(59, 130, 246, 0.2)', background: 'rgba(59, 130, 246, 0.02)' }} 
                      title={quiz.title}
                    >
                      <div className="ws-list-card-icon" style={{ background: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6' }}>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                      </div>
                      <div className="ws-list-card-content">
                        <div className="ws-list-card-title" style={{ color: '#3b82f6' }}>
                          {quiz.title}
                        </div>
                        <div className="ws-list-card-subtitle">
                          {quiz.total_questions} Questions
                        </div>
                      </div>
                    </div>
                  ))}

                  {/* Empty state if nothing uploaded */}
                  {workspaceQuizzes.length === 0 && (
                    <div style={{ color: '#6b7280', fontSize: '0.9rem', gridColumn: '1 / -1' }}>
                      No quizzes created yet. Click "Take quiz" to get started.
                    </div>
                  )}
                </div>
              )}
            </section>

            {/* Files Section */}
            <section className="ws-section" id="workspace-files-section">
              <h2 className="ws-section-title">Material</h2>
              {isLoadingFiles ? (
                <div style={{ color: '#a1a1aa' }}>Loading files...</div>
              ) : (
                <div className="ws-cards-grid" id="workspace-files-grid">
                  {/* Render Question Bank */}
                  {workspaceFiles.question_bank && (
                    <div className="ws-empty-square" style={{ borderColor: '#10b981', background: 'rgba(16, 185, 129, 0.03)' }} title={workspaceFiles.question_bank.original_filename}>
                      <span className="ws-empty-icon" style={{ color: '#10b981' }}>{Icon.file}</span>
                      <span style={{ position: 'absolute', bottom: '10px', fontSize: '0.75rem', color: '#10b981', fontWeight: 600 }}>Question Bank</span>
                    </div>
                  )}

                  {/* Render Notes */}
                  {workspaceFiles.notes.map((note) => (
                    <div key={note.id} className="ws-empty-square" title={note.original_filename}>
                      <span className="ws-empty-icon">{Icon.file}</span>
                      <span style={{ position: 'absolute', bottom: '10px', fontSize: '0.75rem', color: '#8b5cf6', fontWeight: 600, width: '90%', textAlign: 'center', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {note.original_filename}
                      </span>
                    </div>
                  ))}

                  {/* Empty state if nothing uploaded */}
                  {!workspaceFiles.question_bank && workspaceFiles.notes.length === 0 && (
                    <div style={{ color: '#6b7280', fontSize: '0.9rem', gridColumn: '1 / -1' }}>
                      No materials uploaded yet. Click "Add files" to get started.
                    </div>
                  )}
                </div>
              )}
            </section>

            {/* Schedules Section */}
            <section className="ws-section" id="workspace-schedules-section">
              <h2 className="ws-section-title">Schedules</h2>
              {isLoadingFiles ? (
                <div style={{ color: '#a1a1aa' }}>Loading schedules...</div>
              ) : (
                <div className="ws-list-container" id="workspace-schedules-grid">
                  {workspaceSchedules.map((schedule) => (
                    <div 
                      key={schedule.id} 
                      className="ws-list-card" 
                      style={{ borderColor: 'rgba(245, 158, 11, 0.2)', background: 'rgba(245, 158, 11, 0.02)' }} 
                      title={`Schedule generated on ${new Date(schedule.created_at).toLocaleDateString()}`} 
                      onClick={() => navigate(`/workspace/${workspaceId}/schedule/${schedule.id}`)}
                    >
                      <div className="ws-list-card-icon" style={{ background: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b' }}>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                          <line x1="16" y1="2" x2="16" y2="6" />
                          <line x1="8" y1="2" x2="8" y2="6" />
                          <line x1="3" y1="10" x2="21" y2="10" />
                        </svg>
                      </div>
                      <div className="ws-list-card-content">
                        <div className="ws-list-card-title" style={{ color: '#f59e0b' }}>
                          Study Plan
                        </div>
                        <div className="ws-list-card-subtitle">
                          Score: {schedule.preparedness_score}%
                        </div>
                      </div>
                    </div>
                  ))}

                  {/* Empty state if nothing generated */}
                  {workspaceSchedules.length === 0 && (
                    <div style={{ color: '#6b7280', fontSize: '0.9rem', gridColumn: '1 / -1' }}>
                      No schedules generated yet. Click "Create schedule" to get started.
                    </div>
                  )}
                </div>
              )}
            </section>
          </div>

        </div>

        {/* ══ Sidebar ══ */}
        <aside className="db-sidebar ws-sidebar" id="workspace-sidebar">

          {/* Actions Card */}
          <section className="db-card ws-sidebar-card ws-sidebar-single-card" id="workspace-actions-card">
            <div className="ws-sidebar-top-actions">
              <button
                className={`ws-action-btn ws-btn-primary ${!isProcessed ? 'disabled' : ''}`}
                id="btn-create-quiz"
                onClick={() => {
                  setNewQuizTitle(`Quiz - ${new Date().toLocaleString()}`);
                  setIsCreateQuizModalOpen(true);
                }}
                disabled={!isProcessed}
                title={!isProcessed ? "Workspace must be processed before creating a quiz" : ""}
                style={!isProcessed ? { opacity: 0.5, cursor: 'not-allowed' } : {}}
              >
                <span className="ws-btn-icon">{Icon.plus}</span> Create a quiz
              </button>
              
              <button
                className={`ws-action-btn ws-btn-secondary ${!isProcessed ? 'disabled' : ''}`}
                id="btn-start-quiz"
                onClick={handleStartQuizClick}
                disabled={!isProcessed}
                title={!isProcessed ? "Workspace must be processed before starting a quiz" : ""}
                style={!isProcessed ? { opacity: 0.5, cursor: 'not-allowed' } : {}}
              >
                <span className="ws-btn-icon">{Icon.play}</span> Start quiz
              </button>
              
              <button
                className={`ws-action-btn ws-btn-secondary ${!isProcessed ? 'disabled' : ''}`}
                id="btn-continue-quiz"
                onClick={handleContinueQuizClick}
                disabled={!isProcessed}
                title={!isProcessed ? "Workspace must be processed before continuing a quiz" : ""}
                style={!isProcessed ? { opacity: 0.5, cursor: 'not-allowed' } : {}}
              >
                <span className="ws-btn-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polygon points="13 19 22 12 13 5 13 19" />
                    <polygon points="2 19 11 12 2 5 2 19" />
                  </svg>
                </span> Continue quiz
              </button>
              <button
                className={`ws-action-btn ws-btn-secondary ${hasFiles ? 'disabled' : ''}`}
                id="btn-add-files"
                onClick={() => setIsAddFilesModalOpen(true)}
                disabled={hasFiles}
                style={hasFiles ? { opacity: 0.5, cursor: 'not-allowed' } : {}}
              >
                <span className="ws-btn-icon">{Icon.plus}</span> {hasFiles ? 'Files Uploaded' : 'Add files'}
              </button>

              <button
                className={`ws-action-btn ws-btn-secondary ${!isProcessed ? 'disabled' : ''}`}
                id="btn-create-schedule"
                onClick={() => navigate(`/workspace/${workspaceId}/schedule/create`)}
                disabled={!isProcessed}
                title={!isProcessed ? "Workspace must be processed before creating a schedule" : ""}
                style={!isProcessed ? { opacity: 0.5, cursor: 'not-allowed' } : {}}
              >
                <span className="ws-btn-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                    <line x1="16" y1="2" x2="16" y2="6" />
                    <line x1="8" y1="2" x2="8" y2="6" />
                    <line x1="3" y1="10" x2="21" y2="10" />
                  </svg>
                </span> Create schedule
              </button>

              <button className="ws-action-btn ws-btn-secondary" id="btn-quiz-stats">
                <span className="ws-btn-icon">{Icon.stats}</span> Quiz stats for WS
              </button>
            </div>

            <div className="ws-sidebar-bottom-actions">
              <button
                className={`ws-action-btn ws-btn-primary ${!hasFiles || isProcessing ? 'disabled' : ''}`}
                id="btn-process-workspace"
                onClick={handleProcessWorkspace}
                disabled={!hasFiles || isProcessing}
                style={(!hasFiles || isProcessing) ? { opacity: 0.5, cursor: 'not-allowed', width: '100%', marginBottom: '1rem' } : { width: '100%', marginBottom: '1rem' }}
              >
                <span className="ws-btn-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: '18px', height: '18px' }}><polygon points="5 3 19 12 5 21 5 3" /></svg>
                </span>
                {isProcessing ? 'Processing...' : 'Process Workspace'}
              </button>
              
              <button
                className="ws-action-btn ws-btn-outline"
                id="btn-edit-workspace-name"
                onClick={() => { setEditNameValue(workspaceName); setIsEditModalOpen(true); }}
              >
                <span className="ws-btn-icon">{Icon.edit}</span> Edit name
              </button>
              <button
                className="ws-action-btn ws-btn-danger"
                id="btn-delete-workspace"
                onClick={() => setIsDeleteModalOpen(true)}
              >
                <span className="ws-btn-icon">{Icon.trash}</span> Delete workspace
              </button>
            </div>
          </section>

        </aside>
      </main>


      {/* ── Modals ── */}
      {isAddFilesModalOpen && (
        <div
          className="ws-modal-overlay"
          onClick={() => !uploading && setIsAddFilesModalOpen(false)}
        >
          <div
            className="ws-modal-card db-card ws-upload-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="ws-modal-title">Upload Materials</h2>
            <p className="ws-modal-subtitle">Drag and drop your PDFs below</p>
            
            <div className="ws-upload-sections">
              
              {/* Question Bank Zone */}
              <div className="ws-upload-section">
                <div className="ws-upload-section-header">
                  <h3>Question Bank</h3>
                  <span className="ws-badge">Single PDF</span>
                </div>
                
                {questionBankFile ? (
                  <div className="ws-file-chip">
                    <span className="ws-file-icon">{Icon.file}</span>
                    <span className="ws-file-name" title={questionBankFile.name}>{questionBankFile.name}</span>
                    <button className="ws-file-remove" onClick={() => setQuestionBankFile(null)}>✕</button>
                  </div>
                ) : (
                  <label 
                    className={`ws-dropzone ${isDraggingQB ? 'drag-active' : ''}`}
                    onDragOver={onDragOverQB}
                    onDragLeave={onDragLeaveQB}
                    onDrop={onDropQB}
                  >
                    <input type="file" accept=".pdf" disabled={uploading} hidden onChange={(e) => setQuestionBankFile(e.target.files[0] || null)} />
                    <div className="ws-dropzone-content">
                      <span className="ws-dropzone-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                      </span>
                      <p className="ws-dropzone-text">Click to browse or drag file here</p>
                    </div>
                  </label>
                )}
              </div>

              {/* Notes Zone */}
              <div className="ws-upload-section">
                <div className="ws-upload-section-header">
                  <h3>Study Notes</h3>
                  <span className="ws-badge">Multiple PDFs</span>
                </div>
                
                <label 
                  className={`ws-dropzone ${isDraggingNotes ? 'drag-active' : ''}`}
                  onDragOver={onDragOverNotes}
                  onDragLeave={onDragLeaveNotes}
                  onDrop={onDropNotes}
                >
                  <input type="file" accept=".pdf" multiple disabled={uploading} hidden onChange={(e) => setNotesFiles(prev => [...prev, ...Array.from(e.target.files)])} />
                  <div className="ws-dropzone-content">
                    <span className="ws-dropzone-icon">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                    </span>
                    <p className="ws-dropzone-text">Click to browse or drag files here</p>
                  </div>
                </label>
                
                {notesFiles.length > 0 && (
                  <div className="ws-file-list">
                    {notesFiles.map((f, i) => (
                      <div key={i} className="ws-file-chip">
                        <span className="ws-file-icon">{Icon.file}</span>
                        <span className="ws-file-name" title={f.name}>{f.name}</span>
                        <button className="ws-file-remove" onClick={() => setNotesFiles(prev => prev.filter((_, idx) => idx !== i))}>✕</button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

            </div>

            <div className="ws-modal-actions">
              <button
                className="ws-action-btn ws-btn-outline"
                onClick={() => setIsAddFilesModalOpen(false)}
                disabled={uploading}
              >
                Cancel
              </button>
              <button
                className="ws-action-btn ws-btn-primary"
                onClick={handleUpload}
                disabled={uploading || !questionBankFile || notesFiles.length === 0}
              >
                {uploading ? 'Uploading...' : 'Upload Files'}
              </button>
            </div>
          </div>
        </div>
      )}
      {isEditModalOpen && (
        <div className="ws-modal-overlay" id="edit-workspace-modal-overlay">
          <div className="ws-modal-card db-card" id="edit-workspace-modal">
            <h2 className="ws-modal-title">Edit Workspace Name</h2>
            <input
              type="text"
              className="ws-modal-input"
              value={editNameValue}
              onChange={(e) => setEditNameValue(e.target.value)}
              id="edit-workspace-name-input"
            />
            <div className="ws-modal-actions">
              <button
                className="ws-action-btn ws-btn-outline"
                onClick={() => setIsEditModalOpen(false)}
                id="btn-cancel-edit"
              >Cancel</button>
              <button
                className="ws-action-btn ws-btn-primary"
                onClick={async () => {
                  try {
                    await api.patch(`/api/workspace/${workspaceId}/`, {
                      title: editNameValue
                    });
                    setWorkspaceName(editNameValue);
                    setLastEditedTimestamp(new Date().toISOString());
                    setIsEditModalOpen(false);
                    addToast("Workspace renamed successfully!", "success");
                  } catch (err) {
                    console.error(err);
                    addToast("Failed to rename workspace", "error");
                  }
                }}
                id="btn-save-edit"
                disabled={!editNameValue.trim()}
              >Save</button>
            </div>
          </div>
        </div>
      )}

      {isDeleteModalOpen && (
        <div className="ws-modal-overlay" id="delete-workspace-modal-overlay">
          <div className="ws-modal-card db-card" id="delete-workspace-modal">
            <h2 className="ws-modal-title">Delete Workspace</h2>
            <p className="ws-modal-text">Are you sure you want to delete this workspace? This action cannot be undone.</p>
            <div className="ws-modal-actions">
              <button
                className="ws-action-btn ws-btn-outline"
                onClick={() => setIsDeleteModalOpen(false)}
                id="btn-cancel-delete"
              >Cancel</button>
              <button
                className="ws-action-btn ws-btn-danger"
                onClick={async () => {
                  try {
                    await api.delete(`/api/workspace/${workspaceId}/delete/`);
                    setIsDeleted(true);
                    setIsDeleteModalOpen(false);
                  } catch (err) {
                    console.error(err);
                    addToast("Failed to delete workspace", "error");
                  }
                }}
                id="btn-confirm-delete"
              >Delete</button>
            </div>
          </div>
        </div>
      )}

      {isCreateQuizModalOpen && (
        <div className="ws-modal-overlay" id="create-quiz-modal-overlay">
          <div className="ws-modal-card db-card" id="create-quiz-modal">
            <h2 className="ws-modal-title">Create New Quiz</h2>
            <p className="ws-modal-text">Enter a title for your new quiz.</p>
            <input
              type="text"
              className="ws-modal-input"
              value={newQuizTitle}
              onChange={(e) => setNewQuizTitle(e.target.value)}
              placeholder="e.g. Midterm Practice"
              autoFocus
              style={{ marginTop: '1rem', marginBottom: '1.5rem', width: '100%', padding: '0.75rem', borderRadius: '6px', border: '1px solid #e5e7eb' }}
            />
            <div className="ws-modal-actions">
              <button
                className="ws-action-btn ws-btn-outline"
                onClick={() => setIsCreateQuizModalOpen(false)}
              >Cancel</button>
              <button
                className="ws-action-btn ws-btn-primary"
                onClick={handleCreateQuiz}
                disabled={!newQuizTitle.trim()}
              >Create</button>
            </div>
          </div>
        </div>
      )}

      {isStartQuizModalOpen && (
        <div className="ws-modal-overlay" id="start-quiz-modal-overlay">
          <div className="ws-modal-card db-card" id="start-quiz-modal" style={{ maxWidth: '500px' }}>
            <h2 className="ws-modal-title">Select a Quiz to Start</h2>
            
            {isLoadingAttemptable ? (
              <div style={{ textAlign: 'center', padding: '2rem', color: '#6b7280' }}>Loading quizzes...</div>
            ) : attemptableQuizzes.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '2rem', color: '#6b7280' }}>
                <p>No attemptable quizzes found.</p>
                <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>Quizzes may be unavailable if their source material was re-processed.</p>
              </div>
            ) : (
              <div style={{ maxHeight: '300px', overflowY: 'auto', marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {attemptableQuizzes.map(quiz => (
                  <div key={quiz.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem', border: '1px solid #e5e7eb', borderRadius: '6px', background: 'rgba(59, 130, 246, 0.02)' }}>
                    <div>
                      <h4 style={{ margin: 0, color: '#3b82f6', fontSize: '1rem' }}>{quiz.title}</h4>
                      <p style={{ margin: 0, fontSize: '0.75rem', color: '#6b7280', marginTop: '0.25rem' }}>
                        {quiz.actual_question_count} questions
                      </p>
                    </div>
                    <button
                      className="ws-action-btn ws-btn-primary"
                      style={{ padding: '0.5rem 1rem', fontSize: '0.875rem', width: 'auto' }}
                      onClick={() => {
                        setIsStartQuizModalOpen(false);
                        setActiveQuiz(quiz);
                      }}
                    >
                      Start
                    </button>
                  </div>
                ))}
              </div>
            )}
            
            <div className="ws-modal-actions" style={{ marginTop: '1.5rem' }}>
              <button
                className="ws-action-btn ws-btn-outline"
                onClick={() => setIsStartQuizModalOpen(false)}
              >Close</button>
            </div>
          </div>
        </div>
      )}

      {isContinueQuizModalOpen && (
        <div className="ws-modal-overlay" id="continue-quiz-modal-overlay">
          <div className="ws-modal-card db-card" id="continue-quiz-modal" style={{ maxWidth: '500px' }}>
            <h2 className="ws-modal-title">Select a Quiz to Continue</h2>
            
            {isLoadingInProgress ? (
              <div style={{ textAlign: 'center', padding: '2rem', color: '#6b7280' }}>Loading quizzes...</div>
            ) : inProgressQuizzes.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '2rem', color: '#6b7280' }}>
                <p>No in-progress quizzes found.</p>
                <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>You haven't paused any quizzes yet.</p>
              </div>
            ) : (
              <div style={{ maxHeight: '300px', overflowY: 'auto', marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {inProgressQuizzes.map(quiz => (
                  <div key={quiz.attempt_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem', border: '1px solid #e5e7eb', borderRadius: '6px', background: 'rgba(59, 130, 246, 0.02)' }}>
                    <div>
                      <h4 style={{ margin: 0, color: '#3b82f6', fontSize: '1rem' }}>{quiz.title}</h4>
                      <p style={{ margin: 0, fontSize: '0.75rem', color: '#6b7280', marginTop: '0.25rem' }}>
                        Attempt {quiz.attempt_number} • Started {formatTimeAgo(quiz.started_at)}
                      </p>
                    </div>
                    <button
                      className="ws-action-btn ws-btn-primary"
                      style={{ padding: '0.5rem 1rem', fontSize: '0.875rem', width: 'auto' }}
                      onClick={() => {
                        setIsContinueQuizModalOpen(false);
                        setActiveQuiz({ ...quiz, isContinuing: true });
                      }}
                    >
                      Continue
                    </button>
                  </div>
                ))}
              </div>
            )}
            
            <div className="ws-modal-actions" style={{ marginTop: '1.5rem' }}>
              <button
                className="ws-action-btn ws-btn-outline"
                onClick={() => setIsContinueQuizModalOpen(false)}
              >Close</button>
            </div>
          </div>
        </div>
      )}

      {/* ── Toasts ── */}
      <div className="ws-toast-container">
        {toasts.map(toast => (
          <div key={toast.id} className={`ws-toast ws-toast-${toast.type}`}>
            {toast.type === 'success' && <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></svg>}
            {toast.type === 'error' && <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" /></svg>}
            {toast.type === 'info' && <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><line x1="12" y1="16" x2="12" y2="12" /><line x1="12" y1="8" x2="12.01" y2="8" /></svg>}
            <span>{toast.message}</span>
          </div>
        ))}
      </div>

    </div>
  );
}
