/**
 * Input Component
 * Aureon by Rhematek Solutions
 *
 * Reusable input field with validation states and icons
 */

import React, { InputHTMLAttributes, ReactNode, forwardRef } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  fullWidth?: boolean;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      hint,
      leftIcon,
      rightIcon,
      fullWidth = false,
      className = '',
      disabled,
      ...props
    },
    ref
  ) => {
    const baseStyles = 'rounded-lg border px-4 py-2 text-base transition-colors focus:outline-none focus:ring-2 focus:ring-offset-0 disabled:opacity-50 disabled:cursor-not-allowed';

    const normalStyles = 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:border-primary-500 focus:ring-primary-500';

    const errorStyles = 'border-danger bg-red-50 dark:bg-red-900/20 text-gray-900 dark:text-white focus:border-danger focus:ring-danger';

    const widthStyle = fullWidth ? 'w-full' : '';
    const hasLeftIcon = leftIcon ? 'pl-10' : '';
    const hasRightIcon = rightIcon ? 'pr-10' : '';

    return (
      <div className={fullWidth ? 'w-full' : ''}>
        {label && (
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {label}
          </label>
        )}

        <div className="relative">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
              {leftIcon}
            </div>
          )}

          <input
            ref={ref}
            className={`${baseStyles} ${error ? errorStyles : normalStyles} ${widthStyle} ${hasLeftIcon} ${hasRightIcon} ${className}`}
            disabled={disabled}
            aria-invalid={error ? 'true' : 'false'}
            aria-describedby={error ? `${props.id}-error` : hint ? `${props.id}-hint` : undefined}
            {...props}
          />

          {rightIcon && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400">
              {rightIcon}
            </div>
          )}
        </div>

        {error && (
          <p className="mt-1 text-sm text-danger" id={`${props.id}-error`}>
            {error}
          </p>
        )}

        {hint && !error && (
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400" id={`${props.id}-hint`}>
            {hint}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;
