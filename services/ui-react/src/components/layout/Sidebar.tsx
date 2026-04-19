import { Plus, MessageSquare } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { SessionList } from '@/components/sidebar/SessionList'

export function Sidebar() {
  const navigate = useNavigate()

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
          onClick={() => navigate('/')}
          className="w-full flex items-center justify-center gap-2 rounded-lg
            bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700
            px-3 py-2 text-sm font-medium text-white transition-colors"
        >
          <Plus size={16} />
          Новый чат
        </button>
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
