import { forwardRef } from 'react'
import type { TextareaHTMLAttributes } from 'react'

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, className = '', id, ...rest }, ref) => {
    return (
      <div className="flex flex-col gap-1">
        {label && (
          <label htmlFor={id} className="text-sm font-medium text-gray-300">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={id}
          className={[
            'rounded-lg border border-gray-600 bg-gray-800 px-3 py-2 text-sm text-gray-100',
            'placeholder:text-gray-500',
            'focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500',
            'disabled:cursor-not-allowed disabled:opacity-50',
            'resize-vertical min-h-[80px]',
            className,
          ].join(' ')}
          {...rest}
        />
      </div>
    )
  },
)

Textarea.displayName = 'Textarea'
