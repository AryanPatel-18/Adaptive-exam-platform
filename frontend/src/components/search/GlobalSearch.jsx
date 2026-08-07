import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import Navbar from '../common/Navbar';
import api from '../../api/axios';
import './GlobalSearch.css';

const GlobalSearch = ({ username = 'Student' }) => {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  const navigate = useNavigate();
  
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchValue, setSearchValue] = useState(query);

  useEffect(() => {
    const fetchResults = async () => {
      if (!query) return;
      
      setLoading(true);
      try {
        const response = await api.get(`/api/dashboard/search/?q=${encodeURIComponent(query)}`);
        setResults(response.data.results || []);
      } catch (error) {
        console.error("Failed to fetch search results", error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchResults();
  }, [query]);

  const handleNavigateWorkspace = (id) => {
    navigate(`/workspace/${id}`);
  };

  return (
    <div className="gs-layout">
      <Navbar 
        searchValue={searchValue}
        onSearchChange={setSearchValue}
      />
      <div className="gs-main-container">
        <div className="gs-content">
          <div className="gs-header">
            <h1>Search Results for "{query}"</h1>
            <p>Showing top matching workspaces</p>
          </div>
          
          {loading ? (
            <div className="gs-loading-container">
              <div className="gs-spinner"></div>
            </div>
          ) : results.length === 0 ? (
            <div className="gs-no-results">
              <div className="gs-empty-state">
                <span className="gs-empty-icon">🔍</span>
                <h3>No workspaces found</h3>
                <p>Try adjusting your search query.</p>
              </div>
            </div>
          ) : (
            <div className="gs-results-grid">
              {results.slice(0, 2).map((workspace, idx) => (
                <div key={workspace.workspace_id || idx} className="gs-workspace-column">
                  <div className="gs-column-header">
                    <h2>{workspace.workspace_title}</h2>
                    <button 
                      className="gs-view-btn"
                      onClick={() => handleNavigateWorkspace(workspace.workspace_id)}
                    >
                      View Workspace →
                    </button>
                  </div>
                  
                  <div className="gs-match-section">
                    <div className="gs-match-badge">Matched in: {workspace.matched_in.join(', ')}</div>
                    <ul className="gs-match-list">
                      {workspace.matched_values.map((val, vIdx) => (
                        <li key={vIdx}>
                          <HighlightedText text={val} highlight={query} />
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  <div className="gs-content-section">
                    <h3>Workspace Contents</h3>
                    
                    {workspace.content.files.length > 0 && (
                      <div className="gs-content-group">
                        <h4>Files ({workspace.content.files.length})</h4>
                        <ul>
                          {workspace.content.files.map((f, i) => <li key={i}>📄 {f}</li>)}
                        </ul>
                      </div>
                    )}
                    
                    {workspace.content.quizzes.length > 0 && (
                      <div className="gs-content-group">
                        <h4>Quizzes ({workspace.content.quizzes.length})</h4>
                        <ul>
                          {workspace.content.quizzes.map((q, i) => <li key={i}>📝 {q}</li>)}
                        </ul>
                      </div>
                    )}
                    
                    {workspace.content.topics.length > 0 && (
                      <div className="gs-content-group">
                        <h4>Topics ({workspace.content.topics.length})</h4>
                        <ul>
                          {workspace.content.topics.map((t, i) => <li key={i}>📚 {t}</li>)}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const HighlightedText = ({ text, highlight }) => {
  if (!highlight.trim()) {
    return <span>{text}</span>;
  }
  const regex = new RegExp(`(${highlight})`, "gi");
  const parts = text.split(regex);
  return (
    <span>
      {parts.filter(String).map((part, i) => {
        return regex.test(part) ? (
          <mark key={i} className="gs-highlight">{part}</mark>
        ) : (
          <span key={i}>{part}</span>
        );
      })}
    </span>
  );
};

export default GlobalSearch;
