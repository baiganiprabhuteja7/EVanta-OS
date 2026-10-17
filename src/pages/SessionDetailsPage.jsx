import { Link, Navigate, useParams } from 'react-router-dom'
import { ArrowLeft, BatteryCharging, Clock3, Zap } from 'lucide-react'
import PageHeader from '../components/common/PageHeader.jsx'
import { useAppData } from '../context/useAppData.js'
import { formatCurrency, formatDuration, formatEnergy, formatSessionTime } from '../utils/formatters.js'
import './SessionDetailsPage.css'

function SessionDetailsPage() {
  const { sessionId } = useParams()
  const { sessions } = useAppData()
  const session = sessions.find((item) => item.id === sessionId)
  if (!session) return <Navigate to="/sessions" replace />

  return <div className="session-details-page">
    <Link to="/sessions" className="session-details-back"><ArrowLeft size={15} />Back to sessions</Link>
    <div className="session-details-header"><PageHeader title="Session details" description={session.id} /><span className={`session-status session-status-${session.status.toLowerCase()}`}>{session.status}</span></div>
    <section className="session-details-grid">
      <article><span><BatteryCharging size={14} />Station</span><strong>{session.station}</strong><Link to={`/stations/${session.stationId}`}>{session.stationId} · view station</Link></article>
      <article><span><Zap size={14} />Charger</span><strong>{session.chargerId} · {session.chargerType}</strong></article>
      <article><span>Start time</span><strong>{formatSessionTime(new Date(session.startedAt))}</strong></article>
      <article><span>End time</span><strong>{session.endedAt ? formatSessionTime(new Date(session.endedAt)) : 'In progress'}</strong></article>
      <article><span><Clock3 size={14} />Duration</span><strong>{formatDuration(session.durationMinutes)}</strong></article>
      <article><span>Energy delivered</span><strong>{formatEnergy(session.energy, 1)}</strong></article>
      <article><span>Rate per kWh</span><strong>{formatCurrency(session.ratePerKwh)}</strong></article>
      <article><span>Estimated amount</span><strong>{formatCurrency(session.amount)}</strong></article>
    </section>
    <p className="session-details-disclaimer">Session details are illustrative frontend demo data. No physical charging equipment is connected or controlled.</p>
  </div>
}

export default SessionDetailsPage
