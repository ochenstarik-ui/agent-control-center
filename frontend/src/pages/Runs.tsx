import { useEffect, useState } from 'react'
import { listRuns, type Run } from '../api'

export default function Runs() {
  const [runs, setRuns] = useState<Run[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const r = await listRuns()
        setRuns(r.data)
      } finally {
        setLoading(false)
      }
    }
    load()
    const id = setInterval(load, 5000)
    return () => clearInterval(id)
  }, [])

  if (loading) return <div className="card">Loading...</div>

  return (
    <div>
      <h2>Runs</h2>
      <div className="run-list">
        {runs.length === 0 && <div className="card">No runs yet.</div>}
        {runs.map((run) => (
          <div key={run.id} className="run-item">
            <div>
              <strong>{run.profile}</strong>{' '}
              <span className={`status-${run.status}`}>{run.status}</span>
              <span style={{ color: 'var(--muted)', marginLeft: 12, fontSize: '0.85rem' }}>
                {new Date(run.created_at).toLocaleString()}
              </span>
            </div>
            <p>{run.prompt}</p>
            {(run.output || run.error) && (
              <pre>{run.error ? `ERROR: ${run.error}` : run.output}</pre>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
