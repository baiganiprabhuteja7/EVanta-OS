function PageHeader({ title, description }) {
  return (
    <header className="page-header">
      <p className="page-eyebrow">EVanta OS / Workspace</p>
      <h1 className="page-title">{title}</h1>
      <p className="page-description">{description}</p>
    </header>
  )
}

export default PageHeader
