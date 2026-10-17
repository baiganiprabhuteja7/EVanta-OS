import { useEffect, useMemo, useState } from 'react'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Activity, CircleStop, Clock3, Play, RefreshCw, Zap } from 'lucide-react'
import PageHeader from '../components/common/PageHeader.jsx'
import { useAppData } from '../context/useAppData.js'
import { energyHistory } from '../data/energyData.js'
import { formatCurrency, formatEnergy, formatNumber, formatShortDate } from '../utils/formatters.js'
import './EnergyMonitoringPage.css'

const rangeOptions = [
  { value: '1', label: 'Today' },
  { value: '7', label: 'Last 7 days' },
  { value: '30', label: 'Last 30 days' },
]

function estimatedPower(charger) {
  if (!charger) return 0
  if (charger.type === 'DC') return (charger.voltage * charger.current) / 1000
  const phaseFactor = charger.voltage >= 380 ? Math.sqrt(3) : 1
  return (phaseFactor * charger.voltage * charger.current * (charger.powerFactor ?? 0.94)) / 1000
}

function EnergyMetric({ icon: Icon, label, value, note }) {
  return <article className="energy-metric">
    <span className="energy-metric-icon" aria-hidden="true"><Icon size={17} /></span>
    <span className="energy-metric-label">{label}</span>
    <strong>{value}</strong>
    <small>{note}</small>
  </article>
}

function EnergyChartCard({ title, description, children, legend }) {
  return <section className="energy-chart-card">
    <div className="energy-chart-heading"><div><h2>{title}</h2><p>{description}</p></div>{legend}</div>
    {children}
  </section>
}

function EnergyMonitoringPage() {
  const { stations, chargers, preferences } = useAppData()
  const [range, setRange] = useState('7')
  const [stationFilter, setStationFilter] = useState('All stations')
  const [selectedChargerId, setSelectedChargerId] = useState('')
  const [simulationRunning, setSimulationRunning] = useState(false)
  const [refreshCount, setRefreshCount] = useState(0)
  const [readingTick, setReadingTick] = useState(0)
  const [measurementTime, setMeasurementTime] = useState(() => new Date())

  const activeChargers = useMemo(() => chargers.filter((charger) => charger.status === 'Charging'), [chargers])
  const selectedCharger = chargers.find((charger) => charger.id === selectedChargerId) ?? activeChargers[0] ?? chargers[0]

  useEffect(() => {
    if (!simulationRunning) return undefined
    const timer = window.setInterval(() => {
      setReadingTick((current) => current + 1)
      setMeasurementTime(new Date())
    }, 5000)
    return () => window.clearInterval(timer)
  }, [simulationRunning])

  const filteredHistory = useMemo(() => energyHistory
    .filter((record) => stationFilter === 'All stations' || record.stationId === stationFilter)
    .reduce((days, record) => {
      const day = days[record.date] ?? { date: record.date, energy: 0, peakPower: 0, acEnergy: 0, dcEnergy: 0 }
      day.energy += record.energy
      day.peakPower = Math.max(day.peakPower, record.peakPower)
      day.acEnergy += record.acEnergy
      day.dcEnergy += record.dcEnergy
      days[record.date] = day
      return days
    }, {}),
  [stationFilter])
  const chartData = Object.values(filteredHistory).slice(-Number(range)).map((record) => ({
    ...record,
    averagePower: Number((record.energy / 24).toFixed(1)),
    label: formatShortDate(record.date),
  }))

  const stationEnergy = useMemo(() => {
    const totals = new Map(stations.map((station) => [station.id, { station: station.name, energy: 0 }]))
    energyHistory.forEach((record) => {
      if (stationFilter !== 'All stations' && record.stationId !== stationFilter) return
      const total = totals.get(record.stationId)
      if (total) total.energy += record.energy
    })
    return [...totals.values()].filter((item) => item.energy > 0).sort((a, b) => b.energy - a.energy)
  }, [stations, stationFilter])

  const energyToday = chartData.at(-1)?.energy ?? 0
  const energyMonth = chartData.reduce((total, item) => total + item.energy, 0)
  const averagePower = chartData.length
    ? chartData.reduce((sum, item) => sum + item.averagePower, 0) / chartData.length
    : 0
  const peakPower = chartData.reduce((peak, item) => Math.max(peak, item.peakPower), 0)
  const applicableChargers = stationFilter === 'All stations'
    ? chargers
    : chargers.filter((charger) => charger.stationId === stationFilter)
  const averageUtilization = applicableChargers.length
    ? applicableChargers.filter((charger) => charger.status === 'Charging').length / applicableChargers.length * 100
    : 0
  const energyCost = energyMonth * preferences.electricityCostPerKwh
  const currentPower = selectedCharger ? Math.min(
    selectedCharger.ratedPower,
    estimatedPower(selectedCharger) + (simulationRunning && selectedCharger.status === 'Charging' ? (readingTick % 3) * 0.2 : 0),
  ) : 0
  function refreshReadings() {
    setRefreshCount((count) => count + 1)
    setMeasurementTime(new Date())
  }

  return <div className="energy-page">
    <div className="energy-page-header">
      <PageHeader title="Energy Monitoring" description="Explore simulated energy use, power demand, and charger utilization across your network." />
      <span className="energy-demo-chip"><Activity size={14} /> Simulation Mode — No live charger connection</span>
    </div>

    <div className="energy-controls">
      <label>Reporting period<select value={range} onChange={(event) => setRange(event.target.value)}>
        {rangeOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
      </select></label>
      <label>Station<select value={stationFilter} onChange={(event) => setStationFilter(event.target.value)}>
        <option>All stations</option>{stations.map((station) => <option key={station.id} value={station.id}>{station.name}</option>)}
      </select></label>
    </div>

    <section className="energy-metrics-grid" aria-label="Energy monitoring metrics">
      <EnergyMetric icon={Zap} label="Energy Delivered Today" value={formatEnergy(energyToday)} note="Simulated daily total" />
      <EnergyMetric icon={Activity} label="Energy Delivered This Period" value={formatEnergy(energyMonth)} note={`Selected ${range === '1' ? 'day' : `${range} days`}`} />
      <EnergyMetric icon={Activity} label="Average Power" value={`${averagePower.toFixed(1)} kW`} note="Average daily energy ÷ 24 h" />
      <EnergyMetric icon={Zap} label="Peak Power" value={`${peakPower.toFixed(1)} kW`} note="Simulated period peak" />
      <EnergyMetric icon={Clock3} label="Average Utilization" value={`${averageUtilization.toFixed(1)}%`} note="Chargers currently charging" />
      <EnergyMetric icon={Zap} label="Estimated Energy Cost" value={formatCurrency(energyCost)} note={`At ₹${preferences.electricityCostPerKwh.toFixed(2)} / kWh`} />
    </section>

    <div className="energy-chart-grid">
      <EnergyChartCard title="Energy consumption" description="Delivered energy by day (kWh)" legend={<span className="energy-legend"><i /> Energy delivered</span>}>
        {chartData.length ? <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={chartData} margin={{ top: 8, right: 8, left: -14, bottom: 0 }}>
            <defs><linearGradient id="energyArea" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#c4e16b" stopOpacity={0.28} /><stop offset="95%" stopColor="#c4e16b" stopOpacity={0.01} /></linearGradient></defs>
            <CartesianGrid stroke="#293740" strokeDasharray="3 5" vertical={false} />
            <XAxis dataKey="label" tick={{ fill: '#87969a', fontSize: 9 }} tickLine={false} axisLine={{ stroke: '#36444b' }} />
            <YAxis tick={{ fill: '#87969a', fontSize: 9 }} tickLine={false} axisLine={false} />
            <Tooltip formatter={(value) => [`${formatNumber(value)} kWh`, 'Energy']} contentStyle={{ background: '#18232c', border: '1px solid #3a4a52', borderRadius: 8, color: '#edf2ed', fontSize: 11 }} />
            <Area type="monotone" dataKey="energy" name="Energy delivered" stroke="#c4e16b" strokeWidth={2} fill="url(#energyArea)" />
          </AreaChart>
        </ResponsiveContainer> : <div className="energy-empty-state">No energy readings for this station and date range.</div>}
      </EnergyChartCard>

      <EnergyChartCard title="Power demand" description="Estimated average and peak power (kW)" legend={<span className="energy-chart-subtitle">Daily estimate</span>}>
        {chartData.length ? <ResponsiveContainer width="100%" height={260}>
          <LineChart data={chartData} margin={{ top: 8, right: 8, left: -14, bottom: 0 }}>
            <CartesianGrid stroke="#293740" strokeDasharray="3 5" vertical={false} />
            <XAxis dataKey="label" tick={{ fill: '#87969a', fontSize: 9 }} tickLine={false} axisLine={{ stroke: '#36444b' }} />
            <YAxis tick={{ fill: '#87969a', fontSize: 9 }} tickLine={false} axisLine={false} />
            <Tooltip formatter={(value) => [`${Number(value).toFixed(1)} kW`]} contentStyle={{ background: '#18232c', border: '1px solid #3a4a52', borderRadius: 8, color: '#edf2ed', fontSize: 11 }} />
            <Legend wrapperStyle={{ color: '#aab7b8', fontSize: 10 }} />
            <Line type="monotone" dataKey="averagePower" name="Average" stroke="#9bc77e" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="peakPower" name="Peak" stroke="#79add5" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer> : <div className="energy-empty-state">No power readings are available.</div>}
      </EnergyChartCard>

      <EnergyChartCard title="Energy by station" description="30-day delivered energy (kWh)">
        {stationEnergy.length ? <ResponsiveContainer width="100%" height={270}>
          <BarChart data={stationEnergy} layout="vertical" margin={{ top: 4, right: 15, left: 20, bottom: 0 }}>
            <CartesianGrid stroke="#293740" strokeDasharray="3 5" horizontal={false} />
            <XAxis type="number" tick={{ fill: '#87969a', fontSize: 9 }} tickLine={false} axisLine={{ stroke: '#36444b' }} />
            <YAxis type="category" dataKey="station" width={120} tick={{ fill: '#aab7b8', fontSize: 9 }} tickLine={false} axisLine={false} />
            <Tooltip formatter={(value) => [`${formatNumber(value)} kWh`, 'Energy']} contentStyle={{ background: '#18232c', border: '1px solid #3a4a52', borderRadius: 8, color: '#edf2ed', fontSize: 11 }} />
            <Bar dataKey="energy" name="Delivered" fill="#9bc77e" radius={[0, 5, 5, 0]} />
          </BarChart>
        </ResponsiveContainer> : <div className="energy-empty-state">No energy readings are available.</div>}
      </EnergyChartCard>

      <EnergyChartCard title="AC and DC energy" description="Daily energy by charging type (kWh)" legend={<span className="energy-chart-subtitle">Illustrative mix</span>}>
        {chartData.length ? <ResponsiveContainer width="100%" height={270}>
          <BarChart data={chartData} margin={{ top: 8, right: 8, left: -14, bottom: 0 }}>
            <CartesianGrid stroke="#293740" strokeDasharray="3 5" vertical={false} />
            <XAxis dataKey="label" tick={{ fill: '#87969a', fontSize: 9 }} tickLine={false} axisLine={{ stroke: '#36444b' }} />
            <YAxis tick={{ fill: '#87969a', fontSize: 9 }} tickLine={false} axisLine={false} />
            <Tooltip formatter={(value) => [`${formatNumber(value)} kWh`]} contentStyle={{ background: '#18232c', border: '1px solid #3a4a52', borderRadius: 8, color: '#edf2ed', fontSize: 11 }} />
            <Legend wrapperStyle={{ color: '#aab7b8', fontSize: 10 }} />
            <Bar dataKey="acEnergy" name="AC energy" stackId="type" fill="#9bc77e" />
            <Bar dataKey="dcEnergy" name="DC energy" stackId="type" fill="#79add5" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer> : <div className="energy-empty-state">No energy readings are available.</div>}
      </EnergyChartCard>
    </div>

    <section className="energy-measurement-card">
      <div className="energy-measurement-heading">
        <div><p className="energy-eyebrow">Electrical measurement panel</p><h2>Simulated charger telemetry</h2><p>Illustrative sample readings. No physical charger is connected.</p></div>
        <div className="energy-simulation-controls">
          {simulationRunning
            ? <button type="button" className="energy-stop-button" onClick={() => setSimulationRunning(false)}><CircleStop size={15} />Stop simulation</button>
            : <button type="button" className="energy-start-button" onClick={() => setSimulationRunning(true)}><Play size={14} />Start simulation</button>}
          <button type="button" className="energy-refresh-button" onClick={refreshReadings}><RefreshCw size={14} />Refresh sample</button>
        </div>
      </div>
      <div className="energy-reading-controls">
        <label>Charger<select value={selectedCharger?.id ?? ''} onChange={(event) => setSelectedChargerId(event.target.value)}>
          {chargers.map((charger) => <option key={charger.id} value={charger.id}>{charger.id} · {charger.type} · {charger.status}</option>)}
        </select></label>
        <span className={`energy-telemetry-status ${simulationRunning ? 'is-running' : ''}`}><i />{simulationRunning ? 'Simulation running' : 'Simulation stopped'}</span>
      </div>
      {selectedCharger ? <div className="energy-reading-grid">
        <div><span>Voltage</span><strong>{selectedCharger.voltage} V</strong></div>
        <div><span>Current</span><strong>{selectedCharger.current} A</strong></div>
        <div><span>Estimated real power</span><strong>{currentPower.toFixed(1)} kW</strong></div>
        <div><span>Energy in selected period</span><strong>{formatEnergy(energyMonth)}</strong></div>
        <div><span>Charger type</span><strong>{selectedCharger.type} · {selectedCharger.connector}</strong></div>
        <div><span>Rated power</span><strong>{selectedCharger.ratedPower} kW</strong></div>
        <div><span>Measurement time</span><strong>{measurementTime.toLocaleTimeString('en-IN')}</strong></div>
        <div><span>Operational status</span><strong className={`reading-state-${selectedCharger.status.toLowerCase()}`}>{selectedCharger.status}</strong></div>
      </div> : <div className="energy-empty-state">Add a charger to show sample telemetry.</div>}
      <p className="energy-assumption-note">Calculation assumptions: for balanced three-phase AC, P = √3 × V(line-to-line) × I × power factor. For DC and single-phase AC, P = V × I × power factor. AC measurements use the configured illustrative power factor; DC uses factor 1. Values are estimates and are not a substitute for metered real power.</p>
      <p className="energy-refreshed-note" aria-live="polite">Sample refreshed {refreshCount ? `${refreshCount} time${refreshCount === 1 ? '' : 's'}` : 'using deterministic demo values'}.</p>
    </section>
  </div>
}

export default EnergyMonitoringPage
