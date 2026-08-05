import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api/axios';
import './CreateWorkspaceModal.css';

export default function CreateWorkspaceModal({ isOpen, onClose }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  if (!isOpen) return null;

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
      
      setTitle('');
      setDescription('');
      onClose();
      
      if (newWorkspaceId) {
        navigate(`/workspace/${newWorkspaceId}`);
      } else {
        window.location.reload(); 
      }
    } catch (err) {
      console.error('Workspace creation failed:', err);
      setError(err.response?.data?.message || 'Failed to create workspace. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ws-create-overlay" onClick={onClose}>
      <div className="ws-create-card" onClick={(e) => e.stopPropagation()}>
        <h2 className="ws-create-title">Create Workspace</h2>
        
        {error && <div className="ws-create-error">{error}</div>}

        <form onSubmit={handleSubmit} className="ws-create-form">
          <div className="ws-form-group">
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

          <div className="ws-form-group">
            <label htmlFor="ws-desc">Description (Optional)</label>
            <textarea
              id="ws-desc"
              placeholder="What is this workspace for?"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows="3"
              disabled={loading}
            />
          </div>

          <div className="ws-create-actions">
            <button
              type="button"
              className="ws-action-btn ws-btn-outline"
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="ws-action-btn ws-btn-primary"
              disabled={loading}
            >
              {loading ? 'Creating...' : 'Create Workspace'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
