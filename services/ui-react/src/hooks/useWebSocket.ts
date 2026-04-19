import { useEffect, useRef, useCallback } from 'react'
import { buildWsUrl } from '@/api/client'
import { useChatStore } from '@/store/useChatStore'
import { useNotificationStore } from '@/store/useNotificationStore'
import type { WsServerEvent, WsSendPayload } from '@/api/types'

const USERNAME = 'guest'
const MAX_RETRIES = 3
const BACKOFF_BASE_MS = 1000

export function useWebSocket(
  sessionId: string,
  options?: { onOpen?: () => void },
): {
  sendMessage: (payload: WsSendPayload) => void
} {
  const wsRef = useRef<WebSocket | null>(null)
  const retriesRef = useRef(0)
  const shouldReconnectRef = useRef(true)
  const sessionIdRef = useRef(sessionId)
  const onOpenRef = useRef(options?.onOpen)
  onOpenRef.current = options?.onOpen

  const appendToken = useChatStore((s) => s.appendToken)
  const appendToolStep = useChatStore((s) => s.appendToolStep)
  const finalizeStream = useChatStore((s) => s.finalizeStream)
  const setError = useChatStore((s) => s.setError)
  const addNotification = useNotificationStore((s) => s.addNotification)

  sessionIdRef.current = sessionId

  const connect = useCallback(() => {
    if (!sessionIdRef.current) return

    const url = buildWsUrl(sessionIdRef.current, USERNAME)
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      retriesRef.current = 0
      onOpenRef.current?.()
    }

    ws.onmessage = (event: MessageEvent<string>) => {
      let parsed: WsServerEvent
      try {
        parsed = JSON.parse(event.data) as WsServerEvent
      } catch {
        return
      }

      switch (parsed.type) {
        case 'token':
          appendToken(parsed.content)
          break
        case 'tool_step':
          appendToolStep({
            name: parsed.name,
            args: parsed.args,
            toolCallId: parsed.tool_call_id,
            result: parsed.content,
          })
          break
        case 'done':
          finalizeStream(parsed.stats)
          break
        case 'error':
          setError(parsed.message)
          break
        case 'notification':
          addNotification(parsed.content)
          break
      }
    }

    ws.onerror = () => {
      setError('WebSocket connection error')
    }

    ws.onclose = () => {
      wsRef.current = null
      if (!shouldReconnectRef.current) return
      if (retriesRef.current >= MAX_RETRIES) {
        setError('Connection lost. Please refresh the page.')
        return
      }
      const delay = BACKOFF_BASE_MS * Math.pow(2, retriesRef.current)
      retriesRef.current += 1
      setTimeout(() => {
        if (shouldReconnectRef.current) connect()
      }, delay)
    }
  }, [appendToken, appendToolStep, finalizeStream, setError, addNotification])

  useEffect(() => {
    shouldReconnectRef.current = true
    retriesRef.current = 0
    connect()

    return () => {
      shouldReconnectRef.current = false
      wsRef.current?.close()
      wsRef.current = null
    }
  }, [sessionId, connect])

  const sendMessage = useCallback((payload: WsSendPayload) => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      setError('Not connected. Please wait a moment and try again.')
      return
    }
    ws.send(JSON.stringify(payload))
  }, [setError])

  return { sendMessage }
}
