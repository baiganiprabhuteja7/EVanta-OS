const DAY_MS = 24 * 60 * 60 * 1000

const stationCatalog = [
  {
    id: 'EV-BLR-001',
    name: 'Northstar Mobility Hub',
    location: 'Bengaluru, Karnataka',
    chargerStart: 1,
    chargerCount: 8,
    tariff: 21,
  },
  {
    id: 'EV-HYD-002',
    name: 'Airport Gateway',
    location: 'Hyderabad, Telangana',
    chargerStart: 9,
    chargerCount: 6,
    tariff: 23,
  },
  {
    id: 'EV-PUN-003',
    name: 'Tech Park Central',
    location: 'Pune, Maharashtra',
    chargerStart: 15,
    chargerCount: 5,
    tariff: 20,
  },
  {
    id: 'EV-MUM-004',
    name: 'Harbour Point',
    location: 'Mumbai, Maharashtra',
    chargerStart: 20,
    chargerCount: 5,
    tariff: 22,
  },
  {
    id: 'EV-MAA-005',
    name: 'Greenway Plaza',
    location: 'Chennai, Tamil Nadu',
    chargerStart: 25,
    chargerCount: 4,
    tariff: 19,
  },
  {
    id: 'EV-DEL-006',
    name: 'Ring Road Express',
    location: 'Delhi, NCR',
    chargerStart: 29,
    chargerCount: 4,
    tariff: 24,
  },
]

const chargerStatuses = [
  'charging', 'charging', 'charging', 'charging', 'charging', 'charging', 'charging', 'charging',
  'available', 'available', 'available', 'available', 'available', 'available', 'available',
  'available', 'available', 'available', 'available', 'available', 'available', 'available',
  'available', 'offline', 'offline', 'offline', 'offline', 'offline',
  'faulted', 'faulted', 'faulted', 'faulted',
]

const dateKey = (date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function createSessions(seed) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const sessions = []

  for (let dayOffset = 59; dayOffset >= 0; dayOffset -= 1) {
    const day = new Date(today.getTime() - dayOffset * DAY_MS)
    const date = dateKey(day)

    for (let index = 0; index < 18; index += 1) {
      const isInProgress = dayOffset === 0 && index === 17
      const stationIndex = isInProgress
        ? 0
        : (dayOffset + index + seed) % stationCatalog.length
      const station = stationCatalog[stationIndex]
      const chargerNumber = isInProgress
        ? station.chargerStart
        : station.chargerStart +
          ((dayOffset * 2 + index + seed) % station.chargerCount)
      const energy = isInProgress
        ? 12
        : Math.max(
            10,
            18 +
              ((dayOffset * 13 + index * 17 + seed * 11) % 42) +
              (((dayOffset * 7 + seed * 3) % 17) - 8),
          )
      const durationMinutes = isInProgress
        ? 20
        : Math.round(energy * 1.35 + 8 + ((index * 7) % 17))
      const startedAt = new Date(day)

      if (isInProgress) {
        startedAt.setMinutes(startedAt.getMinutes() - durationMinutes)
      } else {
        startedAt.setHours(
          6 + Math.floor(index / 2),
          (index % 2) * 30 + ((dayOffset * 11) % 20),
          0,
          0,
        )
      }

      sessions.push({
        id: `EV-${date.slice(2).replaceAll('-', '')}-${String(index + 1).padStart(2, '0')}`,
        date,
        startedAt,
        stationId: station.id,
        station: station.name,
        charger: `CH-${String(chargerNumber).padStart(3, '0')}`,
        energy,
        durationMinutes,
        amount: Math.round(energy * station.tariff),
        status: isInProgress ? 'In progress' : 'Completed',
      })
    }
  }

  return sessions
}

function sumBy(items, key) {
  return items.reduce((total, item) => total + item[key], 0)
}

export function createDashboardData(seed = 0) {
  const sessions = createSessions(seed)
  const dailyMap = new Map()

  sessions.forEach((session) => {
    const daily = dailyMap.get(session.date) ?? {
      date: session.date,
      energy: 0,
      revenue: 0,
      sessions: 0,
    }
    daily.energy += session.energy
    daily.revenue += session.amount
    daily.sessions += 1
    dailyMap.set(session.date, daily)
  })

  const chargers = chargerStatuses.map((status, index) => ({
    id: `CH-${String(index + 1).padStart(3, '0')}`,
    status,
    stationId:
      stationCatalog.find(
        (station) =>
          index + 1 >= station.chargerStart &&
          index + 1 < station.chargerStart + station.chargerCount,
      )?.id ?? stationCatalog[0].id,
  }))

  const statusDefinitions = [
    { key: 'charging', label: 'Active', color: '#c4e16b' },
    { key: 'available', label: 'Available', color: '#65818b' },
    { key: 'offline', label: 'Offline', color: '#e6ad64' },
    { key: 'faulted', label: 'Faulted', color: '#d5786d' },
  ]
  const chargerStatus = statusDefinitions.map((status) => ({
    ...status,
    count: chargers.filter((charger) =>
      status.key === 'charging'
        ? charger.status === 'charging'
        : charger.status === status.key,
    ).length,
  }))
  const today = dateKey(new Date())

  return {
    stations: stationCatalog,
    chargers,
    chargerStatus,
    sessions,
    dailyMetrics: [...dailyMap.values()],
    alerts: [
      {
        id: 'charger-offline',
        severity: 'critical',
        title: 'Charger offline',
        description: 'CH-024 at Harbour Point is marked offline in this simulated network.',
        time: '12 min ago',
      },
      {
        id: 'high-utilization',
        severity: 'warning',
        title: 'High station utilization',
        description: 'Airport Gateway reached 86% illustrative utilization during a peak window.',
        time: '28 min ago',
      },
      {
        id: 'session-complete',
        severity: 'success',
        title: 'Charging session completed',
        description: 'A simulated 42 kWh session finished at Northstar Mobility Hub.',
        time: '46 min ago',
      },
      {
        id: 'energy-variance',
        severity: 'info',
        title: 'Unusual energy consumption',
        description: 'Demo consumption at Tech Park Central is above its illustrative daily trend.',
        time: '1 hr ago',
      },
    ],
    today,
  }
}

export function getDateRangeMetrics(dailyMetrics, range) {
  const rangeDays = range === 'today' ? 1 : range === '7d' ? 7 : 30
  const current = dailyMetrics.slice(-rangeDays)
  const previous = dailyMetrics.slice(-rangeDays * 2, -rangeDays)

  return {
    current,
    previous,
    energy: sumBy(current, 'energy'),
    revenue: sumBy(current, 'revenue'),
    sessions: sumBy(current, 'sessions'),
    previousEnergy: sumBy(previous, 'energy'),
    previousRevenue: sumBy(previous, 'revenue'),
    previousSessions: sumBy(previous, 'sessions'),
    rangeDays,
  }
}

export function getStationPerformance(stations, chargers, sessions, dateKeys) {
  const selectedSessions = sessions.filter((session) =>
    dateKeys.has(session.date),
  )

  return stations.map((station) => {
    const stationChargers = chargers.filter(
      (charger) => charger.stationId === station.id,
    )
    const stationSessions = selectedSessions.filter(
      (session) => session.stationId === station.id,
    )
    const chargingChargers = stationChargers.filter(
      (charger) => charger.status === 'charging',
    ).length
    const availableChargers = stationChargers.filter(
      (charger) => charger.status === 'available',
    ).length
    const energy = sumBy(stationSessions, 'energy')
    const revenue = sumBy(stationSessions, 'amount')
    const utilization = stationChargers.length
      ? Math.round((chargingChargers / stationChargers.length) * 100)
      : 0

    return {
      ...station,
      totalChargers: stationChargers.length,
      activeChargers: chargingChargers + availableChargers,
      energy,
      revenue,
      utilization,
      status:
        stationChargers.some(
          (charger) => charger.status === 'offline' || charger.status === 'faulted',
        )
          ? 'Attention'
          : 'Operational',
    }
  })
}

export function getTodayMetrics(data) {
  const todaySessions = data.sessions.filter(
    (session) => session.date === data.today,
  )
  return {
    revenue: sumBy(todaySessions, 'amount'),
    sessions: todaySessions.length,
    energy: sumBy(todaySessions, 'energy'),
  }
}
