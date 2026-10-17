import { initialStations } from './stationsData.js'

export const DEFAULT_ENERGY_COST_PER_KWH = 8.5

const dayKey = (date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export const energyHistory = Array.from({ length: 30 }, (_, offset) => {
  const date = new Date(2026, 9, 17 - (29 - offset))
  const dateKey = dayKey(date)
  return initialStations.map((station, stationIndex) => {
    const energy = 82 + stationIndex * 13 + ((offset * 17 + stationIndex * 29) % 53)
    const peakPower = 32 + stationIndex * 6 + ((offset * 11 + stationIndex * 7) % 28)
    return {
      date: dateKey,
      stationId: station.id,
      energy,
      peakPower,
      averagePower: Number((energy / 24).toFixed(1)),
      acEnergy: Math.round(energy * (0.31 + (stationIndex % 3) * 0.04)),
      dcEnergy: Math.round(energy * (0.69 - (stationIndex % 3) * 0.04)),
    }
  })
})
