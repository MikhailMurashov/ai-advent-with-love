import { useEffect, useState } from 'react'
import { Plus, X } from 'lucide-react'
import { useMCPStore } from '@/store/useMCPStore'
import { MCPServerItem } from './MCPServerItem'
import { AddMCPServerModal } from './AddMCPServerModal'
import { Button } from '@/components/ui/Button'

interface Props {
  onClose: () => void
}

export function MCPServersPanel({ onClose }: Props) {
  const { servers, isLoading, error, loadServers } = useMCPStore()
  const [showAddModal, setShowAddModal] = useState(false)

  useEffect(() => {
    void loadServers()
  }, [loadServers])

  return (
    <>
      <div className="fixed inset-0 z-40 flex">
        <div
          className="fixed inset-0 bg-black/40"
          onClick={onClose}
          aria-hidden="true"
        />
        <div className="relative ml-auto w-full max-w-sm bg-gray-900 border-l border-gray-700 flex flex-col h-full shadow-xl">
          <div className="flex items-center justify-between border-b border-gray-700 px-4 py-3">
            <h2 className="text-base font-semibold text-gray-100">MCP-серверы</h2>
            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-700 hover:text-white transition-colors"
              aria-label="Закрыть"
            >
              <X size={18} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            {isLoading && (
              <p className="text-sm text-gray-400 text-center py-4">Загрузка...</p>
            )}
            {error && (
              <p className="text-sm text-red-400 text-center py-4">{error}</p>
            )}
            {!isLoading && !error && servers.length === 0 && (
              <p className="text-sm text-gray-500 text-center py-4">
                Нет зарегистрированных серверов
              </p>
            )}
            {servers.map((server) => (
              <MCPServerItem key={server.id} server={server} />
            ))}
          </div>

          <div className="border-t border-gray-700 p-4">
            <Button
              variant="primary"
              className="w-full"
              onClick={() => setShowAddModal(true)}
            >
              <Plus size={16} />
              Добавить сервер
            </Button>
          </div>
        </div>
      </div>

      {showAddModal && (
        <AddMCPServerModal onClose={() => setShowAddModal(false)} />
      )}
    </>
  )
}
