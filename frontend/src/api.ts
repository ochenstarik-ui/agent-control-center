const API_BASE = ''

async function api<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, opts)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: { message: res.statusText } }))
    throw new Error(err.error?.message || res.statusText)
  }
  return res.json() as Promise<T>
}

export interface HealthRow {
  profile: string
  current_model: string | null
  provider: string | null
  status: string
  latency_ms: number | null
}

export interface Run {
  id: string
  profile: string
  prompt: string
  status: string
  created_at: string
  updated_at: string
  output: string | null
  error: string | null
}

export interface Project {
  id: string
  key: string
  name: string
  status: string
}

export interface ApiData<T> {
  data: T
  meta: { request_id: string }
}

export const getHealth = () => api<ApiData<HealthRow[]>>(`/api/v1/agents/health`, { method: 'POST' })

export const listProjects = () => api<ApiData<Project[]>>(`/api/v1/projects`)

export const listRuns = () => api<ApiData<Run[]>>(`/api/v1/runs`)

export const createRun = (profile: string, prompt: string) =>
  api<ApiData<Run>>(`/api/v1/runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ profile, prompt }),
  })

export const getMemory = () => api<ApiData<{ key: string; content: string }>>(`/api/v1/memory/global`)

export const putMemory = (content: string) =>
  api<ApiData<{ key: string; content: string; updated_at: string }>>(`/api/v1/memory/global`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  })
