import { useEffect, useRef } from 'react'
import { useChatStore } from '@/store/useChatStore'
import { MessageBubble } from './MessageBubble'
import { StreamingBubble } from './StreamingBubble'

export function MessageList() {
  const messages = useChatStore((s) => s.messages)
  const isStreaming = useChatStore((s) => s.isStreaming)
  const streamingContent = useChatStore((s) => s.streamingContent)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  return (
    <div className="flex-1 overflow-y-auto py-6">
      <div className="max-w-3xl mx-auto px-4 space-y-4">
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} message={msg} />
        ))}
        {isStreaming && (
          <StreamingBubble content={streamingContent} />
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
