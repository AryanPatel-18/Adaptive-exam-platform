import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../common/Navbar';
import { getUserProfile, updatePassword } from '../../api/auth';
import useAuth from '../../hooks/useAuth';
import './Profile.css';

export default function Profile() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [profileData, setProfileData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await getUserProfile();
        setProfileData(response.data);
      } catch (err) {
        setError('Failed to load profile. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, []);

  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);
  const [passwordData, setPasswordData] = useState({ current_password: '', new_password: '', confirm_new_password: '' });
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');

  const handlePasswordUpdate = async (e) => {
    e.preventDefault();
    setPasswordError('');
    setPasswordSuccess('');
    
    if (passwordData.new_password !== passwordData.confirm_new_password) {
      setPasswordError('New passwords do not match.');
      return;
    }

    setPasswordLoading(true);
    try {
      await updatePassword(passwordData);
      alert('Password updated successfully!');
      setPasswordData({ current_password: '', new_password: '', confirm_new_password: '' });
      setIsPasswordModalOpen(false);
      setPasswordSuccess('');
    } catch (err) {
      let errorMessage = err.response?.data?.message || err.response?.data?.detail || 'Failed to update password.';
      if (err.response?.data?.errors) {
        const errors = err.response.data.errors;
        const firstKey = Object.keys(errors)[0];
        if (firstKey && Array.isArray(errors[firstKey])) {
          errorMessage = errors[firstKey][0];
        } else if (firstKey && typeof errors[firstKey] === 'string') {
          errorMessage = errors[firstKey];
        }
      }
      setPasswordError(errorMessage);
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="profile-page">
      <Navbar activePage="profile" onNavigate={(id) => navigate(`/${id}`)} onLogout={handleLogout} />
      <div className="profile-container">
        <div className="profile-card">
          <div className="profile-header">
            <div className="profile-avatar">
              {profileData?.username ? profileData.username.charAt(0).toUpperCase() : 'U'}
            </div>
            <h2>{profileData?.username || 'User Profile'}</h2>
            <p className="profile-email">{profileData?.email}</p>
          </div>
          
          <div className="profile-content">
            {loading ? (
              <div className="profile-loading">Loading your information...</div>
            ) : error ? (
              <div className="profile-error">{error}</div>
            ) : (
              <div className="profile-details">
                <div className="detail-group">
                  <label>Account Status</label>
                  <div className={`status-badge ${profileData?.account_status?.toLowerCase() || 'unknown'}`}>
                    {profileData?.account_status || 'Unknown'}
                  </div>
                </div>
                <div className="detail-group">
                  <label>Member Since</label>
                  <p>{profileData?.created_at ? new Date(profileData.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' }) : 'Unknown'}</p>
                </div>
                <div className="detail-group">
                  <label>User ID</label>
                  <p className="user-id">{profileData?.id}</p>
                </div>
              </div>
            )}
          </div>
          
          <div className="profile-actions">
            <button className="btn-change-password" onClick={() => setIsPasswordModalOpen(true)}>Change Password</button>
            <button className="btn-logout" onClick={handleLogout}>Log Out</button>
          </div>
        </div>
      </div>

      {isPasswordModalOpen && (
        <div className="password-modal-overlay" onClick={() => !passwordLoading && setIsPasswordModalOpen(false)}>
          <div className="password-modal-card" onClick={(e) => e.stopPropagation()}>
            <h2 className="password-modal-title">Change Password</h2>
            
            {passwordError && <div className="password-alert error">{passwordError}</div>}
            {passwordSuccess && <div className="password-alert success">{passwordSuccess}</div>}

            <form onSubmit={handlePasswordUpdate} className="password-form">
              <div className="password-form-group">
                <label>Current Password</label>
                <input 
                  type="password" 
                  required 
                  value={passwordData.current_password} 
                  onChange={(e) => setPasswordData({...passwordData, current_password: e.target.value})} 
                />
              </div>
              <div className="password-form-group">
                <label>New Password</label>
                <input 
                  type="password" 
                  required 
                  value={passwordData.new_password} 
                  onChange={(e) => setPasswordData({...passwordData, new_password: e.target.value})} 
                />
              </div>
              <div className="password-form-group">
                <label>Confirm New Password</label>
                <input 
                  type="password" 
                  required 
                  value={passwordData.confirm_new_password} 
                  onChange={(e) => setPasswordData({...passwordData, confirm_new_password: e.target.value})} 
                />
              </div>
              
              <div className="password-modal-actions">
                <button 
                  type="button" 
                  className="btn-cancel" 
                  onClick={() => setIsPasswordModalOpen(false)}
                  disabled={passwordLoading}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="btn-save" 
                  disabled={passwordLoading}
                >
                  {passwordLoading ? 'Updating...' : 'Update Password'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
