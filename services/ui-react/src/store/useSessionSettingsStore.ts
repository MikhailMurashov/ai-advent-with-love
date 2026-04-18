import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface SessionSettings {
  model: string
  strategy: string
  systemPrompt: string
  temperature: number
  setModel: (v: string) => void
  setStrategy: (v: string) => void
  setSystemPrompt: (v: string) => void
  setTemperature: (v: number) => void
}

export const useSessionSettingsStore = create<SessionSettings>()(
  persist(
    (set) => ({
      model: 'gigachat/GigaChat-2',
      strategy: 'sliding_window_summary',
      systemPrompt: '',
      temperature: 0.7,
      setModel: (v) => set({ model: v }),
      setStrategy: (v) => set({ strategy: v }),
      setSystemPrompt: (v) => set({ systemPrompt: v }),
      setTemperature: (v) => set({ temperature: v }),
    }),
    { name: 'session-settings' },
  ),
)
