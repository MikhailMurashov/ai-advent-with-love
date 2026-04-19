import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Props {
  content: string
}

export function StreamingBubble({ content }: Props) {
  if (!content) {
    return (
      <div className="flex justify-start">
        <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-white border border-gray-200 shadow-sm">
          <span className="text-gray-500 text-sm flex items-center gap-0">
            Думает
            <span className="thinking-dot dot-1">.</span>
            <span className="thinking-dot dot-2">.</span>
            <span className="thinking-dot dot-3">.</span>
          </span>
        </div>
      </div>
    )
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-white border border-gray-200 shadow-sm">
        <div className="prose prose-sm max-w-none text-gray-800">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
        </div>
        <span className="inline-block w-2 h-4 ml-0.5 bg-gray-400 animate-pulse rounded-sm align-middle" />
      </div>
    </div>
  )
}
