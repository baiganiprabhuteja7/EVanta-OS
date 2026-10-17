import { initialChargers } from './chargersData.js'
import { initialStations } from './stationsData.js'

const stationMap = new Map(initialStations.map((station) => [station.id, station]))
const anchor = new Date(2026, 9, 17, 12, 0, 0)

function sessionRecord({ id, charger, startedAt, endedAt, durationMinutes, energy, rate, status }) {
  const station = stationMap.get(charger.stationId)
  return {
    id,
    stationId: charger.stationId,
    station: station?.name ?? 'Unknown station',
    chargerId: charger.id,
    chargerType: charger.type,
    startedAt: startedAt.toISOString(),
    endedAt: endedAt?.toISOString() ?? null,
    durationMinutes,
    energy,
    ratePerKwh: rate,
    amount: status === 'Failed' ? 0 : Number((energy * rate).toFixed(2)),
    status,
  }
}

const ongoingSessions = initialChargers
  .filter((charger) => charger.status === 'Charging')
  .map((charger, index) => {
    const durationMinutes = 18 + ((index * 13) % 62)
    return sessionRecord({
      id: charger.currentSession,
      charger,
      startedAt: new Date(anchor.getTime() - durationMinutes * 60_000),
      endedAt: null,
      durationMinutes,
      energy: Number((5.5 + ((index * 19) % 147) / 10).toFixed(1)),
      rate: 19 + (index % 6),
      status: 'Ongoing',
    })
  })

const historicalSessions = Array.from({ length: 48 }, (_, index) => {
  const charger = initialChargers[(index * 7 + 3) % initialChargers.length]
  const durationMinutes = 25 + ((index * 17) % 96)
  const daysAgo = (index * 5) % 30
  const startedAt = new Date(anchor.getTime() - daysAgo * 86_400_000 - (index % 12) * 3_600_000)
  const failed = index % 13 === 0
  const status = failed ? 'Failed' : 'Completed'
  const energy = failed ? 0 : Number((12 + ((index * 23) % 580) / 10).toFixed(1))
  return sessionRecord({
    id: `SES-HIST-${String(index + 1).padStart(4, '0')}`,
    charger,
    startedAt,
    endedAt: new Date(startedAt.getTime() + durationMinutes * 60_000),
    durationMinutes,
    energy,
    rate: 19 + ((index + 2) % 6),
    status,
  })
})

export const initialSessions = [...ongoingSessions, ...historicalSessions]
  .sort((a, b) => new Date(b.startedAt) - new Date(a.startedAt))

export const sessionStatusOptions = ['Completed', 'Ongoing', 'Failed']
export const sessionRatePerKwh = 22
