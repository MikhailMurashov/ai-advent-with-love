import { MessageSquarePlus } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { useAppStore } from '@/store/useAppStore'
import { useSessionSettingsStore } from '@/store/useSessionSettingsStore'

export function HomePage() {
  const navigate = useNavigate()
  const isLoading = useAppStore((s) => s.isLoading)
  const createSession = useAppStore((s) => s.createSession)
  const settings = useSessionSettingsStore()

  const handleNewChat = async () => {
    const session = await createSession({
      title: 'Новая сессия',
      model_key: settings.model,
      strategy_type: settings.strategy,
      system_prompt: settings.systemPrompt,
    })
    navigate(`/chat/${session.id}`)
  }

  return (
    <div className="flex flex-col items-center justify-center h-full gap-6 text-center px-8">
      <div className="flex flex-col items-center gap-3">
        <div className="rounded-2xl bg-indigo-100 p-4">
          <MessageSquarePlus size={40} className="text-indigo-600" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900">Добро пожаловать в AI Chat</h1>
        <p className="text-gray-500 max-w-sm text-sm leading-relaxed">
          Выберите сессию из списка слева или создайте новый чат,
          чтобы начать общение с AI-ассистентом.
        </p>
      </div>

      <Button
        variant="primary"
        size="lg"
        disabled={isLoading}
        onClick={() => void handleNewChat()}
      >
        <MessageSquarePlus size={18} />
        Создать новый чат
      </Button>
    </div>
  )
}
