import { useCallback, useEffect, useMemo, useState } from 'react'
import { initialChargers } from '../data/chargersData.js'
import { initialStations } from '../data/stationsData.js'
import { initialSessions } from '../data/sessionsData.js'
import { defaultPreferences, PREFERENCES_STORAGE_KEY, readPreferences } from '../data/settingsData.js'
import { AppDataContext } from './AppDataContext.js'

function withChargerCounts(stations, chargers) {
  return stations.map((station) => {
    const stationChargers = chargers.filter((charger) => charger.stationId === station.id)
    return {
      ...station,
      chargers: stationChargers.length,
      activeChargers: stationChargers.filter((charger) => charger.status === 'Charging').length,
    }
  })
}

export function AppDataProvider({ children }) {
  const [stationRecords, setStationRecords] = useState(initialStations)
  const [chargers, setChargers] = useState(initialChargers)
  const [sessions, setSessions] = useState(initialSessions)
  const [storedPreferences, setStoredPreferences] = useState(readPreferences)
  const preferences = storedPreferences.values
  useEffect(() => {
    document.documentElement.dataset.tableDensity = preferences.compactTables ? 'compact' : 'comfortable'
    document.documentElement.dataset.reduceMotion = preferences.reduceMotion ? 'true' : 'false'
  }, [preferences.compactTables, preferences.reduceMotion])
  const stations = useMemo(() => withChargerCounts(stationRecords, chargers), [stationRecords, chargers])
  const setStations = useCallback((updater) => {
    setStationRecords((current) => {
      const visibleStations = withChargerCounts(current, chargers)
      return typeof updater === 'function' ? updater(visibleStations) : updater
    })
  }, [chargers])
  const savePreferences = useCallback((nextPreferences) => {
    try {
      window.localStorage.setItem(PREFERENCES_STORAGE_KEY, JSON.stringify(nextPreferences))
      setStoredPreferences({ values: nextPreferences, warning: '' })
      return { error: '' }
    } catch {
      return { error: 'Preferences could not be saved in this browser. Check browser storage availability and try again.' }
    }
  }, [])
  const resetPreferences = useCallback(() => {
    try {
      window.localStorage.removeItem(PREFERENCES_STORAGE_KEY)
      setStoredPreferences({ values: defaultPreferences, warning: '' })
      return { error: '' }
    } catch {
      return { error: 'Preferences could not be reset in this browser. Check browser storage availability and try again.' }
    }
  }, [])
  const data = useMemo(
    () => ({ stations, setStations, chargers, setChargers, sessions, setSessions, preferences, savePreferences, resetPreferences, preferenceWarning: storedPreferences.warning }),
    [stations, setStations, chargers, setChargers, sessions, setSessions, preferences, savePreferences, resetPreferences, storedPreferences.warning],
  )

  return <AppDataContext.Provider value={data}>{children}</AppDataContext.Provider>
}
