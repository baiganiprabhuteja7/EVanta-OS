import { Bell, ChevronDown, ChevronRight, Menu, Search } from 'lucide-react'
import { useState } from 'react'
import { useLocation } from 'react-router-dom'
import { navigationItems } from '../../data/navigation.js'

function Topbar({ onMenuClick }) {
  const [isProfileOpen, setIsProfileOpen] = useState(false)
  const { pathname } = useLocation()
  const currentPage =
    navigationItems.find((item) => item.path === pathname) ?? navigationItems[0]

  return (
    <header className="topbar">
      <div className="topbar-leading">
        <button
          className="mobile-menu-button"
          type="button"
          aria-label="Open navigation menu"
          onClick={onMenuClick}
        >
          <Menu size={19} aria-hidden="true" />
        </button>
        <div className="breadcrumb" aria-label="Breadcrumb">
          <span>Workspace</span>
          <ChevronRight size={14} aria-hidden="true" />
          <span className="breadcrumb-current" aria-current="page">
            {currentPage.label}
          </span>
        </div>
      </div>

      <div className="topbar-actions">
        <label className="search-box">
          <Search size={15} aria-hidden="true" />
          <input type="search" aria-label="Search workspace" placeholder="Search" />
          <kbd aria-hidden="true">⌘ K</kbd>
        </label>
        <span className="topbar-divider" aria-hidden="true" />
        <button
          className="icon-button"
          type="button"
          aria-label="Notifications will be available in a future release"
          title="Notifications will be available in a future release"
          disabled
        >
          <Bell size={18} aria-hidden="true" />
        </button>
        <span className="topbar-divider" aria-hidden="true" />
        <div className="profile-wrap">
          <button
            className="profile-button"
            type="button"
            aria-label="Open profile menu"
            aria-expanded={isProfileOpen}
            onClick={() => setIsProfileOpen((isOpen) => !isOpen)}
          >
            <span className="avatar" aria-hidden="true">
              EV
            </span>
            <span className="profile-copy">
              <strong>EVanta Admin</strong>
              <span>Workspace owner</span>
            </span>
            <ChevronDown className="profile-chevron" size={15} aria-hidden="true" />
          </button>
          {isProfileOpen && (
            <div className="profile-menu" role="status">
              <strong>EVanta Admin</strong>
              <span>Workspace profile controls will be available in a future release.</span>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}

export default Topbar
