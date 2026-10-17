import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Download, Play, Search, Zap } from 'lucide-react'
import PageHeader from '../components/common/PageHeader.jsx'
import { useAppData } from '../context/useAppData.js'
import { sessionRatePerKwh, sessionStatusOptions } from '../data/sessionsData.js'
import { formatCurrency, formatDuration, formatEnergy, formatSessionTime } from '../utils/formatters.js'
import { downloadCsv } from '../utils/csv.js'
import './ChargingSessionsPage.css'

const DEFAULT_FILTERS = {
  search: '',
  from: '',
  to: '',
  station: 'All stations',
  chargerType: 'All types',
  status: 'All statuses',
  sort: 'startedAt',
}

const csvColumns = [
  { label: 'Session ID', value: (session) => session.id },
  { label: 'Station', value: (session) => session.station },
  { label: 'Station ID', value: (session) => session.stationId },
  { label: 'Charger', value: (session) => session.chargerId },
  { label: 'Charger type', value: (session) => session.chargerType },
  { label: 'Start time', value: (session) => session.startedAt },
  { label: 'End time', value: (session) => session.endedAt ?? '' },
  { label: 'Duration (minutes)', value: (session) => session.durationMinutes },
  { label: 'Energy (kWh)', value: (session) => session.energy },
  { label: 'Rate per kWh (INR)', value: (session) => session.ratePerKwh },
  { label: 'Amount (INR)', value: (session) => session.amount },
  { label: 'Status', value: (session) => session.status },
]

function getDuration(session, now) {
  if (session.status !== 'Ongoing') return session.durationMinutes
  return Math.max(0, Math.floor((now.getTime() - new Date(session.startedAt).getTime()) / 60_000))
}

function SessionStatus({ status }) {
  return <span className={`session-status session-status-${status.toLowerCase()}`}>{status}</span>
}

function StartSessionDialog({ chargers, stations, onStart, onClose }) {
  const [chargerId, setChargerId] = useState(chargers.find((charger) => charger.status === 'Available')?.id ?? '')
  const [error, setError] = useState('')
  const availableChargers = chargers.filter((charger) => charger.status === 'Available')
  const stationMap = new Map(stations.map((station) => [station.id, station]))
  function submit(event) {
    event.preventDefault()
    const result = onStart(chargerId)
    if (result.error) setError(result.error)
    else onClose()
  }

  return <div className="session-dialog-backdrop" onMouseDown={onClose}>
    <section className="session-dialog" role="dialog" aria-modal="true" aria-labelledby="start-session-title" onMouseDown={(event) => event.stopPropagation()}>
      <p className="sessions-eyebrow">SIMULATED EV OPERATIONS</p>
      <h2 id="start-session-title">Start a charging session</h2>
      <p>This changes local demo records only and does not send commands to a charger.</p>
      <form onSubmit={submit}>
        <label>Available charger<select value={chargerId} onChange={(event) => setChargerId(event.target.value)} required>
          {availableChargers.map((charger) => <option key={charger.id} value={charger.id}>{charger.id} · {stationMap.get(charger.stationId)?.name ?? charger.stationId}</option>)}
        </select></label>
        {!availableChargers.length && <p className="session-error" role="status">There are no available chargers for a simulated session.</p>}
        {error && <p className="session-error" role="alert">{error}</p>}
        <div className="session-dialog-actions"><button type="button" className="session-secondary-button" onClick={onClose}>Cancel</button><button type="submit" className="session-primary-button" disabled={!availableChargers.length}>Start session</button></div>
      </form>
    </section>
  </div>
}

function ChargingSessionsPage() {
  const { sessions, setSessions, stations, chargers, setChargers } = useAppData()
  const [filters, setFilters] = useState(DEFAULT_FILTERS)
  const [visibleCount, setVisibleCount] = useState(10)
  const [startDialogOpen, setStartDialogOpen] = useState(false)
  const [notice, setNotice] = useState('')
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 60_000)
    return () => window.clearInterval(timer)
  }, [])

  const filteredSessions = useMemo(() => {
    const query = filters.search.trim().toLocaleLowerCase()
    return sessions
      .filter((session) => {
        const date = session.startedAt.slice(0, 10)
        const matchesQuery = !query || [session.id, session.station, session.stationId, session.chargerId]
          .some((value) => value.toLocaleLowerCase().includes(query))
        return matchesQuery &&
          (!filters.from || date >= filters.from) &&
          (!filters.to || date <= filters.to) &&
          (filters.station === 'All stations' || session.stationId === filters.station) &&
          (filters.chargerType === 'All types' || session.chargerType === filters.chargerType) &&
          (filters.status === 'All statuses' || session.status === filters.status)
      })
      .sort((a, b) => filters.sort === 'amount' || filters.sort === 'energy'
        ? b[filters.sort] - a[filters.sort]
        : new Date(b[filters.sort]) - new Date(a[filters.sort]))
  }, [sessions, filters])

  function changeFilter(name, value) {
    setFilters((current) => ({ ...current, [name]: value }))
    setVisibleCount(10)
  }

  function startSession(chargerId) {
    const charger = chargers.find((item) => item.id === chargerId)
    if (!charger || charger.status !== 'Available') return { error: 'Choose an available charger; offline or faulted chargers cannot start a session.' }
    if (sessions.some((session) => session.chargerId === charger.id && session.status === 'Ongoing')) {
      return { error: 'This charger already has an ongoing session.' }
    }
    const startedAt = new Date()
    const id = `SES-DEMO-${startedAt.getTime()}-${sessions.length + 1}`
    const station = stations.find((item) => item.id === charger.stationId)
    const current = charger.type === 'DC'
      ? charger.ratedPower * 1000 / charger.voltage
      : charger.ratedPower * 1000 / (charger.voltage * (charger.voltage >= 380 ? Math.sqrt(3) : 1) * (charger.powerFactor ?? 0.94))
    setSessions((records) => [{
      id,
      stationId: charger.stationId,
      station: station?.name ?? 'Unknown station',
      chargerId: charger.id,
      chargerType: charger.type,
      startedAt: startedAt.toISOString(),
      endedAt: null,
      durationMinutes: 0,
      energy: 0,
      ratePerKwh: sessionRatePerKwh,
      amount: 0,
      status: 'Ongoing',
    }, ...records])
    setChargers((records) => records.map((item) => item.id === chargerId
      ? { ...item, status: 'Charging', current: Number(current.toFixed(1)), currentSession: id, updatedAt: startedAt.toISOString() }
      : item))
    setNotice(`Simulated session ${id} started.`)
    return { error: '' }
  }

  function completeSession(session) {
    if (session.status !== 'Ongoing') return
    const endedAt = now
    const charger = chargers.find((item) => item.id === session.chargerId)
    const durationMinutes = Math.max(1, Math.floor((endedAt.getTime() - new Date(session.startedAt).getTime()) / 60_000))
    const energy = Number((session.energy + (charger?.ratedPower ?? 7.4) * durationMinutes / 60 * 0.72).toFixed(1))
    setSessions((records) => records.map((item) => item.id === session.id
      ? { ...item, endedAt: endedAt.toISOString(), durationMinutes, energy, amount: Number((energy * item.ratePerKwh).toFixed(2)), status: 'Completed' }
      : item))
    setChargers((records) => records.map((item) => item.id === session.chargerId
      ? { ...item, status: 'Available', current: 0, currentSession: '', updatedAt: endedAt.toISOString() }
      : item))
    setNotice(`Simulated session ${session.id} completed.`)
  }

  const completedCount = sessions.filter((item) => item.status === 'Completed').length
  const activeCount = sessions.filter((item) => item.status === 'Ongoing').length
  const failedCount = sessions.filter((item) => item.status === 'Failed').length
  const visibleSessions = filteredSessions.slice(0, visibleCount)

  return <div className="sessions-page">
    <div className="sessions-page-heading">
      <PageHeader title="Charging Sessions" description="Review session history and manage simulated EV charging workflows." />
      <div className="sessions-page-actions">
        <button type="button" className="session-export-button" onClick={() => downloadCsv('evanta-sessions.csv', filteredSessions, csvColumns)}><Download size={15} />Export CSV</button>
        <button type="button" className="session-primary-button" onClick={() => { setNotice(''); setStartDialogOpen(true) }}><Play size={14} />Start simulated session</button>
      </div>
    </div>
    <div className="sessions-demo-banner"><Zap size={15} /><span><strong>Simulated EV operations only.</strong> Starting or completing a session only updates this browser’s demo data; it never controls physical chargers.</span></div>
    <section className="sessions-summary-grid" aria-label="Session summary">
      <article><span>All sessions</span><strong>{sessions.length}</strong></article>
      <article><span>Completed</span><strong>{completedCount}</strong></article>
      <article><span>Ongoing</span><strong>{activeCount}</strong></article>
      <article><span>Failed</span><strong>{failedCount}</strong></article>
    </section>
    <section className="sessions-table-card" aria-label="Charging session records">
      <div className="sessions-table-heading"><div><h2>Session history</h2><p>Showing <strong>{filteredSessions.length}</strong> matching records</p></div><span className="session-demo-label">DEMO DATA</span></div>
      <div className="sessions-filters">
        <label className="sessions-search"><Search size={14} /><input type="search" value={filters.search} onChange={(event) => changeFilter('search', event.target.value)} placeholder="Search session, station, or charger" aria-label="Search sessions" /></label>
        <label><span className="visually-hidden">Start date</span><input aria-label="Sessions from date" type="date" value={filters.from} onChange={(event) => changeFilter('from', event.target.value)} /></label>
        <label><span className="visually-hidden">End date</span><input aria-label="Sessions to date" type="date" value={filters.to} onChange={(event) => changeFilter('to', event.target.value)} /></label>
        <label><span className="visually-hidden">Filter sessions by station</span><select value={filters.station} onChange={(event) => changeFilter('station', event.target.value)}><option>All stations</option>{stations.map((station) => <option key={station.id} value={station.id}>{station.name}</option>)}</select></label>
        <label><span className="visually-hidden">Filter by charger type</span><select value={filters.chargerType} onChange={(event) => changeFilter('chargerType', event.target.value)}><option>All types</option><option>AC</option><option>DC</option></select></label>
        <label><span className="visually-hidden">Filter sessions by status</span><select value={filters.status} onChange={(event) => changeFilter('status', event.target.value)}><option>All statuses</option>{sessionStatusOptions.map((status) => <option key={status}>{status}</option>)}</select></label>
        <label><span className="visually-hidden">Sort sessions</span><select value={filters.sort} onChange={(event) => changeFilter('sort', event.target.value)}><option value="startedAt">Sort: Newest start</option><option value="energy">Sort: Energy</option><option value="amount">Sort: Amount</option></select></label>
        <button className="session-reset-button" type="button" onClick={() => { setFilters(DEFAULT_FILTERS); setVisibleCount(10) }} disabled={JSON.stringify(filters) === JSON.stringify(DEFAULT_FILTERS)}>Reset</button>
      </div>
      {notice && <p className="session-notice" role="status">{notice}</p>}
      {visibleSessions.length ? <div className="sessions-table-scroll"><table className="sessions-table">
        <thead><tr><th>Session ID</th><th>Station</th><th>Charger</th><th>Start time</th><th>Duration</th><th>Energy</th><th>Rate / kWh</th><th>Amount</th><th>Status</th><th><span className="visually-hidden">Actions</span></th></tr></thead>
        <tbody>{visibleSessions.map((session) => <tr key={session.id}>
          <td><Link className="session-id-link" to={`/sessions/${encodeURIComponent(session.id)}`}>{session.id}</Link></td>
          <td><Link className="session-station-link" to={`/stations/${session.stationId}`}>{session.station}<small>{session.stationId}</small></Link></td>
          <td>{session.chargerId}<small>{session.chargerType}</small></td>
          <td>{formatSessionTime(new Date(session.startedAt))}</td>
          <td>{formatDuration(getDuration(session, now))}</td>
          <td>{formatEnergy(session.energy, 1)}</td>
          <td>{formatCurrency(session.ratePerKwh)}</td>
          <td>{formatCurrency(session.amount)}</td>
          <td><SessionStatus status={session.status} /></td>
          <td>{session.status === 'Ongoing' ? <button type="button" className="session-complete-button" onClick={() => completeSession(session)}>Complete</button> : <Link className="session-view-link" to={`/sessions/${encodeURIComponent(session.id)}`}>View</Link>}</td>
        </tr>)}</tbody>
      </table></div> : <div className="sessions-empty-state"><Search size={20} /><h3>No sessions found</h3><p>Adjust your filters or search, or start a simulated session.</p><button type="button" onClick={() => setFilters(DEFAULT_FILTERS)}>Reset filters</button></div>}
      {filteredSessions.length > visibleSessions.length && <button type="button" className="session-show-more" onClick={() => setVisibleCount((count) => count + 10)}>Show {Math.min(10, filteredSessions.length - visibleSessions.length)} more sessions</button>}
    </section>
    <p className="sessions-disclaimer">Session records, charging status, energy, and prices are simulated frontend data. No physical EV charging equipment is controlled.</p>
    {startDialogOpen && <StartSessionDialog chargers={chargers} stations={stations} onStart={startSession} onClose={() => setStartDialogOpen(false)} />}
  </div>
}

export default ChargingSessionsPage
