/**
 * 500 Internal Server Error Page
 * Aureon by Rhematek Solutions
 */

import React from 'react';
import { Link } from 'react-router-dom';
import Button from '@/components/common/Button';

const Error500: React.FC = () => {
  const handleRetry = () => {
    window.location.reload();
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <div className="text-center max-w-lg">
        {/* Illustration */}
        <div className="mb-8 relative">
          <div className="w-32 h-32 mx-auto bg-gradient-to-br from-red-500 to-pink-500 rounded-3xl flex items-center justify-center shadow-2xl shadow-red-500/30 animate-pulse">
            <svg className="w-16 h-16 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
        </div>

        {/* Error code */}
        <h1 className="text-8xl font-bold text-gray-200 dark:text-gray-700 mb-4">500</h1>

        {/* Title */}
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Internal Server Error
        </h2>

        {/* Description */}
        <p className="text-gray-600 dark:text-gray-400 mb-8">
          Something went wrong on our end. Our team has been notified and is working on a fix. Please try again later.
        </p>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button variant="primary" size="lg" onClick={handleRetry}>
            <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Try Again
          </Button>
          <Link to="/">
            <Button variant="outline" size="lg">
              Back to Home
            </Button>
          </Link>
        </div>

        {/* Status */}
        <div className="mt-12 bg-gray-100 dark:bg-gray-800 rounded-xl p-6">
          <div className="flex items-center justify-center space-x-2 mb-3">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              System Status
            </span>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Check our{' '}
            <a
              href="https://status.aureon.io"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-600 dark:text-primary-400 hover:underline"
            >
              status page
            </a>{' '}
            for real-time updates
          </p>
        </div>

        {/* Help link */}
        <p className="mt-8 text-sm text-gray-500 dark:text-gray-400">
          If this problem persists,{' '}
          <a href="mailto:support@aureon.io" className="text-primary-600 dark:text-primary-400 hover:underline">
            contact our support team
          </a>
        </p>
      </div>
    </div>
  );
};

export default Error500;
