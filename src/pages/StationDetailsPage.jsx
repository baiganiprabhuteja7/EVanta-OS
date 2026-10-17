import { Link, Navigate, useParams } from 'react-router-dom'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { ArrowLeft, BatteryCharging, MapPin, Zap } from 'lucide-react'
import PageHeader from '../components/common/PageHeader.jsx'
import StationStatusBadge from '../components/common/StationStatusBadge.jsx'
import { useAppData } from '../context/useAppData.js'
import { energyHistory } from '../data/energyData.js'
import { formatCurrency, formatEnergy, formatNumber, formatShortDate } from '../utils/formatters.js'
import './StationDetailsPage.css'

function StationDetailsPage() {
  const { stationId } = useParams()
  const { stations, chargers } = useAppData()
  const station = stations.find((item) => item.id.toLowerCase() === stationId?.toLowerCase())

  if (!station) return <Navigate to="/stations" replace />

  const stationChargers = chargers.filter((charger) => charger.stationId === station.id)
  const chartData = energyHistory
    .filter((record) => record.stationId === station.id)
    .slice(-14)
    .map((record) => ({ ...record, label: formatShortDate(record.date) }))
  const activeChargers = stationChargers.filter((charger) => charger.status === 'Charging').length

  return <div className="station-detail-page">
    <Link to="/stations" className="station-detail-back"><ArrowLeft size={15} />Back to stations</Link>
    <div className="station-detail-heading">
      <PageHeader title={station.name} description={`${station.id} · ${station.location}`} />
      <StationStatusBadge status={station.status} />
    </div>
    <section className="station-detail-overview">
      <article><span><MapPin size={14} />Street address</span><strong>{station.address || 'Address not provided'}</strong></article>
      <article><span><BatteryCharging size={14} />Charger availability</span><strong>{activeChargers} active / {stationChargers.length} total</strong></article>
      <article><span><Zap size={14} />Delivered energy</span><strong>{formatEnergy(station.energyDelivered)}</strong></article>
      <article><span>Today's revenue</span><strong>{formatCurrency(station.todaysRevenue)}</strong></article>
      <article><span>Estimated utilization</span><strong>{station.utilization}%</strong></article>
      <article><span>Operational status</span><strong>{station.status}</strong></article>
    </section>

    <section className="station-detail-chart-card">
      <div className="station-detail-section-heading"><div><h2>Energy consumption</h2><p>Simulated daily energy trend · latest 14 days</p></div><span>DEMO DATA</span></div>
      {chartData.length ? <ResponsiveContainer width="100%" height={270}>
        <LineChart data={chartData} margin={{ top: 8, right: 12, left: -14, bottom: 0 }}>
          <CartesianGrid stroke="#293740" strokeDasharray="3 5" vertical={false} />
          <XAxis dataKey="label" tick={{ fill: '#87969a', fontSize: 9 }} tickLine={false} axisLine={{ stroke: '#36444b' }} />
          <YAxis tick={{ fill: '#87969a', fontSize: 9 }} tickLine={false} axisLine={false} />
          <Tooltip formatter={(value) => [`${formatNumber(value)} kWh`, 'Energy']} contentStyle={{ background: '#18232c', border: '1px solid #3a4a52', borderRadius: 8, color: '#edf2ed', fontSize: 11 }} />
          <Line type="monotone" dataKey="energy" name="Energy" stroke="#c4e16b" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer> : <p className="station-detail-empty">No energy readings available for this station.</p>}
    </section>

    <section className="station-detail-chart-card station-detail-inventory">
      <div className="station-detail-section-heading"><div><h2>Charger inventory</h2><p>{formatNumber(stationChargers.length)} simulated charger records assigned to this station</p></div><span>{formatNumber(activeChargers)} CHARGING</span></div>
      {stationChargers.length ? <div className="station-detail-table-scroll"><table>
        <thead><tr><th>Charger ID</th><th>Type</th><th>Rated power</th><th>Voltage</th><th>Current</th><th>Status</th></tr></thead>
        <tbody>{stationChargers.map((charger) => <tr key={charger.id}><td>{charger.id}</td><td>{charger.type} · {charger.connector}</td><td>{charger.ratedPower} kW</td><td>{charger.voltage} V</td><td>{charger.current} A</td><td><span className={`station-detail-charger-status status-${charger.status.toLowerCase()}`}>{charger.status}</span></td></tr>)}</tbody>
      </table></div> : <p className="station-detail-empty">No chargers are assigned to this station.</p>}
    </section>

    <p className="station-detail-disclaimer">All station and energy values shown here are illustrative frontend demo data and do not represent live equipment.</p>
  </div>
}

export default StationDetailsPage
