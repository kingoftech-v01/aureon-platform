/**
 * Error Boundary Component
 * Aureon by Rhematek Solutions
 *
 * Global error boundary to catch and handle React errors
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import Button from './Button';
import Card, { CardContent } from './Card';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to console in development
    if (import.meta.env.DEV) {
      console.error('ErrorBoundary caught an error:', error, errorInfo);
    }

    // Call custom error handler if provided
    this.props.onError?.(error, errorInfo);

    this.setState({
      error,
      errorInfo,
    });

    // TODO: Log to error reporting service in production
    // logErrorToService(error, errorInfo);
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
          <Card className="max-w-2xl w-full">
            <CardContent className="p-8">
              <div className="text-center">
                {/* Error Icon */}
                <div className="w-16 h-16 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center mx-auto mb-6">
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
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                    />
                  </svg>
                </div>

                {/* Error Title */}
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                  Oops! Something went wrong
                </h1>

                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  We're sorry, but something unexpected happened. Our team has been notified
                  and we're working to fix the issue.
                </p>

                {/* Error Details (Development Only) */}
                {import.meta.env.DEV && this.state.error && (
                  <div className="mb-6 text-left">
                    <details className="bg-gray-100 dark:bg-gray-800 rounded-lg p-4">
                      <summary className="font-medium text-gray-900 dark:text-white cursor-pointer mb-2">
                        Error Details (Development Mode)
                      </summary>
                      <div className="space-y-2">
                        <div>
                          <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                            Error:
                          </p>
                          <pre className="text-xs text-red-600 dark:text-red-400 bg-white dark:bg-gray-900 p-2 rounded overflow-auto">
                            {this.state.error.toString()}
                          </pre>
                        </div>
                        {this.state.errorInfo && (
                          <div>
                            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                              Component Stack:
                            </p>
                            <pre className="text-xs text-gray-600 dark:text-gray-400 bg-white dark:bg-gray-900 p-2 rounded overflow-auto max-h-48">
                              {this.state.errorInfo.componentStack}
                            </pre>
                          </div>
                        )}
                      </div>
                    </details>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                  <Button variant="primary" onClick={this.handleReset}>
                    Try Again
                  </Button>
                  <Button variant="outline" onClick={this.handleReload}>
                    Reload Page
                  </Button>
                  <Button variant="outline" onClick={() => (window.location.href = '/')}>
                    Go to Home
                  </Button>
                </div>

                {/* Support Information */}
                <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    If this problem persists, please contact our support team at{' '}
                    <a
                      href="mailto:support@aureon.com"
                      className="text-primary-600 dark:text-primary-400 hover:underline"
                    >
                      support@aureon.com
                    </a>
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
