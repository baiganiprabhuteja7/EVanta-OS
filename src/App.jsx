import { lazy } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import AppShell from './components/layout/AppShell.jsx'

const DashboardPage = lazy(() => import('./pages/DashboardPage.jsx'))
const StationsPage = lazy(() => import('./pages/StationsPage.jsx'))
const StationDetailsPage = lazy(() => import('./pages/StationDetailsPage.jsx'))
const ChargersPage = lazy(() => import('./pages/ChargersPage.jsx'))
const EnergyMonitoringPage = lazy(() => import('./pages/EnergyMonitoringPage.jsx'))
const BusinessAnalyticsPage = lazy(() => import('./pages/BusinessAnalyticsPage.jsx'))
const ChargingSessionsPage = lazy(() => import('./pages/ChargingSessionsPage.jsx'))
const SessionDetailsPage = lazy(() => import('./pages/SessionDetailsPage.jsx'))
const SettingsPage = lazy(() => import('./pages/SettingsPage.jsx'))

function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="stations" element={<StationsPage />} />
        <Route path="stations/:stationId" element={<StationDetailsPage />} />
        <Route path="chargers" element={<ChargersPage />} />
        <Route path="energy" element={<EnergyMonitoringPage />} />
        <Route path="analytics" element={<BusinessAnalyticsPage />} />
        <Route path="sessions" element={<ChargingSessionsPage />} />
        <Route path="sessions/:sessionId" element={<SessionDetailsPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  )
}

export default App
