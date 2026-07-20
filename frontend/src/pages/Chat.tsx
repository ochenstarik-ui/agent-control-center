import { useState } from 'react'
import { createRun, type Run } from '../api'

const PROFILES = ['worker-code', 'worker-fast', 'worker-research', 'worker-review']

export default function Chat() {
  const [profile, setProfile] = useState(PROFILES[0])
  const [prompt, setPrompt] = useState('')
  const [run, setRun] = useState<Run | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!prompt.trim()) return
    setLoading(true)
    setError(null)
    setRun(null)
    try {
      const r = await createRun(profile, prompt)
      setRun(r.data)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2>Chat</h2>
      <form onSubmit={handleSubmit} className="card memory-editor">
        <label>
          Worker profile
          <select value={profile} onChange={(e) => setProfile(e.target.value)}>
            {PROFILES.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </label>
        <label>
          Message / task
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter task or message for the agent..."
          />
        </label>
        <div>
          <button type="submit" disabled={loading || !prompt.trim()}>
            {loading ? 'Running...' : 'Send'}
          </button>
        </div>
        {error && <div className="status-error">{error}</div>}
      </form>

      {run && (
        <div className="card run-list">
          <div className="run-item">
            <strong>{run.profile}</strong> — <span className={`status-${run.status}`}>{run.status}</span>
            <pre>{run.error ? `ERROR: ${run.error}` : run.output || '(no output)'}</pre>
          </div>
        </div>
      )}
    </div>
  )
}
