import { useState } from 'react'
import { Plus, MessageSquare } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { SessionList } from '@/components/sidebar/SessionList'
import { useAppStore } from '@/store/useAppStore'
import { useSessionSettingsStore } from '@/store/useSessionSettingsStore'

export function Sidebar() {
  const [createError, setCreateError] = useState<string | null>(null)
  const isLoading = useAppStore((s) => s.isLoading)
  const createSession = useAppStore((s) => s.createSession)
  const settings = useSessionSettingsStore()
  const navigate = useNavigate()

  const handleNewChat = async () => {
    setCreateError(null)
    try {
      const session = await createSession({
        title: 'Новая сессия',
        model_key: settings.model,
        strategy_type: settings.strategy,
        system_prompt: settings.systemPrompt,
      })
      navigate(`/chat/${session.id}`)
    } catch (err) {
      setCreateError(String(err))
    }
  }

  return (
    <aside className="flex flex-col w-[260px] flex-shrink-0 bg-gray-900 text-gray-100 border-r border-gray-700 h-screen">
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-3 border-b border-gray-700">
        <MessageSquare size={18} className="text-indigo-400 flex-shrink-0" />
        <span className="font-semibold text-sm truncate">AI Chat</span>
      </div>

      {/* New Chat Button */}
      <div className="px-3 pt-3">
        <button
          onClick={() => void handleNewChat()}
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-2 rounded-lg
            bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700
            px-3 py-2 text-sm font-medium text-white transition-colors
            disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Plus size={16} />
          Новый чат
        </button>
        {createError && (
          <p className="mt-1.5 text-xs text-red-400 text-center">{createError}</p>
        )}
      </div>

      {/* Sessions */}
      <div className="flex-1 overflow-hidden flex flex-col mt-2">
        <p className="px-4 py-1.5 text-xs font-semibold uppercase tracking-wider text-gray-500">
          Сессии
        </p>
        <SessionList />
      </div>
    </aside>
  )
}
