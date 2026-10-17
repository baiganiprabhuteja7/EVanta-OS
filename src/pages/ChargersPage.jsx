import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertTriangle,
  BatteryCharging,
  CheckCircle2,
  CircleOff,
  Plus,
  Search,
  Trash2,
  X,
  Zap,
} from 'lucide-react'
import PageHeader from '../components/common/PageHeader.jsx'
import { chargerStatusOptions } from '../data/chargersData.js'
import { useAppData } from '../context/useAppData.js'
import { formatNumber } from '../utils/formatters.js'
import './ChargersPage.css'

const INITIAL_FILTERS = {
  search: '',
  station: 'All stations',
  type: 'All types',
  connector: 'All connectors',
  status: 'All statuses',
  sort: 'id',
}

const blankCharger = {
  id: '',
  stationId: '',
  type: 'AC',
  connector: 'Type 2',
  ratedPower: '7.4',
  voltage: '230',
  current: '0',
  powerFactor: '0.94',
  status: 'Available',
}

const chargerSortOptions = [
  ['id', 'Charger ID'],
  ['ratedPower', 'Rated power'],
  ['stationId', 'Station'],
  ['status', 'Status'],
]

const measuredPower = (charger) => {
  if (charger.type === 'DC') return (charger.voltage * charger.current) / 1000
  const phaseFactor = charger.voltage >= 380 ? Math.sqrt(3) : 1
  return (phaseFactor * charger.voltage * charger.current * (charger.powerFactor ?? 0.94)) / 1000
}

function ChargerSummary({ icon: Icon, label, value, tone }) {
  return (
    <article className="charger-summary-card">
      <span className={`charger-summary-icon charger-summary-icon-${tone}`} aria-hidden="true">
        <Icon size={18} />
      </span>
      <div><span>{label}</span><strong>{formatNumber(value)}</strong></div>
    </article>
  )
}

function ChargerDialog({ charger, stations, onClose, onSave }) {
  const editing = Boolean(charger)
  const [form, setForm] = useState(charger ? {
    ...charger,
    ratedPower: String(charger.ratedPower),
    voltage: String(charger.voltage),
    current: String(charger.current),
    powerFactor: String(charger.powerFactor ?? 0.94),
  } : { ...blankCharger, stationId: stations[0]?.id ?? '' })
  const [error, setError] = useState('')

  function updateField(event) {
    const { name, value } = event.target
    setForm((previous) => ({
      ...previous,
      [name]: value,
      ...(name === 'type' ? { connector: value === 'AC' ? 'Type 2' : 'CCS2' } : {}),
      ...(name === 'status' && value !== 'Charging' ? { current: '0' } : {}),
    }))
    setError('')
  }

  function submit(event) {
    event.preventDefault()
    const result = onSave({
      ...form,
      id: form.id.trim().toUpperCase(),
      ratedPower: Number(form.ratedPower),
      voltage: Number(form.voltage),
      current: Number(form.current),
      powerFactor: form.type === 'AC' ? Number(form.powerFactor) : null,
      currentSession: form.status === 'Charging'
        ? charger?.currentSession || `SIM-${form.id.trim().toUpperCase()}`
        : '',
      updatedAt: new Date().toISOString(),
    })
    if (result.error) {
      setError(result.error)
      return
    }
    onClose()
  }

  return (
    <div className="charger-dialog-backdrop" onMouseDown={onClose}>
      <section className="charger-dialog" role="dialog" aria-modal="true" aria-labelledby="charger-dialog-title" onMouseDown={(event) => event.stopPropagation()}>
        <header className="charger-dialog-header">
          <div>
            <p className="charger-eyebrow">{editing ? 'Inventory record' : 'Network setup'}</p>
            <h2 id="charger-dialog-title">{editing ? 'Edit charger' : 'Add charger'}</h2>
            <p>Electrical values are illustrative. No hardware is connected.</p>
          </div>
          <button type="button" className="charger-icon-button" aria-label="Close dialog" onClick={onClose}><X size={18} /></button>
        </header>
        <form className="charger-form" onSubmit={submit}>
          <label>Charger ID<input name="id" value={form.id} onChange={updateField} required maxLength={32} placeholder="CH-BLR-001-01" /></label>
          <label>Station<select name="stationId" value={form.stationId} onChange={updateField} required>
            {stations.map((station) => <option key={station.id} value={station.id}>{station.name} · {station.id}</option>)}
          </select></label>
          <div className="charger-form-row">
            <label>Charger type<select name="type" value={form.type} onChange={updateField}><option>AC</option><option>DC</option></select></label>
            <label>Connector<select name="connector" value={form.connector} onChange={updateField}>
              {(form.type === 'AC' ? ['Type 2'] : ['CCS2', 'CHAdeMO']).map((connector) => <option key={connector}>{connector}</option>)}
            </select></label>
          </div>
          <div className="charger-form-row">
            <label>Rated power (kW)<input type="number" name="ratedPower" value={form.ratedPower} onChange={updateField} required min="1" max="500" step="0.1" /></label>
            <label>Voltage (V)<input type="number" name="voltage" value={form.voltage} onChange={updateField} required min="1" max="1500" /></label>
          </div>
          <div className="charger-form-row">
            <label>Current (A)<input type="number" name="current" value={form.current} onChange={updateField} required min="0" max="1000" step="0.1" /></label>
            {form.type === 'AC' && <label>Power factor<input type="number" name="powerFactor" value={form.powerFactor} onChange={updateField} required min="0.1" max="1" step="0.01" /></label>}
          </div>
          <label>Operational status<select name="status" value={form.status} onChange={updateField}>
            {chargerStatusOptions.filter((status) => status !== 'Charging' || form.status === 'Charging').map((status) => <option key={status}>{status}</option>)}
          </select></label>
          {error && <p className="charger-form-error" role="alert">{error}</p>}
          <div className="charger-dialog-actions">
            <button type="button" className="charger-secondary-button" onClick={onClose}>Cancel</button>
            <button type="submit" className="charger-primary-button">{editing ? 'Save changes' : 'Add charger'}</button>
          </div>
        </form>
      </section>
    </div>
  )
}

function ChargerDetails({ charger, station, onClose, onEdit }) {
  const power = measuredPower(charger)
  return (
    <div className="charger-dialog-backdrop" onMouseDown={onClose}>
      <section className="charger-dialog charger-details-dialog" role="dialog" aria-modal="true" aria-labelledby="charger-details-title" onMouseDown={(event) => event.stopPropagation()}>
        <header className="charger-dialog-header">
          <div><p className="charger-eyebrow">{charger.id}</p><h2 id="charger-details-title">{station?.name ?? 'Unknown station'}</h2>
            {station && <Link to={`/stations/${station.id}`} className="charger-station-link">{station.location} · View station</Link>}
          </div>
          <button type="button" className="charger-icon-button" aria-label="Close details" onClick={onClose}><X size={18} /></button>
        </header>
        <div className={`charger-status-pill charger-status-${charger.status.toLowerCase()}`}>{charger.status}</div>
        <dl className="charger-detail-grid">
          <div><dt>Type / connector</dt><dd>{charger.type} · {charger.connector}</dd></div>
          <div><dt>Rated power</dt><dd>{charger.ratedPower} kW</dd></div>
          <div><dt>Voltage</dt><dd>{charger.voltage} V</dd></div>
          <div><dt>Current</dt><dd>{charger.current} A</dd></div>
          <div><dt>Estimated real power</dt><dd>{power.toFixed(1)} kW</dd></div>
          <div><dt>Last updated</dt><dd>{new Date(charger.updatedAt).toLocaleString('en-IN')}</dd></div>
          {charger.currentSession && <div><dt>Simulated session</dt><dd>{charger.currentSession}</dd></div>}
        </dl>
        <p className="charger-measurement-note">Power estimate uses V × I for DC and √3 × line voltage × current × power factor for balanced three-phase AC. Values are simulated.</p>
        <div className="charger-dialog-actions">
          <button type="button" className="charger-secondary-button" onClick={onClose}>Close</button>
          <button type="button" className="charger-primary-button" onClick={onEdit}>Edit charger</button>
        </div>
      </section>
    </div>
  )
}

function ChargersPage() {
  const { stations, chargers, sessions, setChargers } = useAppData()
  const [filters, setFilters] = useState(INITIAL_FILTERS)
  const [dialogCharger, setDialogCharger] = useState(undefined)
  const [detailsCharger, setDetailsCharger] = useState(null)
  const [deleteError, setDeleteError] = useState('')
  const stationMap = useMemo(() => new Map(stations.map((station) => [station.id, station])), [stations])

  const filteredChargers = useMemo(() => {
    const query = filters.search.trim().toLocaleLowerCase()
    return chargers
      .filter((charger) => {
        const station = stationMap.get(charger.stationId)
        const matchesQuery = !query || [charger.id, charger.stationId, charger.connector, station?.name ?? '']
          .some((item) => item.toLocaleLowerCase().includes(query))
        return matchesQuery &&
          (filters.station === 'All stations' || charger.stationId === filters.station) &&
          (filters.type === 'All types' || charger.type === filters.type) &&
          (filters.connector === 'All connectors' || charger.connector === filters.connector) &&
          (filters.status === 'All statuses' || charger.status === filters.status)
      })
      .sort((a, b) => {
        const left = a[filters.sort]
        const right = b[filters.sort]
        return typeof left === 'number' ? left - right : String(left).localeCompare(String(right))
      })
  }, [chargers, filters, stationMap])

  const counts = useMemo(() => ({
    total: chargers.length,
    available: chargers.filter((item) => item.status === 'Available').length,
    charging: chargers.filter((item) => item.status === 'Charging').length,
    offline: chargers.filter((item) => item.status === 'Offline').length,
    faulted: chargers.filter((item) => item.status === 'Faulted').length,
  }), [chargers])

  function saveCharger(charger) {
    if (!stationMap.has(charger.stationId)) return { error: 'Select a station that exists in this workspace.' }
    if (chargers.some((item) => item.id.toLowerCase() === charger.id.toLowerCase() && item.id !== dialogCharger?.id)) {
      return { error: 'A charger with this ID already exists.' }
    }
    const ongoingSession = sessions.find((session) => session.chargerId === dialogCharger?.id && session.status === 'Ongoing')
    if (ongoingSession && charger.status !== 'Charging') {
      return { error: 'Complete the ongoing simulated session before changing this charger status or station.' }
    }
    if (charger.current > charger.ratedPower * 1000 / Math.max(charger.voltage, 1) * (charger.type === 'AC' && charger.voltage >= 380 ? 1.8 : 1.2)) {
      return { error: 'Current is outside the plausible range for the selected voltage and power rating.' }
    }
    setChargers((current) => dialogCharger
      ? current.map((item) => item.id === dialogCharger.id ? charger : item)
      : [...current, charger])
    setDetailsCharger(null)
    setDialogCharger(undefined)
    setDeleteError('')
    return { error: '' }
  }

  function deleteCharger(charger) {
    if (sessions.some((session) => session.chargerId === charger.id && session.status === 'Ongoing')) {
      setDeleteError('Complete the ongoing simulated session before deleting this charger.')
      return
    }
    if (!window.confirm(`Delete charger ${charger.id}? This removes it from the local demo workspace.`)) return
    setChargers((current) => current.filter((item) => item.id !== charger.id))
    setDetailsCharger(null)
    setDeleteError('')
  }

  function changeFilter(name, value) {
    setFilters((current) => ({ ...current, [name]: value }))
  }

  return (
    <div className="chargers-page">
      <div className="chargers-page-heading">
        <PageHeader title="Charger Management" description="Inventory, status, and simulated electrical readings for your charging network." />
        <button className="charger-primary-button charger-add-button" type="button" onClick={() => setDialogCharger(null)}><Plus size={16} />Add Charger</button>
      </div>
      <div className="charger-simulation-banner"><Zap size={15} /><span><strong>Demo inventory</strong> · Charger status and electrical readings are simulated, not live hardware telemetry.</span></div>
      <section className="charger-summary-grid" aria-label="Charger status summary">
        <ChargerSummary label="Total Chargers" value={counts.total} icon={BatteryCharging} tone="total" />
        <ChargerSummary label="Available" value={counts.available} icon={CheckCircle2} tone="available" />
        <ChargerSummary label="Charging" value={counts.charging} icon={Zap} tone="charging" />
        <ChargerSummary label="Offline" value={counts.offline} icon={CircleOff} tone="offline" />
        <ChargerSummary label="Faulted" value={counts.faulted} icon={AlertTriangle} tone="faulted" />
      </section>
      <section className="chargers-list-card" aria-label="Charger inventory">
        <div className="chargers-list-heading">
          <div><h2>Charger inventory</h2><p>Showing <strong>{filteredChargers.length}</strong> of <strong>{chargers.length}</strong> chargers</p></div>
          <span className="charger-demo-label">SIMULATED DATA</span>
        </div>
        <div className="charger-filters">
          <label className="charger-search"><Search size={15} /><input type="search" value={filters.search} onChange={(event) => changeFilter('search', event.target.value)} placeholder="Search charger or station" aria-label="Search chargers" /></label>
          <label><span className="visually-hidden">Filter by station</span><select value={filters.station} onChange={(event) => changeFilter('station', event.target.value)}><option>All stations</option>{stations.map((station) => <option key={station.id} value={station.id}>{station.name}</option>)}</select></label>
          <label><span className="visually-hidden">Filter by type</span><select value={filters.type} onChange={(event) => changeFilter('type', event.target.value)}><option>All types</option><option>AC</option><option>DC</option></select></label>
          <label><span className="visually-hidden">Filter by connector</span><select value={filters.connector} onChange={(event) => changeFilter('connector', event.target.value)}><option>All connectors</option>{[...new Set(chargers.map((item) => item.connector))].sort().map((connector) => <option key={connector}>{connector}</option>)}</select></label>
          <label><span className="visually-hidden">Filter by status</span><select value={filters.status} onChange={(event) => changeFilter('status', event.target.value)}><option>All statuses</option>{chargerStatusOptions.map((status) => <option key={status}>{status}</option>)}</select></label>
          <label><span className="visually-hidden">Sort chargers</span><select value={filters.sort} onChange={(event) => changeFilter('sort', event.target.value)}>{chargerSortOptions.map(([value, title]) => <option key={value} value={value}>Sort: {title}</option>)}</select></label>
          <button className="charger-reset-button" type="button" onClick={() => setFilters(INITIAL_FILTERS)} disabled={JSON.stringify(filters) === JSON.stringify(INITIAL_FILTERS)}>Reset</button>
        </div>
        {deleteError && <p className="charger-inline-error" role="status">{deleteError}</p>}
        {filteredChargers.length ? <div className="chargers-table-scroll">
          <table className="chargers-table">
            <thead><tr><th>Charger</th><th>Station</th><th>Type / connector</th><th>Rated power</th><th>Voltage</th><th>Current</th><th>Est. power</th><th>Status</th><th><span className="visually-hidden">Actions</span></th></tr></thead>
            <tbody>{filteredChargers.map((charger) => {
              const station = stationMap.get(charger.stationId)
              return <tr key={charger.id}>
                <td><strong>{charger.id}</strong><small>{charger.currentSession ? `Session ${charger.currentSession}` : 'No active session'}</small></td>
                <td>{station ? <Link to={`/stations/${station.id}`} className="charger-station-link">{station.name}<small>{station.id}</small></Link> : <span className="charger-inline-error">Station missing</span>}</td>
                <td>{charger.type} · {charger.connector}</td>
                <td>{charger.ratedPower} kW</td><td>{charger.voltage} V</td><td>{charger.current} A</td>
                <td>{measuredPower(charger).toFixed(1)} kW</td>
                <td><span className={`charger-status-pill charger-status-${charger.status.toLowerCase()}`}>{charger.status}</span></td>
                <td><div className="charger-row-actions">
                  <button type="button" onClick={() => setDetailsCharger(charger)}>View</button>
                  <button type="button" onClick={() => setDialogCharger(charger)}>Edit</button>
                  <button type="button" aria-label={`Delete ${charger.id}`} onClick={() => deleteCharger(charger)}><Trash2 size={14} /></button>
                </div></td>
              </tr>
            })}</tbody>
          </table>
        </div> : <div className="chargers-empty-state"><Search size={20} /><h3>No chargers found</h3><p>Change the search or filter criteria to see charger records.</p><button type="button" className="charger-secondary-button" onClick={() => setFilters(INITIAL_FILTERS)}>Reset filters</button></div>}
      </section>
      <p className="charger-footnote">AC power estimate uses voltage × current × power factor, with √3 for balanced three-phase readings. DC estimate uses voltage × current. Estimates only; not measured hardware data.</p>
      {dialogCharger !== undefined && <ChargerDialog key={dialogCharger?.id ?? 'new'} charger={dialogCharger} stations={stations} onClose={() => setDialogCharger(undefined)} onSave={saveCharger} />}
      {detailsCharger && <ChargerDetails charger={detailsCharger} station={stationMap.get(detailsCharger.stationId)} onClose={() => setDetailsCharger(null)} onEdit={() => { setDialogCharger(detailsCharger); setDetailsCharger(null) }} />}
    </div>
  )
}

export default ChargersPage
