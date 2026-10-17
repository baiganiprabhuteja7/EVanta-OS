function StationStatusBadge({ status }) {
  const statusClass = status.toLowerCase().replaceAll(' ', '-')

  return (
    <span className={`station-status-badge station-status-${statusClass}`}>
      <span aria-hidden="true" />
      {status}
    </span>
  )
}

export default StationStatusBadge
