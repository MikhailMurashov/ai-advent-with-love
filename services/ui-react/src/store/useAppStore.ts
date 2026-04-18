import { create } from 'zustand'
import { getOrCreateUser, getUserSessions, createSession, deleteSession } from '@/api/client'
import type { SessionInfo, CreateSessionParams } from '@/api/types'

const USERNAME = 'guest'

interface AppState {
  userId: string | null
  username: string
  sessions: SessionInfo[]
  isLoading: boolean
  error: string | null

  initUser: () => Promise<void>
  loadSessions: () => Promise<void>
  createSession: (
    opts: Omit<CreateSessionParams, 'user_id'>,
  ) => Promise<SessionInfo>
  deleteSession: (id: string) => Promise<void>
}

export const useAppStore = create<AppState>((set, get) => ({
  userId: null,
  username: USERNAME,
  sessions: [],
  isLoading: false,
  error: null,

  initUser: async () => {
    set({ isLoading: true, error: null })
    try {
      const user = await getOrCreateUser(USERNAME)
      set({ userId: user.id, isLoading: false })
      await get().loadSessions()
    } catch (err) {
      set({ error: String(err), isLoading: false })
    }
  },

  loadSessions: async () => {
    const { userId } = get()
    if (!userId) return
    try {
      const sessions = await getUserSessions(userId)
      set({ sessions })
    } catch (err) {
      set({ error: String(err) })
    }
  },

  createSession: async (opts) => {
    const { userId } = get()
    if (!userId) throw new Error('User not initialized')
    const session = await createSession({ ...opts, user_id: userId })
    set((state) => ({ sessions: [session, ...state.sessions] }))
    return session
  },

  deleteSession: async (id: string) => {
    await deleteSession(id)
    set((state) => ({
      sessions: state.sessions.filter((s) => s.id !== id),
    }))
  },
}))
