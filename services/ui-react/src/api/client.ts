import type {
  User,
  SessionInfo,
  CreateSessionParams,
  DbMessage,
  MCPServer,
  CreateMCPServerParams,
} from './types'

const BASE_URL = import.meta.env.VITE_API_URL ?? ''

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(`HTTP ${res.status}: ${text}`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

// Users
export async function getOrCreateUser(username: string): Promise<User> {
  return request<User>(`/api/users/${encodeURIComponent(username)}`)
}

// Sessions
export async function getUserSessions(userId: string): Promise<SessionInfo[]> {
  return request<SessionInfo[]>(`/api/users/${encodeURIComponent(userId)}/sessions`)
}

export async function createSession(params: CreateSessionParams): Promise<SessionInfo> {
  return request<SessionInfo>('/api/sessions', {
    method: 'POST',
    body: JSON.stringify(params),
  })
}

export async function deleteSession(sessionId: string): Promise<void> {
  return request<void>(`/api/sessions/${encodeURIComponent(sessionId)}`, {
    method: 'DELETE',
  })
}

export async function getSessionMessages(sessionId: string): Promise<DbMessage[]> {
  return request<DbMessage[]>(`/api/sessions/${encodeURIComponent(sessionId)}/messages`)
}

// MCP Servers
export async function getMCPServers(): Promise<MCPServer[]> {
  return request<MCPServer[]>('/api/mcp-servers')
}

export async function createMCPServer(params: CreateMCPServerParams): Promise<MCPServer> {
  return request<MCPServer>('/api/mcp-servers', {
    method: 'POST',
    body: JSON.stringify(params),
  })
}

export async function deleteMCPServer(id: string): Promise<void> {
  return request<void>(`/api/mcp-servers/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  })
}

export async function enableMCPServer(id: string): Promise<MCPServer> {
  return request<MCPServer>(`/api/mcp-servers/${encodeURIComponent(id)}/enable`, {
    method: 'PATCH',
  })
}

export async function disableMCPServer(id: string): Promise<MCPServer> {
  return request<MCPServer>(`/api/mcp-servers/${encodeURIComponent(id)}/disable`, {
    method: 'PATCH',
  })
}

// WebSocket URL builder
export function buildWsUrl(sessionId: string, username: string): string {
  const base = BASE_URL || window.location.origin
  const wsBase = base.replace(/^http:\/\//, 'ws://').replace(/^https:\/\//, 'wss://')
  return `${wsBase}/ws/chat/${encodeURIComponent(sessionId)}?username=${encodeURIComponent(username)}`
}
