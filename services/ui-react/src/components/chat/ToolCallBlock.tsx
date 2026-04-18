import { useState } from 'react'
import { ChevronDown, ChevronRight, Wrench } from 'lucide-react'

interface Props {
  name: string
  args: object
  result: string
}

export function ToolCallBlock({ name, args, result }: Props) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="my-2 rounded-lg border border-yellow-200 bg-yellow-50 overflow-hidden">
      <button
        onClick={() => setIsOpen((v) => !v)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left hover:bg-yellow-100 transition-colors"
        aria-expanded={isOpen}
      >
        <Wrench size={14} className="text-yellow-600 flex-shrink-0" />
        <span className="text-sm font-medium text-yellow-800 flex-1 truncate">{name}</span>
        {isOpen ? (
          <ChevronDown size={14} className="text-yellow-600 flex-shrink-0" />
        ) : (
          <ChevronRight size={14} className="text-yellow-600 flex-shrink-0" />
        )}
      </button>

      {isOpen && (
        <div className="border-t border-yellow-200 px-3 py-2 space-y-2">
          <div>
            <p className="text-xs font-semibold text-yellow-700 mb-1">Аргументы</p>
            <pre className="text-xs overflow-auto bg-yellow-100 rounded p-2 text-yellow-900 max-h-40 whitespace-pre-wrap break-words">
              {JSON.stringify(args, null, 2)}
            </pre>
          </div>
          <div>
            <p className="text-xs font-semibold text-yellow-700 mb-1">Результат</p>
            <pre className="text-xs overflow-auto bg-yellow-100 rounded p-2 text-yellow-900 max-h-60 whitespace-pre-wrap break-words">
              {result}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}
