/**
 * Loading Spinner Component
 * Aureon by Rhematek Solutions
 *
 * Loading indicator with customizable size and color
 */

import React from 'react';

type SpinnerSize = 'sm' | 'md' | 'lg' | 'xl';
type SpinnerColor = 'primary' | 'secondary' | 'white' | 'gray';

interface LoadingSpinnerProps {
  size?: SpinnerSize;
  color?: SpinnerColor;
  className?: string;
  text?: string;
  fullScreen?: boolean;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  color = 'primary',
  className = '',
  text,
  fullScreen = false,
}) => {
  const sizeStyles: Record<SpinnerSize, string> = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16',
  };

  const colorStyles: Record<SpinnerColor, string> = {
    primary: 'border-primary-500',
    secondary: 'border-accent-500',
    white: 'border-white',
    gray: 'border-gray-500',
  };

  const spinner = (
    <div className={`flex flex-col items-center justify-center ${className}`}>
      <div
        className={`animate-spin rounded-full border-b-2 ${sizeStyles[size]} ${colorStyles[color]}`}
        role="status"
        aria-label="Loading"
      />
      {text && (
        <p className="mt-3 text-sm text-gray-600 dark:text-gray-400">{text}</p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-white/80 dark:bg-gray-900/80 z-50">
        {spinner}
      </div>
    );
  }

  return spinner;
};

export default LoadingSpinner;
