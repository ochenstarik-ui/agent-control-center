import { useEffect, useState } from 'react'
import { getMemory, putMemory } from '../api'

export default function Memory() {
  const [content, setContent] = useState('')
  const [saved, setSaved] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    getMemory().then((r) => setContent(r.data.content))
  }, [])

  async function handleSave() {
    setLoading(true)
    try {
      await putMemory(content)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2>Memory</h2>
      <div className="card memory-editor">
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Global project memory (MARKDOWN supported in MVP)..."
        />
        <div>
          <button onClick={handleSave} disabled={loading}>
            {loading ? 'Saving...' : 'Save Memory'}
          </button>
          {saved && <span style={{ marginLeft: 12, color: 'var(--accent-2)' }}>Saved</span>}
        </div>
      </div>
    </div>
  )
}
