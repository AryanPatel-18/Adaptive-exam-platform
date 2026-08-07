import React, { useState, useEffect } from 'react';
import Navbar from '../common/Navbar';
import api from '../../api/axios';
import { useNavigate } from 'react-router-dom';
import './UserHistory.css';

const UserHistory = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const navigate = useNavigate();

  useEffect(() => {
    fetchHistory(page);
  }, [page]);

  const fetchHistory = async (pageNum) => {
    setLoading(true);
    try {
      const response = await api.get(`/api/dashboard/history/?page=${pageNum}`);
      // Assuming DRF PageNumberPagination returns { count, next, previous, results }
      if (response.data.results) {
        setHistory(response.data.results);
        setTotalPages(Math.ceil(response.data.count / 20)); // assuming page_size=20
      } else {
        setHistory(response.data);
        setTotalPages(1);
      }
    } catch (error) {
      console.error("Failed to fetch history:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleNextPage = () => {
    if (page < totalPages) setPage(p => p + 1);
  };

  const handlePrevPage = () => {
    if (page > 1) setPage(p => p - 1);
  };

  const getIconForAction = (action) => {
    switch(action) {
      case 'LOGIN': return '🔐';
      case 'WORKSPACE_CREATED': return '📂';
      case 'QUIZ_CREATED': return '📝';
      case 'QUIZ_COMPLETED': return '🏆';
      case 'SCHEDULE_CREATED': return '📅';
      case 'SCHEDULE_VIEWED': return '👁️';
      default: return '📌';
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return new Intl.DateTimeFormat('en-US', {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: 'numeric', minute: '2-digit', hour12: true
    }).format(date);
  };

  const handleActionClick = (item) => {
    if (item.metadata?.workspace_id) {
      navigate(`/workspace/${item.metadata.workspace_id}`);
    }
  };

  const [searchQuery, setSearchQuery] = useState('');

  return (
    <div className="uh-layout">
      <Navbar 
        activePage="history" 
        searchValue={searchQuery}
        onSearchChange={setSearchQuery}
      />
      
      <div className="uh-main-container">
        <div className="uh-content">
          <div className="uh-header">
            <h1>Activity History</h1>
            <p>A timeline of all your activities on the platform.</p>
          </div>

          {loading && history.length === 0 ? (
            <div className="uh-loading-container">
              <div className="uh-spinner"></div>
            </div>
          ) : history.length === 0 ? (
            <div className="uh-empty-state">
              <span className="uh-empty-icon">📭</span>
              <h3>No history found</h3>
              <p>Your recent activities will appear here.</p>
            </div>
          ) : (
            <div className="uh-timeline-container">
              <div className="uh-timeline">
                {history.map((item, index) => (
                  <div key={item.id || index} className="uh-timeline-item">
                    <div className="uh-timeline-icon">
                      {getIconForAction(item.action)}
                    </div>
                    <div className="uh-timeline-content" onClick={() => handleActionClick(item)} style={{ cursor: item.metadata?.workspace_id ? 'pointer' : 'default' }}>
                      <div className="uh-timeline-header">
                        <span className="uh-action-badge">{item.action.replace('_', ' ')}</span>
                        <span className="uh-time">{formatTime(item.timestamp)}</span>
                      </div>
                      <p className="uh-description">{item.description}</p>
                    </div>
                  </div>
                ))}
              </div>
              
              {totalPages > 1 && (
                <div className="uh-pagination">
                  <button onClick={handlePrevPage} disabled={page === 1} className="uh-page-btn">
                    ← Previous
                  </button>
                  <span className="uh-page-info">Page {page} of {totalPages}</span>
                  <button onClick={handleNextPage} disabled={page === totalPages} className="uh-page-btn">
                    Next →
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserHistory;
