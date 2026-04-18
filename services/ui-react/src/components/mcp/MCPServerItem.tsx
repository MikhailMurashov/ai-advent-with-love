import { useState } from 'react'
import { Trash2, ExternalLink } from 'lucide-react'
import { useMCPStore } from '@/store/useMCPStore'
import type { MCPServer } from '@/api/types'

interface Props {
  server: MCPServer
}

export function MCPServerItem({ server }: Props) {
  const removeServer = useMCPStore((s) => s.removeServer)
  const toggleServer = useMCPStore((s) => s.toggleServer)
  const [isLoading, setIsLoading] = useState(false)

  const handleToggle = async () => {
    setIsLoading(true)
    try {
      await toggleServer(server.id, !server.enabled)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRemove = async () => {
    if (!confirm(`Удалить сервер "${server.name}"?`)) return
    await removeServer(server.id)
  }

  return (
    <div className="flex items-start gap-3 rounded-lg border border-gray-700 bg-gray-800 p-3">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm text-gray-100 truncate">{server.name}</span>
          <a
            href={server.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-500 hover:text-gray-300 flex-shrink-0"
            aria-label="Открыть URL сервера"
          >
            <ExternalLink size={12} />
          </a>
        </div>
        {server.description && (
          <p className="text-xs text-gray-400 mt-0.5 truncate">{server.description}</p>
        )}
        <p className="text-xs text-gray-500 mt-0.5 truncate font-mono">{server.url}</p>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        <button
          onClick={() => void handleToggle()}
          disabled={isLoading}
          className={[
            'relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent',
            'transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-800',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            server.enabled ? 'bg-indigo-600' : 'bg-gray-600',
          ].join(' ')}
          role="switch"
          aria-checked={server.enabled}
          aria-label={server.enabled ? 'Отключить сервер' : 'Включить сервер'}
        >
          <span
            className={[
              'pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0',
              'transition duration-200 ease-in-out',
              server.enabled ? 'translate-x-4' : 'translate-x-0',
            ].join(' ')}
          />
        </button>
        <button
          onClick={() => void handleRemove()}
          className="rounded p-1 text-gray-500 hover:text-red-400 hover:bg-gray-700 transition-colors"
          aria-label="Удалить сервер"
        >
          <Trash2 size={14} />
        </button>
      </div>
    </div>
  )
}
