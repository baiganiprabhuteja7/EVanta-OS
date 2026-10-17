export const PREFERENCES_STORAGE_KEY = 'evanta-os.preferences.v1'

export const defaultPreferences = {
  displayName: 'EVanta OS Workspace Admin',
  email: 'admin@evanta.demo',
  currency: 'INR',
  energyUnit: 'kWh',
  electricityCostPerKwh: 8.5,
  initialInvestment: 12500000,
  monthlyOperatingCosts: 185000,
  notifyOperationalAlerts: true,
  notifySessionUpdates: true,
  notifyWeeklySummary: false,
  compactTables: false,
  reduceMotion: false,
}

export function readPreferences() {
  try {
    const stored = window.localStorage.getItem(PREFERENCES_STORAGE_KEY)
    if (!stored) return { values: defaultPreferences, warning: '' }
    const parsed = JSON.parse(stored)
    return { values: { ...defaultPreferences, ...parsed }, warning: '' }
  } catch {
    return {
      values: defaultPreferences,
      warning: 'Saved preferences could not be read. Defaults are shown; saving will replace the unreadable preference entry.',
    }
  }
}
