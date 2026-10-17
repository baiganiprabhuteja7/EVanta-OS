import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertTriangle,
  ArrowDownWideNarrow,
  ArrowUpWideNarrow,
  CheckCircle2,
  CircleOff,
  MapPin,
  Plus,
  RotateCcw,
  Search,
  Trash2,
  X,
} from 'lucide-react'
import PageHeader from '../components/common/PageHeader.jsx'
import StationStatusBadge from '../components/common/StationStatusBadge.jsx'
import { stationStatusOptions } from '../data/stationsData.js'
import { createChargerRecord } from '../data/chargersData.js'
import { useAppData } from '../context/useAppData.js'
import { formatCurrency, formatEnergy, formatNumber } from '../utils/formatters.js'
import './StationsPage.css'

const DEFAULT_FILTERS = {
  search: '',
  status: 'All statuses',
  location: 'All locations',
  sort: 'name',
  direction: 'asc',
}

const sortOptions = [
  { value: 'name', label: 'Station name' },
  { value: 'energyDelivered', label: 'Energy delivered' },
  { value: 'todaysRevenue', label: "Today's revenue" },
  { value: 'utilization', label: 'Utilization' },
]

const emptyForm = {
  id: '',
  name: '',
  location: '',
  address: '',
  chargers: '',
  status: 'Online',
}

function StationSummaryCard({ label, value, note, icon: Icon, tone }) {
  return (
    <article className="station-summary-card">
      <span className={`station-summary-icon station-summary-icon-${tone}`} aria-hidden="true">
        <Icon size={17} strokeWidth={1.8} />
      </span>
      <div className="station-summary-content">
        <span>{label}</span>
        <strong>{formatNumber(value)}</strong>
        <small>{note}</small>
      </div>
    </article>
  )
}

function StationDialog({ station, onClose, onSave }) {
  const isEditing = Boolean(station)
  const [form, setForm] = useState(
    station
      ? {
          id: station.id,
          name: station.name,
          location: station.location,
          address: station.address ?? '',
          chargers: String(station.chargers),
          status: station.status,
        }
      : emptyForm,
  )
  const [error, setError] = useState('')

  useEffect(() => {
    function closeOnEscape(event) {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [onClose])

  function updateField(event) {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
    setError('')
  }

  function handleSubmit(event) {
    event.preventDefault()
    const result = onSave({
      ...form,
      id: form.id.trim().toUpperCase(),
      name: form.name.trim(),
      location: form.location.trim(),
      address: form.address.trim(),
      chargers: Number(form.chargers),
    })
    if (result.error) {
      setError(result.error)
      return
    }
    onClose()
  }

  return (
    <div className="station-dialog-backdrop" onMouseDown={onClose}>
      <section
        className="station-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="station-dialog-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="station-dialog-header">
          <div>
            <p className="stations-eyebrow">{isEditing ? 'Station details' : 'Network setup'}</p>
            <h2 id="station-dialog-title">{isEditing ? 'Edit station' : 'Add a station'}</h2>
            <p>
              {isEditing
                ? 'Update this station in the local demo workspace.'
                : 'Add a station to the local demo network.'}
            </p>
          </div>
          <button className="station-close-button" type="button" aria-label="Close dialog" onClick={onClose}>
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        <form className="station-form" onSubmit={handleSubmit}>
          <label>
            Station ID
            <input
              name="id"
              value={form.id}
              onChange={updateField}
              placeholder="EV-BLR-009"
              required
              maxLength={24}
              readOnly={isEditing}
              autoFocus
            />
          </label>
          <label>
            Station name
            <input
              name="name"
              value={form.name}
              onChange={updateField}
              placeholder="Central City Charging Hub"
              required
              maxLength={80}
            />
          </label>
          <label>
            Location
            <input
              name="location"
              value={form.location}
              onChange={updateField}
              placeholder="Ahmedabad, Gujarat"
              required
              maxLength={100}
            />
          </label>
          <label>
            Street address
            <input
              name="address"
              value={form.address}
              onChange={updateField}
              placeholder="Street, area, postal code"
              required
              maxLength={160}
            />
          </label>
          <div className="station-form-row">
            <label>
              Number of chargers
              <input
                name="chargers"
                type="number"
                value={form.chargers}
                onChange={updateField}
                min="1"
                max="500"
                required
              />
            </label>
            <label>
              Station status
              <select name="status" value={form.status} onChange={updateField}>
                {stationStatusOptions.map((status) => (
                  <option key={status} value={status}>{status}</option>
                ))}
              </select>
            </label>
          </div>
          {error && <p className="station-form-error" role="alert">{error}</p>}
          <div className="station-dialog-actions">
            <button className="station-secondary-button" type="button" onClick={onClose}>
              Cancel
            </button>
            <button className="station-primary-button" type="submit">
              {isEditing ? 'Save changes' : 'Add station'}
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}

function StationDetails({ station, onClose, onEdit }) {
  return (
    <div className="station-dialog-backdrop" onMouseDown={onClose}>
      <section
        className="station-dialog station-details-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="station-details-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="station-dialog-header">
          <div>
            <p className="stations-eyebrow">{station.id}</p>
            <h2 id="station-details-title">{station.name}</h2>
            <p>{station.location}</p>
          </div>
          <button className="station-close-button" type="button" aria-label="Close details" onClick={onClose}>
            <X size={18} aria-hidden="true" />
          </button>
        </div>
        <div className="station-details-status"><StationStatusBadge status={station.status} /></div>
        <dl className="station-detail-grid">
          <div><dt>Total chargers</dt><dd>{formatNumber(station.chargers)}</dd></div>
          <div><dt>Active chargers</dt><dd>{formatNumber(station.activeChargers)}</dd></div>
          <div><dt>Energy delivered</dt><dd>{formatEnergy(station.energyDelivered)}</dd></div>
          <div><dt>Today's revenue</dt><dd>{formatCurrency(station.todaysRevenue)}</dd></div>
          <div><dt>Utilization</dt><dd>{station.utilization}%</dd></div>
        </dl>
        <div className="station-dialog-actions">
          <button className="station-secondary-button" type="button" onClick={onClose}>Close</button>
          <button className="station-primary-button" type="button" onClick={onEdit}>Edit station</button>
        </div>
      </section>
    </div>
  )
}

function ChargingStationsPage() {
  const { stations, setStations, chargers, setChargers, sessions, setSessions } = useAppData()
  const [filters, setFilters] = useState(DEFAULT_FILTERS)
  const [dialogStation, setDialogStation] = useState(undefined)
  const [detailsStation, setDetailsStation] = useState(null)
  const closeForm = () => setDialogStation(undefined)

  const locations = useMemo(
    () => [...new Set(stations.map((station) => station.location))].sort(),
    [stations],
  )

  const filteredStations = useMemo(() => {
    const query = filters.search.trim().toLocaleLowerCase()
    return stations
      .filter((station) => {
        const matchesQuery =
          !query ||
          [station.name, station.id, station.location].some((value) =>
            value.toLocaleLowerCase().includes(query),
          )
        const matchesStatus =
          filters.status === 'All statuses' || station.status === filters.status
        const matchesLocation =
          filters.location === 'All locations' ||
          station.location === filters.location
        return matchesQuery && matchesStatus && matchesLocation
      })
      .sort((first, second) => {
        const firstValue = first[filters.sort]
        const secondValue = second[filters.sort]
        const comparison =
          typeof firstValue === 'string'
            ? firstValue.localeCompare(secondValue)
            : firstValue - secondValue
        return comparison * (filters.direction === 'asc' ? 1 : -1)
      })
  }, [stations, filters])

  const summary = useMemo(
    () => ({
      total: stations.length,
      online: stations.filter((station) => station.status === 'Online').length,
      offline: stations.filter((station) => station.status === 'Offline').length,
      faulted: stations.filter((station) => station.status === 'Faulted' || station.status === 'Maintenance').length,
    }),
    [stations],
  )

  function changeFilter(name, value) {
    setFilters((current) => ({ ...current, [name]: value }))
  }

  function saveStation(station) {
    if (
      stations.some(
        (existing) =>
          existing.id.toLowerCase() === station.id.toLowerCase() &&
          existing.id !== dialogStation?.id,
      )
    ) {
      return { error: 'A station with this ID already exists.' }
    }

    const online = station.status === 'Online'
    const assignedChargers = chargers.filter((charger) => charger.stationId === dialogStation?.id)
    const activeCount = assignedChargers.filter((charger) => charger.status === 'Charging').length
    if (dialogStation && activeCount > station.chargers) {
      return { error: `The station has ${activeCount} charging chargers. Complete or reassign them before reducing the charger count.` }
    }
    if (dialogStation && station.status !== 'Online' && sessions.some(
      (session) => session.stationId === dialogStation.id && session.status === 'Ongoing',
    )) {
      return { error: 'Complete the station’s ongoing simulated sessions before changing it to a non-online status.' }
    }
    const nextStation = {
      ...station,
      activeChargers: online && dialogStation ? Math.min(dialogStation.activeChargers, station.chargers) : 0,
      energyDelivered: dialogStation?.energyDelivered ?? 0,
      todaysRevenue: dialogStation?.todaysRevenue ?? 0,
      utilization: online && station.chargers > 0 ? 50 : 0,
    }

    setStations((current) =>
      dialogStation
        ? current.map((item) => item.id === dialogStation.id ? nextStation : item)
        : [...current, nextStation],
    )
    setChargers((current) => {
      const previous = current.filter((charger) => charger.stationId === dialogStation?.id)
      const retained = previous
        .sort((a, b) => Number(b.status === 'Charging') - Number(a.status === 'Charging'))
        .slice(0, nextStation.chargers)
        .map((charger, index) => {
          if (nextStation.status === 'Offline') return { ...charger, status: 'Offline', current: 0, currentSession: '' }
          if (nextStation.status === 'Faulted' || nextStation.status === 'Maintenance') {
            return { ...charger, status: index === 0 ? 'Faulted' : 'Offline', current: 0, currentSession: '' }
          }
          if (charger.status === 'Offline' || charger.status === 'Faulted') {
            return { ...charger, status: 'Available', current: 0, currentSession: '' }
          }
          return charger
        })
      const retainedIds = new Set(retained.map((charger) => charger.id))
      const added = Array.from({ length: nextStation.chargers }, (_, index) =>
        createChargerRecord(nextStation, index + 1),
      ).filter((charger) => !retainedIds.has(charger.id))
      return current.filter((charger) => charger.stationId !== dialogStation?.id).concat(retained, added)
    })
    setDetailsStation(null)
    setDialogStation(undefined)
    return { error: '' }
  }

  function openEdit(station) {
    setDetailsStation(null)
    setDialogStation(station)
  }

  function deleteStation(station) {
    if (!window.confirm(`Delete ${station.name} (${station.id}) and its demo chargers? This cannot be undone.`)) return
    setStations((current) => current.filter((item) => item.id !== station.id))
    setChargers((current) => current.filter((charger) => charger.stationId !== station.id))
    setSessions((current) => current.filter((session) => session.stationId !== station.id))
  }

  return (
    <div className="stations-page">
      <div className="stations-page-heading">
        <PageHeader
          title="Charging Stations"
          description="Monitor and manage your EV charging network."
        />
        <button
          className="station-add-button"
          type="button"
          onClick={() => setDialogStation(null)}
        >
          <Plus size={17} aria-hidden="true" />
          Add Station
        </button>
      </div>

      <section className="station-summary-grid" aria-label="Station status summary">
        <StationSummaryCard
          label="Total Stations"
          value={summary.total}
          note="In your demo network"
          icon={MapPin}
          tone="total"
        />
        <StationSummaryCard
          label="Online Stations"
          value={summary.online}
          note="Operating normally"
          icon={CheckCircle2}
          tone="online"
        />
        <StationSummaryCard
          label="Offline Stations"
          value={summary.offline}
          note="Currently unavailable"
          icon={CircleOff}
          tone="offline"
        />
        <StationSummaryCard
          label="Faulted / Maintenance"
          value={summary.faulted}
          note="Require attention"
          icon={AlertTriangle}
          tone="faulted"
        />
      </section>

      <section className="stations-table-card" aria-label="Charging station list">
        <div className="stations-list-heading">
          <div>
            <h2>Station network</h2>
            <p>
              Showing <strong>{formatNumber(filteredStations.length)}</strong> of{' '}
              <strong>{formatNumber(stations.length)}</strong> stations
            </p>
          </div>
          <span className="station-data-label">DEMO DATA</span>
        </div>

        <div className="station-filters">
          <label className="station-search">
            <Search size={15} aria-hidden="true" />
            <input
              type="search"
              value={filters.search}
              onChange={(event) => changeFilter('search', event.target.value)}
              placeholder="Search name, ID, or location"
              aria-label="Search stations by name, ID, or location"
            />
          </label>
          <label className="station-select-label">
            <span className="visually-hidden">Filter by station status</span>
            <select
              value={filters.status}
              onChange={(event) => changeFilter('status', event.target.value)}
            >
              <option>All statuses</option>
              {stationStatusOptions.map((status) => <option key={status}>{status}</option>)}
            </select>
          </label>
          <label className="station-select-label">
            <span className="visually-hidden">Filter by location</span>
            <select
              value={filters.location}
              onChange={(event) => changeFilter('location', event.target.value)}
            >
              <option>All locations</option>
              {locations.map((location) => <option key={location}>{location}</option>)}
            </select>
          </label>
          <label className="station-select-label station-sort-select">
            <span className="visually-hidden">Sort stations</span>
            <select
              value={filters.sort}
              onChange={(event) => changeFilter('sort', event.target.value)}
            >
              {sortOptions.map((option) => (
                <option value={option.value} key={option.value}>
                  Sort: {option.label}
                </option>
              ))}
            </select>
          </label>
          <button
            className="station-sort-direction"
            type="button"
            aria-label={`Sort ${filters.direction === 'asc' ? 'descending' : 'ascending'}`}
            title={`Sort ${filters.direction === 'asc' ? 'descending' : 'ascending'}`}
            onClick={() => changeFilter('direction', filters.direction === 'asc' ? 'desc' : 'asc')}
          >
            {filters.direction === 'asc'
              ? <ArrowUpWideNarrow size={16} aria-hidden="true" />
              : <ArrowDownWideNarrow size={16} aria-hidden="true" />}
          </button>
          <button
            className="station-reset-button"
            type="button"
            onClick={() => setFilters(DEFAULT_FILTERS)}
            disabled={
              filters.search === DEFAULT_FILTERS.search &&
              filters.status === DEFAULT_FILTERS.status &&
              filters.location === DEFAULT_FILTERS.location &&
              filters.sort === DEFAULT_FILTERS.sort &&
              filters.direction === DEFAULT_FILTERS.direction
            }
          >
            <RotateCcw size={14} aria-hidden="true" />
            Reset filters
          </button>
        </div>

        {filteredStations.length > 0 ? (
          <div className="stations-table-scroll">
            <table className="stations-table">
              <thead>
                <tr>
                  <th scope="col">Station</th>
                  <th scope="col">Location</th>
                  <th scope="col">Chargers</th>
                  <th scope="col">Active</th>
                  <th scope="col">Energy delivered</th>
                  <th scope="col">Today’s revenue</th>
                  <th scope="col">Utilization</th>
                  <th scope="col">Status</th>
                  <th scope="col"><span className="visually-hidden">Actions</span></th>
                </tr>
              </thead>
              <tbody>
                {filteredStations.map((station) => (
                  <tr key={station.id}>
                    <td className="station-name-cell">
                      <strong>{station.name}</strong>
                      <span>{station.id}</span>
                    </td>
                    <td>
                      <span className="station-location-cell">
                        <MapPin size={13} aria-hidden="true" />
                        {station.location}
                      </span>
                    </td>
                    <td>{formatNumber(station.chargers)}</td>
                    <td>{formatNumber(station.activeChargers)}</td>
                    <td>{formatEnergy(station.energyDelivered)}</td>
                    <td>{formatCurrency(station.todaysRevenue)}</td>
                    <td>
                      <span className="station-utilization-cell">
                        <span
                          className="station-utilization-track"
                          role="progressbar"
                          aria-label={`${station.name} utilization`}
                          aria-valuemin={0}
                          aria-valuemax={100}
                          aria-valuenow={station.utilization}
                        >
                          <span style={{ width: `${station.utilization}%` }} />
                        </span>
                        <strong>{station.utilization}%</strong>
                      </span>
                    </td>
                    <td><StationStatusBadge status={station.status} /></td>
                    <td>
                      <div className="station-row-actions">
                        <button type="button" onClick={() => setDetailsStation(station)}>View</button>
                        <Link className="station-open-link" to={`/stations/${station.id}`}>Open</Link>
                        <button type="button" onClick={() => openEdit(station)}>Edit</button>
                        <button type="button" aria-label={`Delete ${station.id}`} onClick={() => deleteStation(station)}>
                          <Trash2 size={13} aria-hidden="true" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="stations-empty-state">
            <span><Search size={19} aria-hidden="true" /></span>
            <h3>No stations found</h3>
            <p>Try a different search or reset the filters to see all stations.</p>
            <button type="button" onClick={() => setFilters(DEFAULT_FILTERS)}>Reset filters</button>
          </div>
        )}
      </section>

      <p className="stations-demo-note">
        Station metrics are illustrative frontend demo data and do not represent live equipment.
      </p>

      {dialogStation !== undefined && (
        <StationDialog
          key={dialogStation?.id ?? 'new'}
          station={dialogStation}
          onClose={closeForm}
          onSave={saveStation}
        />
      )}
      {detailsStation && (
        <StationDetails
          station={detailsStation}
          onClose={() => setDetailsStation(null)}
          onEdit={() => openEdit(detailsStation)}
        />
      )}
    </div>
  )
}

export default ChargingStationsPage
