import { useMemo, useState } from 'react'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Download, IndianRupee, Percent, TrendingUp, Users, Zap } from 'lucide-react'
import PageHeader from '../components/common/PageHeader.jsx'
import { useAppData } from '../context/useAppData.js'
import { downloadCsv } from '../utils/csv.js'
import { formatCurrency, formatNumber, formatShortDate } from '../utils/formatters.js'
import './BusinessAnalyticsPage.css'

const rangeOptions = [
  { value: 7, label: 'Last 7 days' },
  { value: 30, label: 'Last 30 days' },
]
const chartColors = ['#c4e16b', '#79add5', '#d4a879', '#ba91ce', '#81c3aa', '#e28e7c', '#90a8db', '#dabd71']
const exportColumns = [
  { label: 'Session ID', value: (row) => row.id },
  { label: 'Date', value: (row) => row.startedAt },
  { label: 'Station', value: (row) => row.station },
  { label: 'Station ID', value: (row) => row.stationId },
  { label: 'Charger type', value: (row) => row.chargerType },
  { label: 'Energy kWh', value: (row) => row.energy },
  { label: 'Revenue INR', value: (row) => row.amount },
  { label: 'Status', value: (row) => row.status },
]

function AnalyticsMetric({ icon: Icon, label, value, note, tone = '' }) {
  return <article className={`analytics-metric ${tone}`}><span><Icon size={16} /></span><small>{label}</small><strong>{value}</strong><p>{note}</p></article>
}

function AnalyticsChart({ title, subtitle, children, className = '' }) {
  return <section className={`analytics-chart ${className}`}><div className="analytics-chart-heading"><div><h2>{title}</h2><p>{subtitle}</p></div></div>{children}</section>
}

function BusinessAnalyticsPage() {
  const { stations, chargers, sessions, preferences } = useAppData()
  const [range, setRange] = useState(30)
  const [stationFilter, setStationFilter] = useState('All stations')
  const [todaySnapshot] = useState(() => new Date())
  const filteredSessions = useMemo(() => {
    const today = new Date(todaySnapshot.getTime())
    today.setHours(23, 59, 59, 999)
    const earliest = new Date(today)
    earliest.setDate(earliest.getDate() - range + 1)
    return sessions.filter((session) => {
      const started = new Date(session.startedAt)
      return started >= earliest && started <= today &&
        (stationFilter === 'All stations' || session.stationId === stationFilter)
    })
  }, [sessions, range, stationFilter, todaySnapshot])

  const completed = useMemo(
    () => filteredSessions.filter((session) => session.status === 'Completed'),
    [filteredSessions],
  )
  const revenue = completed.reduce((total, session) => total + session.amount, 0)
  const energyCost = completed.reduce((total, session) => total + session.energy * preferences.electricityCostPerKwh, 0)
  const grossMargin = revenue - energyCost
  const marginPercent = revenue > 0 ? grossMargin / revenue * 100 : 0
  const averageRevenue = completed.length ? revenue / completed.length : 0
  const applicableChargers = stationFilter === 'All stations'
    ? chargers
    : chargers.filter((charger) => charger.stationId === stationFilter)
  const chargerUtilization = applicableChargers.length
    ? applicableChargers.filter((charger) => charger.status === 'Charging').length / applicableChargers.length * 100
    : 0
  const monthlyScale = 30 / range
  const estimatedMonthlyGrossMargin = grossMargin * monthlyScale
  const annualNetOperatingBenefit = (estimatedMonthlyGrossMargin - preferences.monthlyOperatingCosts) * 12
  const roi = preferences.initialInvestment > 0 ? annualNetOperatingBenefit / preferences.initialInvestment * 100 : null

  const daily = useMemo(() => {
    const result = new Map()
    filteredSessions.forEach((session) => {
      const key = session.startedAt.slice(0, 10)
      const row = result.get(key) ?? { date: key, revenue: 0, energyCost: 0, sessions: 0 }
      if (session.status === 'Completed') {
        row.revenue += session.amount
        row.energyCost += session.energy * preferences.electricityCostPerKwh
      }
      row.sessions += 1
      result.set(key, row)
    })
    return [...result.values()].sort((a, b) => a.date.localeCompare(b.date)).map((row) => ({ ...row, label: formatShortDate(row.date) }))
  }, [filteredSessions, preferences.electricityCostPerKwh])

  const stationPerformance = useMemo(() => {
    const rows = new Map(stations.map((station) => [station.id, { station: station.name, stationId: station.id, revenue: 0, cost: 0, energy: 0, sessions: 0 }]))
    completed.forEach((session) => {
      const row = rows.get(session.stationId)
      if (!row) return
      row.revenue += session.amount
      row.energy += session.energy
      row.cost += session.energy * preferences.electricityCostPerKwh
      row.sessions += 1
    })
    return [...rows.values()].filter((row) => row.sessions).sort((a, b) => b.revenue - a.revenue)
  }, [stations, completed, preferences.electricityCostPerKwh])

  const byChargerType = ['AC', 'DC'].map((type) => ({
    type,
    sessions: filteredSessions.filter((session) => session.chargerType === type).length,
    energy: filteredSessions.filter((session) => session.chargerType === type && session.status === 'Completed')
      .reduce((sum, session) => sum + session.energy, 0),
  }))
  const peakHours = filteredSessions.reduce((hours, session) => {
    const startHour = new Date(session.startedAt).getHours()
    if (startHour >= 17 && startHour < 22) hours.peak += session.durationMinutes / 60
    else hours.offPeak += session.durationMinutes / 60
    return hours
  }, { peak: 0, offPeak: 0 })
  const dailyCapacityHours = chargers.length * range * 5
  const offPeakCapacityHours = chargers.length * range * 19
  const peakUtilization = dailyCapacityHours ? peakHours.peak / dailyCapacityHours * 100 : 0
  const offPeakUtilization = offPeakCapacityHours ? peakHours.offPeak / offPeakCapacityHours * 100 : 0
  const peakOffPeakData = [
    { period: 'Peak · 17:00–22:00', utilization: Number(peakUtilization.toFixed(2)) },
    { period: 'Off-peak · rest of day', utilization: Number(offPeakUtilization.toFixed(2)) },
  ]

  return <div className="analytics-page">
    <div className="analytics-page-header"><PageHeader title="Business Analytics" description="Transparent revenue, energy cost, and operating estimates from simulated session records." />
      <div className="analytics-controls"><label>Reporting period<select value={range} onChange={(event) => setRange(Number(event.target.value))}>{rangeOptions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
        <label>Station<select value={stationFilter} onChange={(event) => setStationFilter(event.target.value)}><option>All stations</option>{stations.map((station) => <option key={station.id} value={station.id}>{station.name}</option>)}</select></label>
        <button type="button" className="analytics-export-button" onClick={() => downloadCsv('evanta-filtered-analytics.csv', filteredSessions, exportColumns)}><Download size={14} />Export filtered CSV</button>
      </div>
    </div>
    <div className="analytics-demo-note"><TrendingUp size={14} /><span>Demo analysis only. Revenue includes completed session charges; energy costs use the configured per-kWh assumption.</span></div>
    <section className="analytics-metrics-grid" aria-label="Business performance metrics">
      <AnalyticsMetric icon={IndianRupee} label="Total Revenue" value={formatCurrency(revenue, true)} note="Completed sessions in period" />
      <AnalyticsMetric icon={Zap} label="Estimated Energy Cost" value={formatCurrency(energyCost, true)} note={`Energy × ₹${preferences.electricityCostPerKwh.toFixed(2)} / kWh`} />
      <AnalyticsMetric icon={TrendingUp} label="Estimated Gross Margin" value={formatCurrency(grossMargin, true)} note="Revenue − estimated energy cost" tone={grossMargin < 0 ? 'is-negative' : ''} />
      <AnalyticsMetric icon={Percent} label="Gross Margin" value={`${marginPercent.toFixed(1)}%`} note="Gross margin ÷ revenue" />
      <AnalyticsMetric icon={Users} label="Completed Sessions" value={formatNumber(completed.length)} note={`${filteredSessions.length} total sessions in scope`} />
      <AnalyticsMetric icon={IndianRupee} label="Average Revenue / Session" value={formatCurrency(averageRevenue)} note="Revenue ÷ completed sessions" />
      <AnalyticsMetric icon={Zap} label="Estimated Charger Utilization" value={`${chargerUtilization.toFixed(1)}%`} note="Chargers currently in simulated sessions" />
      <AnalyticsMetric icon={TrendingUp} label="Estimated Annual ROI" value={roi === null ? 'Not available' : `${roi.toFixed(1)}%`} note={roi === null ? 'Enter an initial investment' : 'Annual operating benefit ÷ investment'} tone={roi !== null && roi < 0 ? 'is-negative' : ''} />
    </section>

    <div className="analytics-chart-grid">
      <AnalyticsChart title="Revenue trends" subtitle="Completed-session revenue by day (₹)" className="analytics-chart-wide">
        {daily.length ? <ResponsiveContainer width="100%" height={260}><BarChart data={daily} margin={{ top: 8, right: 9, left: -10, bottom: 0 }}>
          <CartesianGrid stroke="#293740" strokeDasharray="3 5" vertical={false} /><XAxis dataKey="label" tick={{ fill: '#87969a', fontSize: 9 }} tickLine={false} axisLine={{ stroke: '#36444b' }} /><YAxis tick={{ fill: '#87969a', fontSize: 9 }} tickLine={false} axisLine={false} />
          <Tooltip formatter={(value) => [formatCurrency(value), 'Revenue']} contentStyle={{ background: '#18232c', border: '1px solid #3a4a52', borderRadius: 8, color: '#edf2ed', fontSize: 10 }} /><Bar dataKey="revenue" name="Revenue" fill="#c4e16b" radius={[4, 4, 0, 0]} />
        </BarChart></ResponsiveContainer> : <div className="analytics-empty-state">No completed revenue in this date range.</div>}
      </AnalyticsChart>
      <AnalyticsChart title="Revenue vs energy cost" subtitle="Completed-session financial comparison (₹)">
        {daily.length ? <ResponsiveContainer width="100%" height={260}><AreaChart data={daily} margin={{ top: 8, right: 9, left: -10, bottom: 0 }}>
          <CartesianGrid stroke="#293740" strokeDasharray="3 5" vertical={false} /><XAxis dataKey="label" tick={{ fill: '#87969a', fontSize: 9 }} tickLine={false} axisLine={{ stroke: '#36444b' }} /><YAxis tick={{ fill: '#87969a', fontSize: 9 }} tickLine={false} axisLine={false} />
          <Tooltip formatter={(value) => [formatCurrency(value)]} contentStyle={{ background: '#18232c', border: '1px solid #3a4a52', borderRadius: 8, color: '#edf2ed', fontSize: 10 }} /><Legend wrapperStyle={{ color: '#aab7b8', fontSize: 9 }} />
          <Area type="monotone" dataKey="revenue" name="Revenue" stroke="#c4e16b" fill="#c4e16b" fillOpacity={0.13} /><Area type="monotone" dataKey="energyCost" name="Energy cost" stroke="#79add5" fill="#79add5" fillOpacity={0.11} />
        </AreaChart></ResponsiveContainer> : <div className="analytics-empty-state">No session records to compare.</div>}
      </AnalyticsChart>
      <AnalyticsChart title="Revenue by station" subtitle="Completed-session revenue in selected range">
        {stationPerformance.length ? <ResponsiveContainer width="100%" height={270}><BarChart data={stationPerformance} layout="vertical" margin={{ top: 4, right: 12, left: 20, bottom: 0 }}>
          <CartesianGrid stroke="#293740" strokeDasharray="3 5" horizontal={false} /><XAxis type="number" tick={{ fill: '#87969a', fontSize: 9 }} tickLine={false} axisLine={{ stroke: '#36444b' }} /><YAxis type="category" dataKey="station" width={120} tick={{ fill: '#aab7b8', fontSize: 9 }} tickLine={false} axisLine={false} />
          <Tooltip formatter={(value) => [formatCurrency(value), 'Revenue']} contentStyle={{ background: '#18232c', border: '1px solid #3a4a52', borderRadius: 8, color: '#edf2ed', fontSize: 10 }} /><Bar dataKey="revenue" name="Revenue" fill="#9bc77e" radius={[0, 4, 4, 0]} />
        </BarChart></ResponsiveContainer> : <div className="analytics-empty-state">No station revenue is available in this period.</div>}
      </AnalyticsChart>
      <AnalyticsChart title="Sessions by charger type" subtitle="Count of session records, by AC and DC">
        <ResponsiveContainer width="100%" height={270}><PieChart><Pie data={byChargerType} dataKey="sessions" nameKey="type" innerRadius={62} outerRadius={90} paddingAngle={4} stroke="#18232c">
          {byChargerType.map((entry, index) => <Cell key={entry.type} fill={chartColors[index]} />)}
        </Pie><Tooltip formatter={(value) => [`${value} sessions`]} contentStyle={{ background: '#18232c', border: '1px solid #3a4a52', borderRadius: 8, color: '#edf2ed', fontSize: 10 }} /><Legend wrapperStyle={{ color: '#aab7b8', fontSize: 10 }} /></PieChart></ResponsiveContainer>
      </AnalyticsChart>
      <AnalyticsChart title="Peak vs off-peak utilization" subtitle="Estimated session charger-hours / available charger-hours">
        <ResponsiveContainer width="100%" height={250}><BarChart data={peakOffPeakData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
          <CartesianGrid stroke="#293740" strokeDasharray="3 5" vertical={false} /><XAxis dataKey="period" tick={{ fill: '#aab7b8', fontSize: 9 }} tickLine={false} axisLine={{ stroke: '#36444b' }} /><YAxis unit="%" tick={{ fill: '#87969a', fontSize: 9 }} tickLine={false} axisLine={false} />
          <Tooltip formatter={(value) => [`${Number(value).toFixed(2)}%`, 'Estimated utilization']} contentStyle={{ background: '#18232c', border: '1px solid #3a4a52', borderRadius: 8, color: '#edf2ed', fontSize: 10 }} /><Bar dataKey="utilization" name="Utilization" fill="#79add5" radius={[5, 5, 0, 0]} />
        </BarChart></ResponsiveContainer>
      </AnalyticsChart>
      <AnalyticsChart title="Monthly performance comparison" subtitle="Revenue and estimated energy cost, by month">
        <ResponsiveContainer width="100%" height={250}><LineChart data={Object.values(daily.reduce((months, row) => {
          const month = row.date.slice(0, 7)
          const current = months[month] ?? { month, revenue: 0, energyCost: 0 }
          current.revenue += row.revenue
          current.energyCost += row.energyCost
          months[month] = current
          return months
        }, {}))} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
          <CartesianGrid stroke="#293740" strokeDasharray="3 5" vertical={false} /><XAxis dataKey="month" tick={{ fill: '#aab7b8', fontSize: 9 }} tickLine={false} axisLine={{ stroke: '#36444b' }} /><YAxis tick={{ fill: '#87969a', fontSize: 9 }} tickLine={false} axisLine={false} />
          <Tooltip formatter={(value) => [formatCurrency(value)]} contentStyle={{ background: '#18232c', border: '1px solid #3a4a52', borderRadius: 8, color: '#edf2ed', fontSize: 10 }} /><Legend wrapperStyle={{ color: '#aab7b8', fontSize: 9 }} />
          <Line type="monotone" dataKey="revenue" name="Revenue" stroke="#c4e16b" strokeWidth={2} /><Line type="monotone" dataKey="energyCost" name="Energy cost" stroke="#79add5" strokeWidth={2} />
        </LineChart></ResponsiveContainer>
      </AnalyticsChart>
    </div>
    <section className="analytics-assumptions"><h2>Estimate assumptions</h2><ul>
      <li><strong>Revenue</strong> = sum of completed session charges in the selected period.</li>
      <li><strong>Energy cost</strong> = completed session energy × configured ₹{preferences.electricityCostPerKwh.toFixed(2)} per kWh.</li>
      <li><strong>Gross margin</strong> = revenue − estimated energy cost. This is not net profit.</li>
      <li><strong>ROI projection</strong> annualizes the selected period to 30 days, subtracts configured monthly operating expenses of {formatCurrency(preferences.monthlyOperatingCosts)}, and divides the resulting annual operating benefit by the configured initial investment of {formatCurrency(preferences.initialInvestment)}. It is an estimate, not a realized return.</li>
      <li>Peak session hours are 17:00–22:00 local time. Utilization is estimated from recorded session duration and charger-hours in the period.</li>
    </ul></section>
  </div>
}

export default BusinessAnalyticsPage
