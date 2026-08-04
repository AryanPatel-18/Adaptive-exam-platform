import React, { useState } from 'react';
import './Navbar.css';
import { SearchIcon, BellIcon, PlusIcon, UserIcon, ChevronDownIcon, UploadIcon } from './svg';

// ── Nav link definitions ──────────────────────────────────────────────────────
const NAV_LINKS = [
  { id: "home", label: "Home" },

  { id: "history", label: "History" },

  {
    id: "workspaces",
    label: "Workspaces",
    hasDropdown: true,
    dropdown: [
      { id: "create", label: "Create Workspace" },
      { id: "all", label: "View All Workspaces" },
      { id: "recent", label: "Recent Workspaces" },
      { id: "favorites", label: "Favorites" },
      { id: "archived", label: "Archived" },
    ],
  },
];

/**
 * Navbar – universal top navigation bar.
 *
 * Props:
 *  - activePage {string}       – which nav link is active (matches NAV_LINKS id)
 *  - onNavigate {fn(id)}       – called when a nav link is clicked
 *  - onCreateWorkspace {fn}    – called when "+ Create Workspace" is clicked
 *  - onNotifications {fn}      – called when bell is clicked
 *  - onProfile {fn}            – called when avatar is clicked
 *  - notificationCount {number}– badge count; hide badge when 0
 *  - searchValue {string}      – controlled search input value
 *  - onSearchChange {fn(val)}  – called on search input change
 */
export default function Navbar({
  activePage = 'dashboard',
  onNavigate = () => { },
  onCreateWorkspace = () => { },
  onNotifications = () => { },
  onProfile = () => { },
  notificationCount = 0,
  searchValue = '',
  onSearchChange = () => { },
}) {
  // Create Workspace Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [workspaceName, setWorkspaceName] = useState("");
  const [workspaceFiles, setWorkspaceFiles] = useState([]);
  return (
    <header className="nav-root ">
      {/* Left – nav links */}
      <nav className="nav-links " aria-label="Main navigation">
        {NAV_LINKS.map(({ id, label, hasDropdown, dropdown }) => (
          <div className="nav-dropdown" key={id}>
            <button
              id={`nav-link-${id}`}
              className={`nav-link-btn ${activePage === id ? "active" : ""}`}
              onClick={() => onNavigate(id)}
            >
              {label}

              {hasDropdown && (
                <span className="nav-link-chevron">
                  <ChevronDownIcon />
                </span>
              )}
            </button>

            {hasDropdown && (
              <div className="dropdown-menu">
                {dropdown.map(item => (
                  <>
                    <button
                      key={item.id}
                      className="dropdown-item"
                      onClick={() => console.log(item.id)}
                    >
                      {item.label}
                    </button>
                    <hr className="dropdown-divider" /></>
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>

      {/* Centre – search */}
      <div className="nav-search" role="search">
        <span className='space'></span>
        <span className="nav-search-icon"><SearchIcon /></span>
        <input
          id="nav-search-input"
          type="search"
          placeholder="Search workspaces…"
          value={searchValue}
          onChange={e => onSearchChange(e.target.value)}
          aria-label="Search workspaces"
        />
      </div>

      {/* Right – actions */}
      <div className="nav-actions">
        <span className='space'>  </span>
        <button
          id="nav-create-workspace-btn"
          className="nav-create-btn"
          onClick={() => setShowCreateModal(true)}
        >
          <span className="nav-create-icon"><PlusIcon /></span>
          Create Workspace
        </button>

        <span className='space'></span>
        <button
          id="nav-notifications-btn"
          className="nav-icon-btn"
          aria-label={`Notifications${notificationCount > 0 ? `, ${notificationCount} unread` : ''}`}
          onClick={onNotifications}
        >
          <BellIcon />
          {notificationCount > 0 && (
            <span className="nav-badge" aria-hidden="true">{notificationCount}</span>
          )}
        </button>

        <span className='space'></span>
        <button
          id="nav-profile-btn"
          className="nav-avatar-btn"
          aria-label="Profile"
          onClick={onProfile}
        >
          <UserIcon />
        </button>
      </div>
      {showCreateModal && (
        <div
          className="ws-modal-overlay"
          onClick={() => setShowCreateModal(false)}
        >
          <div
            className="ws-modal-card db-card ws-upload-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="ws-modal-title">
              Create Workspace
            </h2>

            <input
              className="ws-modal-input"
              placeholder="Workspace Name"
              value={workspaceName}
              onChange={(e) => setWorkspaceName(e.target.value)}
            />

            <div className="ws-cards-grid ws-upload-grid">

              <label className="ws-upload-box">

                <input
                  hidden
                  multiple
                  type="file"
                  onChange={(e) =>
                    setWorkspaceFiles(prev => [
                      ...prev,
                      ...Array.from(e.target.files)
                    ])
                  }
                />

                <UploadIcon />

                <span>Click to upload files</span>

              </label>
              <div className="ws-selected-files">

                {workspaceFiles.map((file, index) => (

                  <div
                    key={index}
                    className="ws-selected-file"
                  >

                    <UploadIcon />

                    <span>{file.name}</span>

                    <button
                      onClick={() =>
                        setWorkspaceFiles(prev =>
                          prev.filter((_, i) => i !== index)
                        )
                      }>
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            </div>

            <div className="ws-modal-actions">

              <button
                className="ws-action-btn ws-btn-outline"
                onClick={() => setShowCreateModal(false)}
              >
                Cancel
              </button>

              <button
                className="ws-action-btn ws-btn-primary"
                onClick={() => {
                  console.log({
                    workspace: workspaceName,
                    files: workspaceFiles
                  });

                  // TODO:
                  // Create workspace
                  // Redirect to workspace page

                  setWorkspaceName("");
                  setWorkspaceFiles([]);
                  setShowCreateModal(false);
                }}
              >
                Create Workspace
              </button>

            </div>

          </div>
        </div>
      )}
    </header>
  );
}
