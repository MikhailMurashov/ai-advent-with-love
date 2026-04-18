import { useState, useRef, useCallback } from 'react'
import { Send } from 'lucide-react'
import type { WsSendPayload } from '@/api/types'

interface Props {
  onSend: (payload: WsSendPayload) => void
  disabled?: boolean
}

export function ChatInput({ onSend, disabled = false }: Props) {
  const [text, setText] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = useCallback(() => {
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSend({ content: trimmed })
    setText('')
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }, [text, disabled, onSend])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value)
    // Auto-resize
    const el = e.target
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`
  }

  const canSend = text.trim().length > 0 && !disabled

  return (
    <div className="border-t border-gray-200 bg-white px-4 py-3">
      <div className="max-w-3xl mx-auto">
      <div className="flex items-end gap-2 rounded-xl border border-gray-300 bg-gray-50 px-3 py-2
        focus-within:border-indigo-400 focus-within:ring-1 focus-within:ring-indigo-400 transition-all">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder="Напишите сообщение... (Enter — отправить, Shift+Enter — новая строка)"
          disabled={disabled}
          rows={1}
          className="flex-1 resize-none bg-transparent text-sm text-gray-900 placeholder:text-gray-400
            focus:outline-none disabled:cursor-not-allowed disabled:opacity-50 max-h-[200px]"
          style={{ minHeight: '24px' }}
        />
        <button
          onClick={handleSend}
          disabled={!canSend}
          className={[
            'flex-shrink-0 rounded-lg p-1.5 transition-colors',
            canSend
              ? 'bg-indigo-600 text-white hover:bg-indigo-500'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed',
          ].join(' ')}
          aria-label="Отправить"
        >
          <Send size={16} />
        </button>
      </div>
      </div>
    </div>
  )
}
