import { create } from 'zustand'
import type { DisplayMessage, TokenStats } from '@/api/types'

interface ToolStepParams {
  name: string
  args: object
  toolCallId: string
  result: string
}

interface ChatState {
  messages: DisplayMessage[]
  isStreaming: boolean
  streamingContent: string
  error: string | null

  setMessages: (messages: DisplayMessage[]) => void
  startStreaming: () => void
  appendToken: (token: string) => void
  appendToolStep: (step: ToolStepParams) => void
  finalizeStream: (stats: TokenStats) => void
  addUserMessage: (content: string) => void
  setError: (error: string | null) => void
  reset: () => void
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isStreaming: false,
  streamingContent: '',
  error: null,

  setMessages: (messages) => set({ messages }),

  startStreaming: () => set({ isStreaming: true, streamingContent: '' }),

  appendToken: (token) => {
    set((state) => ({
      isStreaming: true,
      streamingContent: state.streamingContent + token,
    }))
  },

  appendToolStep: (step) => {
    const toolMsg: DisplayMessage = {
      kind: 'tool_step',
      name: step.name,
      args: step.args,
      result: step.result,
      toolCallId: step.toolCallId,
    }
    set((state) => ({ messages: [...state.messages, toolMsg] }))
  },

  finalizeStream: (stats) => {
    const { streamingContent } = get()
    if (!streamingContent) {
      set({ isStreaming: false, streamingContent: '' })
      return
    }
    const assistantMsg: DisplayMessage = {
      kind: 'message',
      role: 'assistant',
      content: streamingContent,
      stats,
    }
    set((state) => ({
      messages: [...state.messages, assistantMsg],
      isStreaming: false,
      streamingContent: '',
    }))
  },

  addUserMessage: (content) => {
    const userMsg: DisplayMessage = { kind: 'message', role: 'user', content }
    set((state) => ({ messages: [...state.messages, userMsg] }))
  },

  setError: (error) => set({ error, isStreaming: false }),

  reset: () =>
    set({ messages: [], isStreaming: false, streamingContent: '', error: null }),
}))
