export const formatNumber = (value, maximumFractionDigits = 0) =>
  new Intl.NumberFormat('en-IN', {
    maximumFractionDigits,
  }).format(value)

export const formatCurrency = (value, compact = false) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
    notation: compact ? 'compact' : 'standard',
  }).format(value)

export const formatEnergy = (value, maximumFractionDigits = 0) =>
  `${formatNumber(value, maximumFractionDigits)} kWh`

export const formatDuration = (minutes) => {
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  return hours > 0 ? `${hours}h ${remainingMinutes}m` : `${remainingMinutes}m`
}

export const formatShortDate = (dateKey) =>
  new Date(`${dateKey}T12:00:00`).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
  })

export const formatClockTime = (date) =>
  date.toLocaleTimeString('en-IN', {
    hour: 'numeric',
    minute: '2-digit',
  })

export const formatSessionTime = (date) =>
  date.toLocaleString('en-IN', {
    day: 'numeric',
    month: 'short',
    hour: 'numeric',
    minute: '2-digit',
  })
