import { useMemo, useState } from 'react'
import { CalendarDays, Database } from 'lucide-react'
import { useAppData } from '../context/useAppData.js'
import {
  createDashboardData,
  getDateRangeMetrics,
  getStationPerformance,
  getTodayMetrics,
} from '../data/dashboardData.js'
import {
  formatClockTime,
  formatCurrency,
  formatEnergy,
  formatNumber,
} from '../utils/formatters.js'
import {
  ChartPanel,
  ChargerStatusChart,
  MetricCard,
  OperationalAlerts,
  QuickActions,
  RecentSessions,
  RefreshButton,
  StationPerformance,
} from '../components/dashboard/DashboardWidgets.jsx'

const RANGE_OPTIONS = [
  { value: 'today', label: 'Today' },
  { value: '7d', label: 'Last 7 Days' },
  { value: '30d', label: 'Last 30 Days' },
]

const percentChange = (current, previous) =>
  previous > 0 ? Math.round(((current - previous) / previous) * 100) : null

function DashboardPageContent() {
  const { stations, chargers, sessions } = useAppData()
  const [range, setRange] = useState('7d')
  const [refreshCount, setRefreshCount] = useState(0)
  const [lastRefreshed, setLastRefreshed] = useState(null)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const data = useMemo(() => {
    const generated = createDashboardData(refreshCount)
    const normalizedSessions = sessions.map((session) => ({
      ...session,
      date: session.startedAt.slice(0, 10),
      startedAt: new Date(session.startedAt),
      charger: session.chargerId,
      status: session.status === 'Ongoing' ? 'In progress' : session.status,
      amount: session.status === 'Completed' ? session.amount : 0,
    }))
    const byDate = new Map()
    normalizedSessions.forEach((session) => {
      const daily = byDate.get(session.date) ?? { date: session.date, energy: 0, revenue: 0, sessions: 0 }
      daily.energy += session.energy
      daily.revenue += session.amount
      daily.sessions += 1
      byDate.set(session.date, daily)
    })
    const statusInfo = [
      { key: 'charging', label: 'Active', color: '#c4e16b' },
      { key: 'available', label: 'Available', color: '#65818b' },
      { key: 'offline', label: 'Offline', color: '#e6ad64' },
      { key: 'faulted', label: 'Faulted', color: '#d5786d' },
    ]
    const statusCounts = statusInfo.map((status) => ({
      ...status,
      count: chargers.filter((charger) => charger.status.toLowerCase() === status.key).length,
    }))
    return {
      ...generated,
      stations,
      chargers: chargers.map((charger) => ({ ...charger, status: charger.status.toLowerCase() })),
      chargerStatus: statusCounts,
      sessions: normalizedSessions,
      dailyMetrics: [...byDate.values()].sort((a, b) => a.date.localeCompare(b.date)),
    }
  }, [refreshCount, stations, chargers, sessions])
  const period = useMemo(
    () => getDateRangeMetrics(data.dailyMetrics, range),
    [data.dailyMetrics, range],
  )
  const todayMetrics = getTodayMetrics(data)
  const previousDayRevenue =
    getDateRangeMetrics(data.dailyMetrics, 'today').previousRevenue
  const totalChargers = data.chargers.length
  const activeChargers = data.chargers.filter(
    (charger) => charger.status === 'charging' || charger.status === 'available',
  ).length
  const chargingCount =
    data.chargerStatus.find((status) => status.key === 'charging')?.count ?? 0
  const averageUtilization = totalChargers
    ? Math.round((chargingCount / totalChargers) * 100)
    : 0
  const rangeLabel = RANGE_OPTIONS.find((option) => option.value === range)?.label
  const rangeDateKeys = new Set(period.current.map((day) => day.date))
  const stationPerformance = getStationPerformance(
    data.stations,
    data.chargers,
    data.sessions,
    rangeDateKeys,
  )
  const recentSessions = [...data.sessions]
    .sort((a, b) => b.startedAt - a.startedAt)
    .slice(0, 7)

  const metrics = [
    {
      label: 'Total Charging Stations',
      value: formatNumber(data.stations.length),
      context: 'Across the illustrative network',
      icon: 'stations',
    },
    {
      label: 'Active Chargers',
      value: formatNumber(activeChargers),
      context: `of ${formatNumber(totalChargers)} chargers available or charging`,
      icon: 'chargers',
    },
    {
      label: 'Total Energy Delivered (kWh)',
      value: formatNumber(period.energy),
      context: `${rangeLabel} · ${formatEnergy(period.energy)} delivered`,
      change: percentChange(period.energy, period.previousEnergy),
      icon: 'energy',
    },
    {
      label: "Today's Revenue (₹)",
      value: formatCurrency(todayMetrics.revenue, true),
      context: `${formatNumber(todayMetrics.sessions)} simulated sessions today`,
      change: percentChange(todayMetrics.revenue, previousDayRevenue),
      icon: 'revenue',
    },
    {
      label: 'Total Charging Sessions',
      value: formatNumber(period.sessions),
      context: `${rangeLabel} · includes active demo session`,
      change: percentChange(period.sessions, period.previousSessions),
      icon: 'sessions',
    },
    {
      label: 'Average Charger Utilization',
      value: `${averageUtilization}%`,
      context: `${formatNumber(chargingCount)} of ${formatNumber(totalChargers)} chargers charging`,
      icon: 'utilization',
    },
  ]

  function refreshDashboard() {
    if (isRefreshing) return
    setIsRefreshing(true)
    window.setTimeout(() => {
      setRefreshCount((count) => count + 1)
      setLastRefreshed(new Date())
      setIsRefreshing(false)
    }, 350)
  }

  return (
    <div className="dashboard-page">
      <header className="dashboard-header">
        <div className="dashboard-header-copy">
          <p className="dashboard-eyebrow">EVanta OS / Overview</p>
          <h1>Dashboard</h1>
          <p>Charging network performance, energy delivery, and station operations.</p>
        </div>
        <div className="dashboard-controls">
          <span className="demo-indicator">
            <Database size={13} aria-hidden="true" />
            Illustrative demo data
          </span>
          <label className="range-select-wrap">
            <CalendarDays size={15} aria-hidden="true" />
            <span className="visually-hidden">Dashboard date range</span>
            <select value={range} onChange={(event) => setRange(event.target.value)}>
              {RANGE_OPTIONS.map((option) => (
                <option value={option.value} key={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <RefreshButton refreshing={isRefreshing} onClick={refreshDashboard} />
        </div>
      </header>

      <div className="dashboard-meta" aria-live="polite">
        <span>Showing {rangeLabel?.toLowerCase()} performance</span>
        {lastRefreshed && (
          <span>Demo data refreshed at {formatClockTime(lastRefreshed)}</span>
        )}
      </div>

      <section className="metrics-grid" aria-label="Key performance indicators">
        {metrics.map((metric) => <MetricCard key={metric.label} metric={metric} />)}
      </section>

      <section className="dashboard-charts" aria-label="Dashboard analytics">
        <ChartPanel
          type="energy"
          data={period.current}
          summary={formatEnergy(period.energy)}
        />
        <ChartPanel
          type="revenue"
          data={period.current}
          summary={formatCurrency(period.revenue)}
        />
        <ChartPanel
          type="sessions"
          data={period.current}
          summary={formatNumber(period.sessions)}
        />
        <ChargerStatusChart statuses={data.chargerStatus} total={totalChargers} />
      </section>

      <StationPerformance stations={stationPerformance} rangeLabel={rangeLabel} />
      <RecentSessions sessions={recentSessions} />

      <section className="dashboard-bottom-grid" aria-label="Alerts and quick actions">
        <OperationalAlerts alerts={data.alerts} />
        <QuickActions />
      </section>
    </div>
  )
}

export default DashboardPageContent
