import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Trash2 } from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'
import type { SessionInfo } from '@/api/types'

interface Props {
  session: SessionInfo
}

export function SessionItem({ session }: Props) {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const deleteSession = useAppStore((s) => s.deleteSession)
  const [isDeleting, setIsDeleting] = useState(false)

  const isActive = sessionId === session.id

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm(`Удалить сессию "${session.title}"?`)) return
    setIsDeleting(true)
    try {
      await deleteSession(session.id)
      if (isActive) navigate('/')
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => navigate(`/chat/${session.id}`)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') navigate(`/chat/${session.id}`)
      }}
      className={[
        'group flex items-start justify-between rounded-lg px-3 py-2.5 cursor-pointer',
        'transition-colors',
        isActive ? 'bg-gray-700' : 'hover:bg-gray-800',
      ].join(' ')}
    >
      <div className="flex-1 min-w-0">
        <p className="truncate text-sm font-medium text-gray-100">{session.title}</p>
        <p className="truncate text-xs text-gray-400 mt-0.5">{session.model_key.split('/').pop()}</p>
      </div>
      <button
        onClick={(e) => void handleDelete(e)}
        disabled={isDeleting}
        className={[
          'ml-2 flex-shrink-0 rounded p-1 text-gray-500',
          'opacity-0 group-hover:opacity-100 hover:text-red-400 hover:bg-gray-600',
          'transition-all disabled:opacity-30',
        ].join(' ')}
        aria-label="Удалить сессию"
      >
        <Trash2 size={14} />
      </button>
    </div>
  )
}
