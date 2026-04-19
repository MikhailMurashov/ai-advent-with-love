import { useNotificationStore } from '@/store/useNotificationStore'
import { NotificationToast } from './NotificationToast'

export function NotificationContainer() {
  const notifications = useNotificationStore((s) => s.notifications)
  const removeNotification = useNotificationStore((s) => s.removeNotification)

  if (notifications.length === 0) return null

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2">
      {notifications.map((n) => (
        <NotificationToast
          key={n.id}
          id={n.id}
          content={n.content}
          onClose={() => removeNotification(n.id)}
        />
      ))}
    </div>
  )
}
