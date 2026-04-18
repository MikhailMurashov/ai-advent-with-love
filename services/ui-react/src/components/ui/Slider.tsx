import { forwardRef } from 'react'
import type { InputHTMLAttributes } from 'react'

interface SliderProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  valueDisplay?: string
}

export const Slider = forwardRef<HTMLInputElement, SliderProps>(
  ({ label, valueDisplay, className = '', id, ...rest }, ref) => {
    return (
      <div className="flex flex-col gap-1">
        {label && (
          <div className="flex items-center justify-between">
            <label htmlFor={id} className="text-sm font-medium text-gray-300">
              {label}
            </label>
            {valueDisplay !== undefined && (
              <span className="text-sm text-gray-400">{valueDisplay}</span>
            )}
          </div>
        )}
        <input
          ref={ref}
          id={id}
          type="range"
          className={[
            'w-full h-2 rounded-lg appearance-none cursor-pointer',
            'bg-gray-700 accent-indigo-500',
            className,
          ].join(' ')}
          {...rest}
        />
      </div>
    )
  },
)

Slider.displayName = 'Slider'
