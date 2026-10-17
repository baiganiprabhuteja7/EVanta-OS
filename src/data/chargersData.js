import { initialStations } from './stationsData.js'

const chargerProfiles = [
  { type: 'AC', connector: 'Type 2', power: 7.4, voltage: 230, current: 32 },
  { type: 'AC', connector: 'Type 2', power: 22, voltage: 400, current: 34 },
  { type: 'DC', connector: 'CCS2', power: 60, voltage: 500, current: 120 },
  { type: 'DC', connector: 'CCS2', power: 120, voltage: 650, current: 185 },
  { type: 'DC', connector: 'CHAdeMO', power: 50, voltage: 400, current: 125 },
]

export const chargerStatusOptions = ['Available', 'Charging', 'Offline', 'Faulted']

export function createChargerRecord(station, index) {
  const profile = chargerProfiles[(index - 1 + station.id.length) % chargerProfiles.length]
  let status = 'Available'

  if (station.status === 'Offline') status = 'Offline'
  else if (station.status === 'Faulted' || station.status === 'Maintenance') status = index === 1 ? 'Faulted' : 'Offline'
  else if (index <= station.activeChargers) status = 'Charging'

  const charging = status === 'Charging'
  return {
    id: `${station.id.replace('EV-', 'CH-')}-${String(index).padStart(2, '0')}`,
    stationId: station.id,
    type: profile.type,
    connector: profile.connector,
    ratedPower: profile.power,
    voltage: profile.voltage,
    current: charging ? profile.current : 0,
    powerFactor: profile.type === 'AC' ? 0.94 : null,
    status,
    currentSession: charging ? `SES-${station.id.slice(-3)}-${String(index).padStart(2, '0')}` : '',
    updatedAt: '2026-10-17T12:00:00+05:30',
  }
}

export const initialChargers = initialStations.flatMap((station) =>
  Array.from({ length: station.chargers }, (_, index) => createChargerRecord(station, index + 1)),
)
