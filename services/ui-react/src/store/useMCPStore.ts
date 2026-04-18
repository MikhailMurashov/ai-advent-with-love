import { create } from 'zustand'
import {
  getMCPServers,
  createMCPServer,
  deleteMCPServer,
  enableMCPServer,
  disableMCPServer,
} from '@/api/client'
import type { MCPServer, CreateMCPServerParams } from '@/api/types'

interface MCPState {
  servers: MCPServer[]
  isLoading: boolean
  error: string | null

  loadServers: () => Promise<void>
  addServer: (params: CreateMCPServerParams) => Promise<void>
  removeServer: (id: string) => Promise<void>
  toggleServer: (id: string, enabled: boolean) => Promise<void>
}

export const useMCPStore = create<MCPState>((set, get) => ({
  servers: [],
  isLoading: false,
  error: null,

  loadServers: async () => {
    set({ isLoading: true, error: null })
    try {
      const servers = await getMCPServers()
      set({ servers, isLoading: false })
    } catch (err) {
      set({ error: String(err), isLoading: false })
    }
  },

  addServer: async (params) => {
    const server = await createMCPServer(params)
    set((state) => ({ servers: [...state.servers, server] }))
  },

  removeServer: async (id) => {
    await deleteMCPServer(id)
    set((state) => ({ servers: state.servers.filter((s) => s.id !== id) }))
  },

  toggleServer: async (id, enabled) => {
    const server = enabled ? await enableMCPServer(id) : await disableMCPServer(id)
    set((state) => ({
      servers: state.servers.map((s) => (s.id === id ? server : s)),
    }))
    // Reload all servers after toggle since MCP state changes on backend
    await get().loadServers()
  },
}))
