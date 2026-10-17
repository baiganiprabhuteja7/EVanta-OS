import { useState } from 'react'
import { Bell, Building2, RotateCcw, Save, SlidersHorizontal, UserRound } from 'lucide-react'
import PageHeader from '../components/common/PageHeader.jsx'
import { defaultPreferences } from '../data/settingsData.js'
import { useAppData } from '../context/useAppData.js'
import { formatCurrency } from '../utils/formatters.js'
import './SettingsPage.css'

function PreferenceToggle({ name, label, description, checked, onChange }) {
  return <label className="preference-toggle">
    <span><strong>{label}</strong><small>{description}</small></span>
    <input type="checkbox" name={name} checked={checked} onChange={onChange} />
    <i aria-hidden="true" />
  </label>
}

function SettingsPage() {
  const { preferences, savePreferences, resetPreferences, preferenceWarning } = useAppData()
  const [form, setForm] = useState(preferences)
  const [message, setMessage] = useState(preferenceWarning)

  function updateField(event) {
    const { name, value, checked, type } = event.target
    setForm((current) => ({ ...current, [name]: type === 'checkbox' ? checked : value }))
    setMessage('')
  }

  function submit(event) {
    event.preventDefault()
    const result = savePreferences({
      ...form,
      electricityCostPerKwh: Number(form.electricityCostPerKwh),
      initialInvestment: Number(form.initialInvestment),
      monthlyOperatingCosts: Number(form.monthlyOperatingCosts),
    })
    setMessage(result.error || 'Preferences saved in this browser.')
  }

  function reset() {
    const result = resetPreferences()
    if (result.error) {
      setMessage(result.error)
      return
    }
    setForm(defaultPreferences)
    setMessage('Preferences reset to the EVanta OS defaults.')
  }

  return <div className="settings-page">
    <PageHeader title="Settings" description="Manage workspace preferences and transparent demo business assumptions." />
    <div className="settings-simulation-note"><Building2 size={15} /><span>Frontend demo workspace. These settings are not linked to an authenticated account or backend.</span></div>
    <form className="settings-form" onSubmit={submit}>
      <section className="settings-card">
        <div className="settings-card-heading"><span><UserRound size={16} /></span><div><h2>User profile</h2><p>Profile details shown in this local workspace.</p></div></div>
        <div className="settings-fields two-col">
          <label>Display name<input name="displayName" value={form.displayName} onChange={updateField} required maxLength={80} /></label>
          <label>Email address<input name="email" type="email" value={form.email} onChange={updateField} required maxLength={160} /></label>
        </div>
      </section>

      <section className="settings-card">
        <div className="settings-card-heading"><span><SlidersHorizontal size={16} /></span><div><h2>Currency, units, and business assumptions</h2><p>All financial projections are illustrative and should be configured for your local operation.</p></div></div>
        <div className="settings-fields two-col">
          <div className="settings-readonly-setting"><span>Currency</span><strong>INR (₹)</strong><small>India network display standard</small></div>
          <div className="settings-readonly-setting"><span>Energy unit</span><strong>kWh</strong><small>Energy values are displayed in kilowatt-hours</small></div>
          <label>Estimated electricity cost per kWh (₹)<input name="electricityCostPerKwh" type="number" value={form.electricityCostPerKwh} onChange={updateField} required min="0.01" max="10000" step="0.01" /></label>
          <label>Initial investment assumption (₹)<input name="initialInvestment" type="number" value={form.initialInvestment} onChange={updateField} required min="0" max="100000000000" step="1000" /></label>
          <label>Estimated monthly operating expenses (₹)<input name="monthlyOperatingCosts" type="number" value={form.monthlyOperatingCosts} onChange={updateField} required min="0" max="10000000000" step="1000" /></label>
        </div>
        <p className="settings-formula-note">Analytics estimates energy cost from delivered kWh × this rate. Estimated net operating benefit uses gross margin less these monthly expenses; it is not audited profit and excludes unconfigured taxes or other costs.</p>
      </section>

      <section className="settings-card">
        <div className="settings-card-heading"><span><Bell size={16} /></span><div><h2>Notification preferences</h2><p>Demo preferences only; the frontend does not send notifications.</p></div></div>
        <div className="settings-toggle-list">
          <PreferenceToggle name="notifyOperationalAlerts" label="Operational alerts" description="Show simulated offline and maintenance events." checked={form.notifyOperationalAlerts} onChange={updateField} />
          <PreferenceToggle name="notifySessionUpdates" label="Session updates" description="Show simulated session lifecycle activity." checked={form.notifySessionUpdates} onChange={updateField} />
          <PreferenceToggle name="notifyWeeklySummary" label="Weekly summary" description="Opt into a future weekly performance summary." checked={form.notifyWeeklySummary} onChange={updateField} />
        </div>
      </section>

      <section className="settings-card">
        <div className="settings-card-heading"><span><SlidersHorizontal size={16} /></span><div><h2>Display preferences</h2><p>These options apply to the frontend workspace in this browser.</p></div></div>
        <div className="settings-fields two-col">
          <label>Table density<select name="compactTables" value={form.compactTables ? 'compact' : 'comfortable'} onChange={(event) => setForm((current) => ({ ...current, compactTables: event.target.value === 'compact' }))}>
            <option value="comfortable">Comfortable</option><option value="compact">Compact</option>
          </select></label>
          <PreferenceToggle name="reduceMotion" label="Reduce motion" description="Minimize transitions and animation effects." checked={form.reduceMotion} onChange={updateField} />
        </div>
      </section>

      <section className="settings-card settings-about-card">
        <div className="settings-card-heading"><span><Building2 size={16} /></span><div><h2>Application and simulation</h2><p>EVanta OS · Powering Mobility. Engineering Intelligence.</p></div></div>
        <p>This portfolio interface uses illustrative stations, sessions, charger states, and energy readings. No real equipment telemetry or physical charger control is available. Demo preferences are stored locally in this browser; passwords and access tokens are not stored.</p>
        <small>Preview financial impact: default energy cost is {formatCurrency(defaultPreferences.electricityCostPerKwh)} per kWh; initial investment is {formatCurrency(defaultPreferences.initialInvestment)}.</small>
      </section>

      {message && <p className="settings-save-message" role="status">{message}</p>}
      <div className="settings-actions">
        <button type="button" className="settings-reset-button" onClick={reset}><RotateCcw size={14} />Reset defaults</button>
        <button type="submit" className="settings-save-button"><Save size={14} />Save preferences</button>
      </div>
    </form>
  </div>
}

export default SettingsPage
