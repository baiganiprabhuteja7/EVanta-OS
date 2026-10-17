import { lazy, Suspense } from 'react'
import {
  Activity,
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  BatteryCharging,
  CheckCircle2,
  CircleAlert,
  Clock3,
  IndianRupee,
  MapPin,
  PlugZap,
  RefreshCw,
  Zap,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import {
  formatCurrency,
  formatEnergy,
  formatNumber,
  formatSessionTime,
} from '../../utils/formatters.js'

const AsyncChartPanel = lazy(() =>
  import('./DashboardCharts.jsx').then((module) => ({
    default: module.ChartPanel,
  })),
)
const AsyncChargerStatusChart = lazy(() =>
  import('./DashboardCharts.jsx').then((module) => ({
    default: module.ChargerStatusChart,
  })),
)

function ChartPanel({ type, ...props }) {
  return (
    <Suspense fallback={<div className="dashboard-card chart-loading">Loading chart…</div>}>
      <AsyncChartPanel type={type} {...props} />
    </Suspense>
  )
}

function ChargerStatusChart(props) {
  return (
    <Suspense fallback={<div className="dashboard-card chart-loading">Loading chart…</div>}>
      <AsyncChargerStatusChart {...props} />
    </Suspense>
  )
}

const metricIcons = {
  stations: MapPin,
  chargers: PlugZap,
  energy: Zap,
  revenue: IndianRupee,
  sessions: Activity,
  utilization: BatteryCharging,
}

function MetricCard({ metric }) {
  const Icon = metricIcons[metric.icon]
  const positive = metric.change >= 0

  return (
    <article className="metric-card">
      <div className="metric-card-top">
        <span className={`metric-icon metric-icon-${metric.icon}`} aria-hidden="true">
          <Icon size={18} strokeWidth={1.8} />
        </span>
        {typeof metric.change === 'number' && (
          <span className={`metric-change ${positive ? 'is-positive' : 'is-negative'}`}>
            {positive ? (
              <ArrowUpRight size={13} aria-hidden="true" />
            ) : (
              <ArrowDownRight size={13} aria-hidden="true" />
            )}
            {Math.abs(metric.change)}%
            <span className="visually-hidden"> versus previous period</span>
          </span>
        )}
      </div>
      <p className="metric-label">{metric.label}</p>
      <p className="metric-value">{metric.value}</p>
      <p className="metric-context">{metric.context}</p>
    </article>
  )
}

function StatusBadge({ status }) {
  const statusClass = status.toLowerCase().replaceAll(' ', '-')
  return (
    <span className={`status-badge status-badge-${statusClass}`}>
      <span aria-hidden="true" />
      {status}
    </span>
  )
}

function StationPerformance({ stations, rangeLabel }) {
  return (
    <section className="dashboard-card table-card">
      <div className="card-heading section-card-heading">
        <div>
          <h2>Station performance</h2>
          <p>Network activity · {rangeLabel.toLowerCase()}</p>
        </div>
        <Link className="text-action" to="/stations">
          View All Stations <span aria-hidden="true">→</span>
        </Link>
      </div>
      <div className="table-scroll">
        <table className="dashboard-table stations-table">
          <thead>
            <tr>
              <th scope="col">Station</th>
              <th scope="col">Location</th>
              <th scope="col">Total chargers</th>
              <th scope="col">Active</th>
              <th scope="col">Energy delivered</th>
              <th scope="col">Revenue</th>
              <th scope="col">Status</th>
            </tr>
          </thead>
          <tbody>
            {stations.map((station) => (
              <tr key={station.id}>
                <td>
                  <span className="table-primary">{station.name}</span>
                  <span className="table-secondary">{station.id}</span>
                </td>
                <td>{station.location}</td>
                <td>{formatNumber(station.totalChargers)}</td>
                <td>{formatNumber(station.activeChargers)}</td>
                <td>{formatEnergy(station.energy)}</td>
                <td>{formatCurrency(station.revenue)}</td>
                <td><StatusBadge status={station.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function RecentSessions({ sessions }) {
  return (
    <section className="dashboard-card table-card">
      <div className="card-heading section-card-heading">
        <div>
          <h2>Recent charging sessions</h2>
          <p>Latest session activity from the illustrative demo network</p>
        </div>
        <Link className="text-action" to="/sessions">
          View All Sessions <span aria-hidden="true">→</span>
        </Link>
      </div>
      <div className="table-scroll">
        <table className="dashboard-table sessions-table">
          <thead>
            <tr>
              <th scope="col">Session ID</th>
              <th scope="col">Station</th>
              <th scope="col">Charger</th>
              <th scope="col">Start time</th>
              <th scope="col">Energy delivered</th>
              <th scope="col">Amount</th>
              <th scope="col">Status</th>
            </tr>
          </thead>
          <tbody>
            {sessions.map((session) => (
              <tr key={session.id}>
                <td className="session-id">{session.id}</td>
                <td>{session.station}</td>
                <td>{session.charger}</td>
                <td>{formatSessionTime(session.startedAt)}</td>
                <td>{formatEnergy(session.energy)}</td>
                <td>{formatCurrency(session.amount)}</td>
                <td><StatusBadge status={session.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

const alertIcons = {
  critical: CircleAlert,
  warning: AlertTriangle,
  success: CheckCircle2,
  info: Activity,
}

function OperationalAlerts({ alerts }) {
  return (
    <section className="dashboard-card alerts-card">
      <div className="card-heading">
        <div>
          <h2>Alerts & operational insights</h2>
          <p>Simulated demo events · no live equipment monitoring</p>
        </div>
        <span className="simulated-badge">DEMO</span>
      </div>
      {alerts.length ? (
        <ul className="alert-list">
          {alerts.map((alert) => {
            const Icon = alertIcons[alert.severity]
            return (
              <li className={`alert-item alert-${alert.severity}`} key={alert.id}>
                <span className="alert-icon" aria-hidden="true"><Icon size={16} /></span>
                <div className="alert-content">
                  <div className="alert-title-row">
                    <strong>{alert.title}</strong>
                    <span className="alert-time">
                      <Clock3 size={11} aria-hidden="true" />
                      {alert.time}
                    </span>
                  </div>
                  <p>{alert.description}</p>
                </div>
              </li>
            )
          })}
        </ul>
      ) : (
        <div className="alerts-empty">
          <CheckCircle2 size={19} aria-hidden="true" />
          <span>No simulated alerts at this time.</span>
        </div>
      )}
    </section>
  )
}

const quickActions = [
  { label: 'View Stations', to: '/stations', icon: MapPin },
  { label: 'View Chargers', to: '/chargers', icon: PlugZap },
  { label: 'Energy Monitoring', to: '/energy', icon: Zap },
  { label: 'Business Analytics', to: '/analytics', icon: Activity },
]

function QuickActions() {
  return (
    <section className="dashboard-card quick-actions-card">
      <div className="card-heading">
        <div>
          <h2>Quick actions</h2>
          <p>Jump to a workspace</p>
        </div>
      </div>
      <nav className="quick-actions-list" aria-label="Dashboard quick actions">
        {quickActions.map(({ label, to, icon: Icon }) => (
          <Link className="quick-action-link" to={to} key={to}>
            <Icon size={16} aria-hidden="true" />
            <span>{label}</span>
            <span className="quick-action-arrow" aria-hidden="true">→</span>
          </Link>
        ))}
      </nav>
    </section>
  )
}

function RefreshButton({ refreshing, onClick }) {
  return (
    <button
      className="dashboard-refresh-button"
      type="button"
      onClick={onClick}
      disabled={refreshing}
      aria-label={refreshing ? 'Refreshing demo data' : 'Refresh demo dashboard data'}
    >
      <RefreshCw size={15} aria-hidden="true" />
      <span>{refreshing ? 'Refreshing' : 'Refresh'}</span>
    </button>
  )
}

export {
  ChartPanel,
  ChargerStatusChart,
  MetricCard,
  OperationalAlerts,
  QuickActions,
  RecentSessions,
  RefreshButton,
  StationPerformance,
  StatusBadge,
}
