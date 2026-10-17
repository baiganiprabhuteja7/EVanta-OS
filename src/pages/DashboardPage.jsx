import { lazy, Suspense } from 'react'
import './DashboardPage.css'

const DashboardPageContent = lazy(() => import('./DashboardPageContent.jsx'))

function DashboardPage() {
  return (
    <Suspense fallback={<div className="dashboard-loading">Loading dashboard…</div>}>
      <DashboardPageContent />
    </Suspense>
  )
}

export default DashboardPage
