import { useEffect } from 'react'
import { Bell, X } from 'lucide-react'

interface NotificationToastProps {
  id: string
  content: string
  onClose: () => void
}

export function NotificationToast({ content, onClose }: NotificationToastProps) {
  useEffect(() => {
    const timer = setTimeout(onClose, 60_000)
    return () => clearTimeout(timer)
  }, [onClose])

  return (
    <div className="flex items-start gap-3 bg-gray-800 border border-gray-700 rounded-lg shadow-lg p-4 min-w-72 max-w-sm">
      <Bell className="text-blue-400 mt-0.5 shrink-0" size={18} />
      <p className="text-white text-sm flex-1 leading-relaxed">{content}</p>
      <button
        onClick={onClose}
        className="text-gray-400 hover:text-white transition-colors shrink-0 mt-0.5"
        aria-label="Закрыть"
      >
        <X size={16} />
      </button>
    </div>
  )
}
