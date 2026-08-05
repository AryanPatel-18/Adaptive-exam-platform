import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api/axios';
import Navbar from '../common/Navbar';
import './CreateWorkspace.css';

export default function CreateWorkspace() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim()) {
      setError('Workspace title is required.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await api.post('/api/workspace/create/', {
        title: title.trim(),
        description: description.trim(),
      });
      
      const newWorkspaceId = response.data?.data?.id;
      
      if (newWorkspaceId) {
        navigate(`/workspace/${newWorkspaceId}`);
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      console.error('Workspace creation failed:', err);
      setError(err.response?.data?.message || 'Failed to create workspace. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="cw-page-root">
      <main className="cw-main">
        <div className="cw-container">
          <h1 className="cw-title">Create a New Workspace</h1>
          <p className="cw-subtitle">Set up a dedicated space for your study materials and quizzes.</p>
          
          {error && <div className="cw-error">{error}</div>}

          <form onSubmit={handleSubmit} className="cw-form">
            <div className="cw-form-group">
              <label htmlFor="ws-title">Workspace Name</label>
              <input
                id="ws-title"
                type="text"
                placeholder="e.g. Biology 101"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                autoFocus
                disabled={loading}
              />
            </div>

            <div className="cw-form-group">
              <label htmlFor="ws-desc">Description (Optional)</label>
              <textarea
                id="ws-desc"
                placeholder="What is this workspace for?"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows="4"
                disabled={loading}
              />
            </div>

            <div className="cw-actions">
              <button
                type="button"
                className="cw-btn-outline"
                onClick={() => navigate(-1)}
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="cw-btn-primary"
                disabled={loading}
              >
                {loading ? 'Creating...' : 'Create Workspace'}
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}
