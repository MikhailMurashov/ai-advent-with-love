import { Modal } from './Modal'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Select'
import { Slider } from '@/components/ui/Slider'
import { Textarea } from '@/components/ui/Textarea'
import { useSessionSettingsStore } from '@/store/useSessionSettingsStore'

const MODELS = [
  { value: 'gigachat/GigaChat-2', label: 'GigaChat-2' },
  { value: 'gigachat/GigaChat-2-Pro', label: 'GigaChat-2-Pro' },
  { value: 'gigachat/GigaChat-2-Max', label: 'GigaChat-2-Max' },
]

const STRATEGIES = [
  { value: 'sliding_window_summary', label: 'Sliding Window + Summary' },
  { value: 'branching', label: 'Branching' },
]

interface Props {
  onClose: () => void
}

export function ChatSettingsModal({ onClose }: Props) {
  const { model, strategy, systemPrompt, temperature, setModel, setStrategy, setSystemPrompt, setTemperature } =
    useSessionSettingsStore()

  return (
    <Modal title="Настройки чата" onClose={onClose}>
      <div className="flex flex-col gap-4">
        <Select
          id="settings-model"
          label="Модель"
          value={model}
          onChange={(e) => setModel(e.target.value)}
        >
          {MODELS.map((m) => (
            <option key={m.value} value={m.value}>
              {m.label}
            </option>
          ))}
        </Select>

        <Slider
          id="settings-temperature"
          label="Температура"
          valueDisplay={temperature.toFixed(1)}
          min={0}
          max={1}
          step={0.1}
          value={temperature}
          onChange={(e) => setTemperature(parseFloat(e.target.value))}
        />

        <Select
          id="settings-strategy"
          label="Стратегия контекста"
          value={strategy}
          onChange={(e) => setStrategy(e.target.value)}
        >
          {STRATEGIES.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </Select>

        <Textarea
          id="settings-system-prompt"
          label="System Prompt (опционально)"
          placeholder="Вы — полезный AI-ассистент..."
          value={systemPrompt}
          onChange={(e) => setSystemPrompt(e.target.value)}
          rows={3}
        />

        <div className="flex justify-end pt-1">
          <Button variant="primary" type="button" onClick={onClose}>
            Применить
          </Button>
        </div>
      </div>
    </Modal>
  )
}
