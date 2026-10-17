import { Activity, BatteryCharging } from 'lucide-react'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  formatCurrency,
  formatEnergy,
  formatNumber,
  formatShortDate,
} from '../../utils/formatters.js'

function TrendTooltip({ active, payload, label, type }) {
  if (!active || !payload?.length) return null
  const value = payload[0].value
  const formatted =
    type === 'energy'
      ? formatEnergy(value)
      : type === 'revenue'
        ? formatCurrency(value)
        : formatNumber(value)
  const detail =
    type === 'energy'
      ? `${formatNumber(payload[0].payload.sessions)} sessions`
      : type === 'revenue'
        ? `${formatEnergy(payload[0].payload.energy)} delivered`
        : `${formatEnergy(payload[0].payload.energy)} delivered`

  return (
    <div className="chart-tooltip">
      <span className="chart-tooltip-label">{formatShortDate(label)}</span>
      <strong>{formatted}</strong>
      <span className="chart-tooltip-meta">{detail}</span>
    </div>
  )
}

const chartDefinitions = {
  energy: {
    title: 'Energy Consumption',
    description: 'Daily energy delivered across the network',
    legend: 'Energy delivered',
    color: '#c4e16b',
    dataKey: 'energy',
  },
  revenue: {
    title: 'Revenue Overview',
    description: 'Daily estimated revenue in Indian rupees',
    legend: 'Revenue',
    color: '#77939c',
    dataKey: 'revenue',
  },
  sessions: {
    title: 'Charging Sessions',
    description: 'Daily completed and active charging sessions',
    legend: 'Sessions',
    color: '#e6ad64',
    dataKey: 'sessions',
  },
}

function TimeSeries({ type, data }) {
  const definition = chartDefinitions[type]
  const revenue = type === 'revenue'
  const session = type === 'sessions'
  const tickFormatter = revenue
    ? (value) => formatCurrency(value, true)
    : (value) => formatNumber(value)
  const commonProps = {
    data,
    margin: { top: 10, right: 8, left: 0, bottom: 0 },
  }

  return (
    <div className="trend-chart-wrap">
      {data.length ? (
        <ResponsiveContainer width="100%" height="100%">
          {revenue ? (
            <BarChart {...commonProps} barCategoryGap="28%">
              <CartesianGrid vertical={false} stroke="#ffffff12" strokeDasharray="3 5" />
              <XAxis
                dataKey="date"
                tickFormatter={formatShortDate}
                tickLine={false}
                axisLine={false}
                minTickGap={25}
                tick={{ fill: '#9aa9ad', fontSize: 10 }}
              />
              <YAxis
                tickFormatter={tickFormatter}
                tickLine={false}
                axisLine={false}
                width={60}
                tick={{ fill: '#9aa9ad', fontSize: 10 }}
              />
              <Tooltip
                content={<TrendTooltip type={type} />}
                cursor={{ fill: '#ffffff0b' }}
              />
              <Bar
                dataKey={definition.dataKey}
                name={definition.legend}
                fill={definition.color}
                radius={[4, 4, 0, 0]}
                maxBarSize={28}
              />
            </BarChart>
          ) : session ? (
            <LineChart {...commonProps}>
              <CartesianGrid vertical={false} stroke="#ffffff12" strokeDasharray="3 5" />
              <XAxis
                dataKey="date"
                tickFormatter={formatShortDate}
                tickLine={false}
                axisLine={false}
                minTickGap={25}
                tick={{ fill: '#9aa9ad', fontSize: 10 }}
              />
              <YAxis
                tickFormatter={tickFormatter}
                tickLine={false}
                axisLine={false}
                width={38}
                tick={{ fill: '#9aa9ad', fontSize: 10 }}
              />
              <Tooltip
                content={<TrendTooltip type={type} />}
                cursor={{ stroke: '#ffffff35', strokeDasharray: '3 4' }}
              />
              <Line
                type="monotone"
                dataKey={definition.dataKey}
                name={definition.legend}
                stroke={definition.color}
                strokeWidth={2.5}
                dot={false}
                activeDot={{ r: 4, fill: definition.color, stroke: '#18232c', strokeWidth: 2 }}
              />
            </LineChart>
          ) : (
            <AreaChart {...commonProps}>
              <defs>
                <linearGradient id="energy-area" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={definition.color} stopOpacity={0.2} />
                  <stop offset="100%" stopColor={definition.color} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid vertical={false} stroke="#ffffff12" strokeDasharray="3 5" />
              <XAxis
                dataKey="date"
                tickFormatter={formatShortDate}
                tickLine={false}
                axisLine={false}
                minTickGap={25}
                tick={{ fill: '#9aa9ad', fontSize: 10 }}
              />
              <YAxis
                tickFormatter={tickFormatter}
                tickLine={false}
                axisLine={false}
                width={42}
                tick={{ fill: '#9aa9ad', fontSize: 10 }}
              />
              <Tooltip
                content={<TrendTooltip type={type} />}
                cursor={{ stroke: '#ffffff35', strokeDasharray: '3 4' }}
              />
              <Area
                type="monotone"
                dataKey={definition.dataKey}
                name={definition.legend}
                stroke={definition.color}
                strokeWidth={2.5}
                fill="url(#energy-area)"
                activeDot={{ r: 4, fill: definition.color, stroke: '#18232c', strokeWidth: 2 }}
              />
            </AreaChart>
          )}
        </ResponsiveContainer>
      ) : (
        <div className="chart-empty">
          <Activity size={20} aria-hidden="true" />
          <span>No demo readings are available for this date range.</span>
        </div>
      )}
    </div>
  )
}

export function ChartPanel({ type, data, summary }) {
  const definition = chartDefinitions[type]

  return (
    <section className="dashboard-card chart-card">
      <div className="card-heading chart-heading">
        <div>
          <h2>{definition.title}</h2>
          <p>{definition.description}</p>
        </div>
        <span className={`chart-legend chart-legend-${type}`}>
          <span aria-hidden="true" />
          {definition.legend}
        </span>
      </div>
      <div className="chart-summary">
        <strong>{summary}</strong>
        <span>selected period</span>
      </div>
      <TimeSeries type={type} data={data} />
    </section>
  )
}

export function ChargerStatusChart({ statuses, total }) {
  return (
    <section className="dashboard-card status-card">
      <div className="card-heading">
        <div>
          <h2>Charger Status</h2>
          <p>Demo charger fleet distribution</p>
        </div>
        <BatteryCharging size={17} className="card-heading-icon" aria-hidden="true" />
      </div>
      <div className="status-chart">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={statuses}
              dataKey="count"
              nameKey="label"
              cx="50%"
              cy="50%"
              innerRadius="70%"
              outerRadius="91%"
              paddingAngle={3}
              stroke="none"
              isAnimationActive={false}
            >
              {statuses.map((status) => (
                <Cell key={status.key} fill={status.color} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value, name) => [formatNumber(value), name]}
              contentStyle={{
                border: '1px solid #34434c',
                borderRadius: 9,
                background: '#1c2932',
                color: '#eaf0e8',
                fontSize: 12,
              }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="donut-center" aria-label={`${formatNumber(total)} total chargers`}>
          <strong>{formatNumber(total)}</strong>
          <span>chargers</span>
        </div>
      </div>
      <ul className="status-legend">
        {statuses.map((status) => (
          <li key={status.key}>
            <span className="status-legend-name">
              <span className="status-dot" style={{ '--status-color': status.color }} />
              {status.label}
            </span>
            <strong>{formatNumber(status.count)}</strong>
          </li>
        ))}
      </ul>
    </section>
  )
}
