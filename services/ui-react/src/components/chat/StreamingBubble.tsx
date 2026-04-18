import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Props {
  content: string
}

export function StreamingBubble({ content }: Props) {
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
