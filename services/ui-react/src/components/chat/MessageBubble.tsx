import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { ToolCallBlock } from './ToolCallBlock'
import type { DisplayMessage, TokenStats } from '@/api/types'

interface StatsBadgeProps {
  stats: TokenStats
}

function StatsBadge({ stats }: StatsBadgeProps) {
  return (
    <div className="flex gap-3 mt-1.5 text-xs text-gray-400">
      <span>{stats.prompt_tokens + stats.completion_tokens} tokens</span>
      <span>{stats.elapsed_s.toFixed(2)}s</span>
    </div>
  )
}

interface Props {
  message: DisplayMessage
}

export function MessageBubble({ message }: Props) {
  if (message.kind === 'tool_step') {
    return (
      <div className="px-4">
        <ToolCallBlock
          name={message.name}
          args={message.args}
          result={message.result}
        />
      </div>
    )
  }

  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} px-4`}>
      <div
        className={[
          'max-w-[80%] rounded-2xl px-4 py-3',
          isUser
            ? 'bg-indigo-600 text-white'
            : 'bg-white border border-gray-200 shadow-sm',
        ].join(' ')}
      >
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>
        ) : (
          <div className={`prose prose-sm max-w-none text-gray-800`}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
          </div>
        )}
        {!isUser && message.stats && <StatsBadge stats={message.stats} />}
      </div>
    </div>
  )
}
