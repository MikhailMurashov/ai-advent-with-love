import { useAppStore } from '@/store/useAppStore'
import { SessionItem } from './SessionItem'

export function SessionList() {
  const sessions = useAppStore((s) => s.sessions)

  if (sessions.length === 0) {
    return (
      <div className="flex-1 flex items-start justify-center pt-8 px-4">
        <p className="text-center text-xs text-gray-500">
          Нет сессий. Создайте новый чат.
        </p>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto py-2 px-2 space-y-0.5">
      {sessions.map((session) => (
        <SessionItem key={session.id} session={session} />
      ))}
    </div>
  )
}
