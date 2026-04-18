import { useState } from 'react'
import { Modal } from '@/components/modals/Modal'
import { Button } from '@/components/ui/Button'
import { useMCPStore } from '@/store/useMCPStore'

interface Props {
  onClose: () => void
}

export function AddMCPServerModal({ onClose }: Props) {
  const addServer = useMCPStore((s) => s.addServer)
  const [name, setName] = useState('')
  const [url, setUrl] = useState('')
  const [description, setDescription] = useState('')
  const [isAdding, setIsAdding] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsAdding(true)
    setError(null)
    try {
      await addServer({ name, url, description, enabled: true })
      onClose()
    } catch (err) {
      setError(String(err))
    } finally {
      setIsAdding(false)
    }
  }

  const inputClass =
    'rounded-lg border border-gray-600 bg-gray-800 px-3 py-2 text-sm text-gray-100 ' +
    'placeholder:text-gray-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 w-full'

  return (
    <Modal title="Добавить MCP-сервер" onClose={onClose}>
      <form onSubmit={(e) => void handleSubmit(e)} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <label htmlFor="mcp-name" className="text-sm font-medium text-gray-300">
            Название
          </label>
          <input
            id="mcp-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            placeholder="My MCP Server"
            className={inputClass}
          />
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="mcp-url" className="text-sm font-medium text-gray-300">
            URL
          </label>
          <input
            id="mcp-url"
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
            placeholder="http://localhost:8001"
            className={inputClass}
          />
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="mcp-desc" className="text-sm font-medium text-gray-300">
            Описание (опционально)
          </label>
          <input
            id="mcp-desc"
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Краткое описание"
            className={inputClass}
          />
        </div>

        {error && (
          <p className="rounded-lg bg-red-900/40 border border-red-700 px-3 py-2 text-sm text-red-300">
            {error}
          </p>
        )}

        <div className="flex justify-end gap-3 pt-1">
          <Button variant="secondary" type="button" onClick={onClose}>
            Отмена
          </Button>
          <Button variant="primary" type="submit" loading={isAdding}>
            Добавить
          </Button>
        </div>
      </form>
    </Modal>
  )
}
