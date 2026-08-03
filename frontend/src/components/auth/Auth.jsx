import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuth from '../../hooks/useAuth';
import './Auth.css';

export default function Auth() {
  const navigate = useNavigate();
  const { login, register } = useAuth();
  
  const [isSignUp, setIsSignUp] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    rememberMe: false
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [successState, setSuccessState] = useState(null); // 'login' | 'signup' | null
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    // Clear errors for that field
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
    if (errors.form) {
      setErrors((prev) => ({ ...prev, form: '' }));
    }
  };

  const validate = () => {
    const newErrors = {};
    if (isSignUp) {
      if (!formData.username.trim()) {
        newErrors.username = 'Username is required';
      } else if (formData.username.trim().length < 3) {
        newErrors.username = 'Username must be at least 3 characters';
      }
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email or Username is required';
    } else if (isSignUp || formData.email.includes('@')) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(formData.email)) {
        newErrors.email = 'Please enter a valid email address';
      }
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    if (isSignUp) {
      if (!formData.confirmPassword) {
        newErrors.confirmPassword = 'Please confirm your password';
      } else if (formData.password !== formData.confirmPassword) {
        newErrors.confirmPassword = 'Passwords do not match';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setIsLoading(true);
    try {
      if (isSignUp) {
        // Register API expects: username, email, password, confirm_password
        await register({
          username: formData.username,
          email: formData.email,
          password: formData.password,
          confirm_password: formData.confirmPassword
        });
        setSuccessState('signup');
      } else {
        // Login API expects: username, password (the form reuses 'email' field for username input)
        await login({
          username: formData.email,
          password: formData.password,
        });
        setSuccessState('login');
      }
    } catch (err) {
      // Handle Django Rest Framework 400 Validation Errors
      // The backend's custom exception handler returns: 
      // { success: false, message: "...", code: "...", errors: { field: ["error"] } }
      if (err.response && err.response.data) {
        const data = err.response.data;
        
        if (data.errors && typeof data.errors === 'object' && Object.keys(data.errors).length > 0) {
          // Map backend field errors to frontend state
          const backendErrors = {};
          Object.keys(data.errors).forEach(key => {
            const errorText = Array.isArray(data.errors[key]) ? data.errors[key][0] : data.errors[key];
            if (key === 'non_field_errors') backendErrors.form = errorText;
            else if (key === 'confirm_password') backendErrors.confirmPassword = errorText;
            else backendErrors[key] = errorText;
          });
          setErrors(backendErrors);
        } else if (data.message || data.detail) {
          setErrors({ form: data.message || data.detail });
        } else {
          setErrors({ form: 'Authentication failed. Please check your network and try again.' });
        }
      } else {
        setErrors({ form: 'Authentication failed. Please check your network and try again.' });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleMode = (signUpMode) => {
    setIsSignUp(signUpMode);
    setErrors({});
    setFormData({
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
      rememberMe: false
    });
  };

  const handleProceed = () => {
    if (successState === 'login') {
      navigate('/dashboard');
    } else if (successState === 'signup') {
      // Registration successful, but requires login to get tokens. 
      // Switch to sign in mode automatically so they can log in.
      setSuccessState(null);
      setIsSignUp(false);
      setFormData(prev => ({ ...prev, password: '', confirmPassword: '' }));
    }
  };

  // SVG icons
  const UserIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
  );
  const MailIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
  );
  const LockIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
  );
  const EyeIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
  );
  const EyeOffIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.52 13.52 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><line x1="2" x2="22" y1="2" y2="22"/></svg>
  );

  return (
    <div className="auth-page">
      <div className="auth-wrapper">
        {/* AUTHENTICATION FORMS OR SUCCESS SPLASH SCREEN */}
        <div className="auth-form-container">
          {successState ? (
            <div className="auth-success-screen">
              <div className="auth-success-circle">✓</div>
              <h2 className="auth-success-title">
                {successState === 'signup' ? 'Account Created!' : 'Welcome Back!'}
              </h2>
              <p className="auth-success-text">
                {successState === 'signup'
                  ? `Hey ${formData.username || 'there'}, your account has been successfully set up. Get ready to tackle your study goals!`
                  : `Good to see you again, ${formData.email.split('@')[0] || 'there'}! Prepare to dive into your interactive studies.`
                }
              </p>
              <button className="auth-success-btn" onClick={handleProceed}>
                Proceed to Dashboard
              </button>
            </div>
          ) : (
            <>
              {/* Tab: Sign In / Create Account */}
              <div className="auth-tab-bar">
                <button
                  className={`auth-tab-button ${!isSignUp ? 'active' : ''}`}
                  onClick={() => handleToggleMode(false)}
                >
                  Sign In
                </button>
                <button
                  className={`auth-tab-button ${isSignUp ? 'active' : ''}`}
                  onClick={() => handleToggleMode(true)}
                >
                  Create Account
                </button>
              </div>

              <div className="auth-form-header" key={isSignUp ? 'signup' : 'login'}>
                <h1 className="auth-form-title">
                  {isSignUp ? 'Create Account' : 'Welcome Back'}
                </h1>
                <p className="auth-form-subtitle">
                  {isSignUp
                    ? 'Fill in your details to start preparing for exams'
                    : 'Access your spaces, streaks, and practice quizzes'
                  }
                </p>
              </div>

              {Object.keys(errors).length > 0 && !isSignUp && (
                <div className="auth-alert auth-alert-error">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>
                  <span>Please check your entry and try again.</span>
                </div>
              )}

              <form className="auth-form" onSubmit={handleSubmit} noValidate>
                {/* Username (sign up only) */}
                <div className={`auth-field-transition ${isSignUp ? 'expanded' : 'collapsed'}`}>
                  <div className="auth-input-group">
                    <label className="auth-input-label" htmlFor="username">Username</label>
                    <div className="auth-input-wrapper">
                      <span className="auth-input-icon"><UserIcon /></span>
                      <input
                        type="text" name="username" id="username"
                        placeholder="e.g. aryan_patel"
                        className="auth-input"
                        value={formData.username}
                        onChange={handleInputChange}
                        tabIndex={isSignUp ? 0 : -1}
                      />
                    </div>
                    {errors.username && <span className="auth-alert-error" style={{ fontSize: '11px', marginTop: '2px', padding: '2px 8px', borderRadius: '4px' }}>{errors.username}</span>}
                  </div>
                </div>

                {/* Email */}
                <div className="auth-input-group">
                  <label className="auth-input-label" htmlFor="email">
                    {isSignUp ? 'Email Address' : 'Email or Username'}
                  </label>
                  <div className="auth-input-wrapper">
                    <span className="auth-input-icon"><MailIcon /></span>
                    <input
                      type="email" name="email" id="email"
                      placeholder={isSignUp ? 'username@example.com' : 'Enter email or username'}
                      className="auth-input"
                      value={formData.email}
                      onChange={handleInputChange}
                    />
                  </div>
                  {errors.email && <span className="auth-alert-error" style={{ fontSize: '11px', marginTop: '2px', padding: '2px 8px', borderRadius: '4px' }}>{errors.email}</span>}
                </div>

                {/* Password */}
                <div className="auth-input-group">
                  <label className="auth-input-label" htmlFor="password">
                    {isSignUp ? 'Create Password' : 'Password'}
                  </label>
                  <div className="auth-input-wrapper">
                    <span className="auth-input-icon"><LockIcon /></span>
                    <input
                      type={showPassword ? 'text' : 'password'}
                      name="password" id="password"
                      placeholder="••••••••"
                      className="auth-input auth-input-password-padding"
                      value={formData.password}
                      onChange={handleInputChange}
                    />
                    <button type="button" className="auth-password-toggle" onClick={() => setShowPassword(!showPassword)}>
                      {showPassword ? <EyeOffIcon /> : <EyeIcon />}
                    </button>
                  </div>
                  {errors.password && <span className="auth-alert-error" style={{ fontSize: '11px', marginTop: '2px', padding: '2px 8px', borderRadius: '4px' }}>{errors.password}</span>}
                </div>

                {/* Confirm Password (sign up only) */}
                <div className={`auth-field-transition ${isSignUp ? 'expanded' : 'collapsed'}`}>
                  <div className="auth-input-group">
                    <label className="auth-input-label" htmlFor="confirmPassword">Confirm Password</label>
                    <div className="auth-input-wrapper">
                      <span className="auth-input-icon"><LockIcon /></span>
                      <input
                        type={showConfirmPassword ? 'text' : 'password'}
                        name="confirmPassword" id="confirmPassword"
                        placeholder="••••••••"
                        className="auth-input auth-input-password-padding"
                        value={formData.confirmPassword}
                        onChange={handleInputChange}
                        tabIndex={isSignUp ? 0 : -1}
                      />
                      <button type="button" className="auth-password-toggle" onClick={() => setShowConfirmPassword(!showConfirmPassword)} tabIndex={isSignUp ? 0 : -1}>
                        {showConfirmPassword ? <EyeOffIcon /> : <EyeIcon />}
                      </button>
                    </div>
                    {errors.confirmPassword && <span className="auth-alert-error" style={{ fontSize: '11px', marginTop: '2px', padding: '2px 8px', borderRadius: '4px' }}>{errors.confirmPassword}</span>}
                  </div>
                </div>

                {/* Remember me / Forgot Password (login only) */}
                <div className={`auth-field-transition ${!isSignUp ? 'expanded' : 'collapsed'}`}>
                  <div className="auth-extra-options">
                    <label className="auth-remember-me">
                      <input
                        type="checkbox" name="rememberMe"
                        className="auth-checkbox"
                        checked={formData.rememberMe}
                        onChange={handleInputChange}
                        tabIndex={!isSignUp ? 0 : -1}
                      />
                      Remember me
                    </label>
                    <a href="#forgot" className="auth-forgot-link" onClick={(e) => e.preventDefault()} tabIndex={!isSignUp ? 0 : -1}>
                      Forgot Password?
                    </a>
                  </div>
                </div>

                <button type="submit" className="auth-submit-btn" disabled={isLoading} key={isSignUp ? 'signup-btn' : 'login-btn'}>
                  {isLoading ? <span className="auth-btn-spinner"/> : <span>{isSignUp ? 'Create Account' : 'Sign In'}</span>}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
