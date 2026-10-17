import { LayoutDashboard } from 'lucide-react'
import PageHeader from '../components/common/PageHeader.jsx'

function PlaceholderPage({ title, description }) {
  return (
    <>
      <PageHeader title={title} description={description} />
      <section className="placeholder-panel" aria-label={`${title} page placeholder`}>
        <span className="placeholder-icon" aria-hidden="true">
          <LayoutDashboard size={21} strokeWidth={1.8} />
        </span>
        <h2>{title} workspace</h2>
        <p>
          This area is ready for the {title.toLowerCase()} experience. More
          capabilities will be introduced in a future release.
        </p>
      </section>
    </>
  )
}

export default PlaceholderPage
