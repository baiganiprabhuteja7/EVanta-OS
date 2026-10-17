import { useEffect, useState } from 'react'
import { Suspense } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar.jsx'
import Topbar from './Topbar.jsx'

function AppShell() {
  const [mobileNavState, setMobileNavState] = useState({
    isOpen: false,
    pathname: '',
  })
  const { pathname } = useLocation()
  const isMobileNavOpen =
    mobileNavState.isOpen && mobileNavState.pathname === pathname

  useEffect(() => {
    if (!isMobileNavOpen) return undefined

    function closeOnEscape(event) {
      if (event.key === 'Escape') {
        setMobileNavState({ isOpen: false, pathname })
      }
    }

    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [isMobileNavOpen, pathname])

  return (
    <div className="app-shell">
      <Sidebar
        isOpen={isMobileNavOpen}
        onNavigate={() => setMobileNavState({ isOpen: false, pathname })}
      />
      {isMobileNavOpen && (
        <button
          className="sidebar-backdrop"
          type="button"
          aria-label="Close navigation menu"
          onClick={() => setMobileNavState({ isOpen: false, pathname })}
        />
      )}
      <div className="workspace">
        <Topbar
          onMenuClick={() => setMobileNavState({ isOpen: true, pathname })}
        />
        <main className="main-content">
          <Suspense fallback={<div className="page-loading" role="status">Loading workspace…</div>}>
            <Outlet />
          </Suspense>
        </main>
      </div>
    </div>
  )
}

export default AppShell
