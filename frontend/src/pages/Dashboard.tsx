import { useEffect, useState } from 'react'
import { getHealth, listProjects, type HealthRow, type Project } from '../api'

export default function Dashboard() {
  const [health, setHealth] = useState<HealthRow[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const [h, p] = await Promise.all([getHealth(), listProjects()])
        setHealth(h.data)
        setProjects(p.data)
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e))
      } finally {
        setLoading(false)
      }
    }
    load()
    const id = setInterval(load, 30000)
    return () => clearInterval(id)
  }, [])

  if (loading) return <div className="card">Loading...</div>
  if (error) return <div className="card status-error">Error: {error}</div>

  return (
    <div>
      <h2>Dashboard</h2>

      <div className="card">
        <h3>Projects</h3>
        <div className="grid-2">
          {projects.map((p) => (
            <div key={p.id} className="health-card">
              <h4>{p.key}</h4>
              <p>{p.name}</p>
              <p className="status-ok">{p.status}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h3>Agent Health</h3>
        <div className="grid-4">
          {health.map((h) => (
            <div key={h.profile} className="health-card">
              <h4>{h.profile}</h4>
              <p>{h.current_model || 'not set'}</p>
              <p className={`status-${h.status}`}>{h.status}</p>
              <p>{h.latency_ms != null ? `${h.latency_ms} ms` : '-'}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
