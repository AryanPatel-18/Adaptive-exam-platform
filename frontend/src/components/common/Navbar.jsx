import React, { useState } from 'react';
import './Navbar.css';

// ── SVG icons ─────────────────────────────────────────────────────────────────
const SearchIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
  </svg>
);
const BellIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 0 1-3.46 0" />
  </svg>
);
const PlusIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
  </svg>
);
const UserIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
  </svg>
);
const ChevronDownIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: 12, height: 12 }}>
    <polyline points="6 9 12 15 18 9" />
  </svg>
);

const LogOutIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" />
  </svg>
);

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
 *  - onLogout {fn}             – called when logout is clicked
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
  onLogout = () => { },
  notificationCount = 0,
  searchValue = '',
  onSearchChange = () => { },
}) {
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
                  <React.Fragment key={item.id}>
                  <button
                    className="dropdown-item"
                    onClick={() => console.log(item.id)}
                  >
                    {item.label}
                  </button>
                <hr className="dropdown-divider" />
                </React.Fragment>
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
        <span className='space'></span>
        <button
          id="nav-create-workspace-btn"
          className="nav-create-btn"
          onClick={onCreateWorkspace}
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

        <span className='space'></span>
        <button
          id="nav-logout-btn"
          className="nav-icon-btn"
          aria-label="Log Out"
          onClick={onLogout}
        >
          <LogOutIcon />
        </button>
      </div>
    </header>
  );
}
