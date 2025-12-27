/**
 * Error Fallback Components
 * Aureon by Rhematek Solutions
 *
 * Reusable error fallback UI components
 */

import React from 'react';
import Button from './Button';
import Card, { CardContent } from './Card';

interface ErrorFallbackProps {
  error?: Error;
  resetError?: () => void;
  title?: string;
  message?: string;
}

/**
 * Generic error fallback component
 */
export const ErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  resetError,
  title = 'Something went wrong',
  message = 'We encountered an unexpected error. Please try again.',
}) => {
  return (
    <div className="flex items-center justify-center min-h-[400px] p-4">
      <div className="text-center max-w-md">
        <div className="w-16 h-16 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg
            className="w-8 h-8 text-red-600 dark:text-red-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>

        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          {title}
        </h3>

        <p className="text-gray-600 dark:text-gray-400 mb-4">{message}</p>

        {import.meta.env.DEV && error && (
          <details className="mb-4 text-left bg-gray-100 dark:bg-gray-800 rounded p-3">
            <summary className="text-sm font-medium cursor-pointer">
              Error Details
            </summary>
            <pre className="text-xs mt-2 text-red-600 dark:text-red-400 overflow-auto">
              {error.message}
            </pre>
          </details>
        )}

        {resetError && (
          <Button variant="primary" onClick={resetError}>
            Try Again
          </Button>
        )}
      </div>
    </div>
  );
};

/**
 * Page-level error fallback
 */
export const PageErrorFallback: React.FC<ErrorFallbackProps> = (props) => {
  return (
    <div className="p-6">
      <Card>
        <CardContent>
          <ErrorFallback {...props} />
        </CardContent>
      </Card>
    </div>
  );
};

/**
 * Network error fallback
 */
export const NetworkErrorFallback: React.FC<ErrorFallbackProps> = ({
  resetError,
}) => {
  return (
    <ErrorFallback
      title="Network Error"
      message="Unable to connect to the server. Please check your internet connection and try again."
      resetError={resetError}
    />
  );
};

/**
 * Not found error fallback
 */
export const NotFoundFallback: React.FC<{ resourceName?: string }> = ({
  resourceName = 'resource',
}) => {
  return (
    <div className="flex items-center justify-center min-h-[400px] p-4">
      <div className="text-center max-w-md">
        <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg
            className="w-8 h-8 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>

        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          {resourceName.charAt(0).toUpperCase() + resourceName.slice(1)} Not Found
        </h3>

        <p className="text-gray-600 dark:text-gray-400 mb-4">
          The {resourceName} you're looking for doesn't exist or has been removed.
        </p>

        <Button variant="primary" onClick={() => window.history.back()}>
          Go Back
        </Button>
      </div>
    </div>
  );
};

/**
 * Loading error fallback (for failed lazy loads)
 */
export const LoadingErrorFallback: React.FC<ErrorFallbackProps> = ({
  resetError,
}) => {
  return (
    <ErrorFallback
      title="Failed to Load"
      message="We couldn't load this page. This might be due to a network issue or the page may be temporarily unavailable."
      resetError={resetError}
    />
  );
};

export default ErrorFallback;
