import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { Settings, Wrench } from 'lucide-react'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useChatStore } from '@/store/useChatStore'
import { useAppStore } from '@/store/useAppStore'
import { useSessionSettingsStore } from '@/store/useSessionSettingsStore'
import { getSessionMessages } from '@/api/client'
import { MessageList } from './MessageList'
import { ChatInput } from './ChatInput'
import { ChatSettingsModal } from '@/components/modals/ChatSettingsModal'
import { MCPServersPanel } from '@/components/mcp/MCPServersPanel'
import type { DbMessage, DisplayMessage, ToolCall, TokenStats, WsSendPayload } from '@/api/types'

function parseDbMessages(dbMessages: DbMessage[]): DisplayMessage[] {
  const result: DisplayMessage[] = []

  for (let i = 0; i < dbMessages.length; i++) {
    const msg = dbMessages[i]
    if (!msg) continue

    if (msg.role === 'user') {
      result.push({ kind: 'message', role: 'user', content: msg.content })
      continue
    }

    if (msg.role === 'assistant') {
      // Check if this assistant message has tool_calls
      if (msg.tool_calls) {
        let toolCalls: ToolCall[] = []
        try {
          const parsed: unknown = JSON.parse(msg.tool_calls)
          if (Array.isArray(parsed)) {
            toolCalls = parsed as ToolCall[]
          }
        } catch {
          // ignore parse error
        }

        if (toolCalls.length > 0) {
          // Collect subsequent 'tool' messages that correspond to these tool_calls
          const toolCallIds = new Set(toolCalls.map((tc) => tc.id))
          let j = i + 1
          const toolResults: Map<string, string> = new Map()

          while (j < dbMessages.length) {
            const next = dbMessages[j]
            if (!next || next.role !== 'tool') break
            // Tool message content is the result; match by tool_call_id stored separately
            // The tool role messages don't always have a direct id match,
            // but we can pair them in order with toolCalls
            const tcIndex = j - (i + 1)
            const tc = toolCalls[tcIndex]
            if (tc) {
              toolResults.set(tc.id, next.content)
            }
            j++
          }

          // Emit tool_step for each tool call
          for (const tc of toolCalls) {
            let args: object = {}
            try {
              const parsed: unknown = JSON.parse(tc.function.arguments)
              if (parsed !== null && typeof parsed === 'object' && !Array.isArray(parsed)) {
                args = parsed
              }
            } catch {
              args = { raw: tc.function.arguments }
            }

            const inSet = toolCallIds.has(tc.id)
            if (inSet) {
              result.push({
                kind: 'tool_step',
                name: tc.function.name,
                args,
                result: toolResults.get(tc.id) ?? '',
                toolCallId: tc.id,
              })
            }
          }

          // Skip the consumed tool messages
          i = j - 1
          continue
        }
      }

      // Regular assistant message (no tool_calls or empty tool_calls)
      const stats: TokenStats | undefined =
        msg.tokens_prompt !== null &&
        msg.tokens_completion !== null &&
        msg.elapsed_s !== null
          ? {
              prompt_tokens: msg.tokens_prompt,
              completion_tokens: msg.tokens_completion,
              elapsed_s: msg.elapsed_s,
            }
          : undefined

      result.push({
        kind: 'message',
        role: 'assistant',
        content: msg.content,
        ...(stats !== undefined ? { stats } : {}),
      })
      continue
    }

    // role === 'tool' without a preceding assistant with tool_calls — skip
  }

  return result
}

export function ChatPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  const sessions = useAppStore((s) => s.sessions)
  const messages = useChatStore((s) => s.messages)
  const setMessages = useChatStore((s) => s.setMessages)
  const addUserMessage = useChatStore((s) => s.addUserMessage)
  const isStreaming = useChatStore((s) => s.isStreaming)
  const error = useChatStore((s) => s.error)
  const setError = useChatStore((s) => s.setError)
  const reset = useChatStore((s) => s.reset)
  const startStreaming = useChatStore((s) => s.startStreaming)

  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [showMCP, setShowMCP] = useState(false)

  const settings = useSessionSettingsStore()

  // First message passed via navigation state (from HomePage lazy session creation)
  const firstMessageRef = useRef<string | null>(
    (location.state as { firstMessage?: string } | null)?.firstMessage ?? null,
  )
  // Ref to always call the latest handleSend from onOpen callback
  const handleSendRef = useRef<((payload: WsSendPayload) => void) | null>(null)

  // Clear location state immediately to prevent re-send on page refresh
  useEffect(() => {
    if (firstMessageRef.current) {
      window.history.replaceState({}, '')
    }
  }, [])

  const { sendMessage } = useWebSocket(sessionId ?? '', {
    onOpen: () => {
      const msg = firstMessageRef.current
      if (msg) {
        firstMessageRef.current = null
        handleSendRef.current?.({ content: msg })
      }
    },
  })

  // Validate session exists
  useEffect(() => {
    if (sessionId && sessions.length > 0) {
      const found = sessions.find((s) => s.id === sessionId)
      if (!found) navigate('/')
    }
  }, [sessionId, sessions, navigate])

  // Load history when session changes
  useEffect(() => {
    if (!sessionId) return

    reset()
    setIsLoadingHistory(true)

    getSessionMessages(sessionId)
      .then((dbMessages) => {
        const display = parseDbMessages(dbMessages)
        // Only overwrite store if history is non-empty.
        // If empty, reset() already cleared it — don't wipe a user message
        // that may have been added by the first-message auto-send via onOpen.
        if (display.length > 0) {
          setMessages(display)
        }
      })
      .catch((err: unknown) => {
        setError(`Ошибка загрузки истории: ${String(err)}`)
      })
      .finally(() => {
        setIsLoadingHistory(false)
      })
  }, [sessionId, reset, setMessages, setError])

  const session = sessions.find((s) => s.id === sessionId)
  const isEmpty = messages.length === 0 && !isStreaming && !isLoadingHistory

  const handleSend = (payload: WsSendPayload) => {
    addUserMessage(payload.content)
    startStreaming()
    sendMessage({ ...payload, params: { ...payload.params, temperature: settings.temperature } })
  }
  handleSendRef.current = handleSend

  const toolbar = (
    <div className="flex-shrink-0 border-t border-gray-100 bg-white px-4 pt-1.5 pb-4 flex justify-center">
      <div className="w-full max-w-3xl flex items-center gap-2">
        <button
          onClick={() => setShowSettings(true)}
          title="Настройки чата"
          className="flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs text-gray-500
            hover:bg-gray-100 hover:text-gray-800 transition-colors"
        >
          <Settings size={13} />
          Настройки
        </button>
        <button
          onClick={() => setShowMCP(true)}
          title="MCP-серверы"
          className="flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs text-gray-500
            hover:bg-gray-100 hover:text-gray-800 transition-colors"
        >
          <Wrench size={13} />
          MCP
        </button>
      </div>
    </div>
  )

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-gray-200 bg-white px-6 py-3">
        <h1 className="text-base font-semibold text-gray-900 truncate">
          {session?.title ?? 'Чат'}
        </h1>
        {session && (
          <p className="text-xs text-gray-500 mt-0.5">
            {session.model_key.split('/').pop()} · {session.strategy_type}
          </p>
        )}
      </div>

      {/* Error banner */}
      {error && !isLoadingHistory && (
        <div className="mx-4 mt-3 flex-shrink-0 flex items-center justify-between
          rounded-lg bg-red-50 border border-red-200 px-4 py-2">
          <p className="text-sm text-red-700">{error}</p>
          <button
            onClick={() => setError(null)}
            className="ml-3 text-red-500 hover:text-red-700 text-xs underline"
          >
            Закрыть
          </button>
        </div>
      )}

      {/* Loading */}
      {isLoadingHistory ? (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-sm text-gray-400">Загрузка истории...</p>
        </div>
      ) : isEmpty ? (
        /* Empty state: input centered on screen */
        <div className="flex-1 flex flex-col items-center justify-center px-4">
          <div className="w-full max-w-3xl">
            <p className="text-sm text-gray-400 text-center mb-4">Начните разговор</p>
            <ChatInput onSend={handleSend} disabled={isStreaming} />
            {toolbar}
          </div>
        </div>
      ) : (
        /* Has messages: normal scroll layout */
        <>
          <MessageList />
          <ChatInput onSend={handleSend} disabled={isStreaming} />
          {toolbar}
        </>
      )}

      {showSettings && <ChatSettingsModal onClose={() => setShowSettings(false)} />}
      {showMCP && <MCPServersPanel onClose={() => setShowMCP(false)} />}
    </div>
  )
}
