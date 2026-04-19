import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Settings, Wrench } from 'lucide-react'
import { ChatInput } from '@/components/chat/ChatInput'
import { ChatSettingsModal } from '@/components/modals/ChatSettingsModal'
import { MCPServersPanel } from '@/components/mcp/MCPServersPanel'
import { useAppStore } from '@/store/useAppStore'
import { useSessionSettingsStore } from '@/store/useSessionSettingsStore'
import type { WsSendPayload } from '@/api/types'

export function HomePage() {
  const navigate = useNavigate()
  const isLoading = useAppStore((s) => s.isLoading)
  const createSession = useAppStore((s) => s.createSession)
  const settings = useSessionSettingsStore()

  const [showSettings, setShowSettings] = useState(false)
  const [showMCP, setShowMCP] = useState(false)

  const handleSend = async (payload: WsSendPayload) => {
    const title = payload.content.split(' ').slice(0, 3).join(' ')
    const session = await createSession({
      title,
      model_key: settings.model,
      strategy_type: settings.strategy,
      system_prompt: settings.systemPrompt,
    })
    navigate(`/chat/${session.id}`, { state: { firstMessage: payload.content } })
  }

  return (
    <div className="flex flex-col h-full items-center justify-center">
      <div className="w-full max-w-3xl px-4">
        <p className="text-sm text-gray-400 text-center mb-4">Начните разговор</p>

        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden [&>div:first-child]:border-t-0">
          <ChatInput onSend={(p) => void handleSend(p)} disabled={isLoading} />

          <div className="flex items-center gap-2 px-3 py-2 border-t border-gray-100">
            <button
              onClick={() => setShowSettings(true)}
              title="Настройки чата"
              className="flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs text-gray-500
                hover:bg-gray-100 hover:text-gray-800 transition-colors"
            >
              <Settings size={13} />
              Настройки
            </button>
            <button
              onClick={() => setShowMCP(true)}
              title="MCP-серверы"
              className="flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs text-gray-500
                hover:bg-gray-100 hover:text-gray-800 transition-colors"
            >
              <Wrench size={13} />
              MCP
            </button>
          </div>
        </div>
      </div>

      {showSettings && <ChatSettingsModal onClose={() => setShowSettings(false)} />}
      {showMCP && <MCPServersPanel onClose={() => setShowMCP(false)} />}
    </div>
  )
}
