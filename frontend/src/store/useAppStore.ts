import { create } from 'zustand'

interface Agent {
  id: string
  name: string
  status: 'online' | 'offline' | 'busy'
  runtime: string
  model: string
  healthy: boolean
}

interface AppState {
  agents: Agent[]
  currentProject: string | null
  setAgents: (agents: Agent[]) => void
  updateAgentStatus: (id: string, status: Agent['status']) => void
  setProject: (id: string | null) => void
}

export const useAppStore = create<AppState>((set) => ({
  agents: [],
  currentProject: null,
  setAgents: (agents) => set({ agents }),
  updateAgentStatus: (id, status) =>
    set((state) => ({
      agents: state.agents.map((a) => (a.id === id ? { ...a, status } : a)),
    })),
  setProject: (id) => set({ currentProject: id }),
}))
