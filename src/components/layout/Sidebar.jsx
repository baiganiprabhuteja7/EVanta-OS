import { Zap } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { navigationItems } from '../../data/navigation.js'

function Sidebar({ isOpen, onNavigate }) {
  return (
    <aside
      className={`sidebar${isOpen ? ' is-open' : ''}`}
      aria-label="Main navigation"
    >
      <NavLink
        className="brand"
        to="/dashboard"
        aria-label="EVanta OS dashboard"
        onClick={onNavigate}
      >
        <span className="brand-mark" aria-hidden="true">
          <Zap size={20} strokeWidth={2.5} />
        </span>
        <span className="brand-copy">
          <span className="brand-name">EVanta OS</span>
          <span className="brand-subtitle">CHARGING INTELLIGENCE</span>
        </span>
      </NavLink>

      <p className="sidebar-section-label">Workspace</p>
      <nav className="sidebar-nav">
        {navigationItems.map(({ icon: Icon, label, path }) => (
          <NavLink
            key={path}
            className="nav-link"
            to={path}
            onClick={onNavigate}
          >
            <Icon className="nav-icon" size={17} strokeWidth={1.8} aria-hidden="true" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <span className="footer-indicator" aria-hidden="true" />
        <span className="footer-copy">
          <strong>Platform workspace</strong>
          <span>Powering Mobility. Engineering Intelligence.</span>
        </span>
      </div>
    </aside>
  )
}

export default Sidebar
