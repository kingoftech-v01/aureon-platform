/**
 * 429 Too Many Requests Error Page
 * Aureon by Rhematek Solutions
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Button from '@/components/common/Button';

const Error429: React.FC = () => {
  const [countdown, setCountdown] = useState(60);

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const handleRetry = () => {
    window.location.reload();
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <div className="text-center max-w-lg">
        {/* Illustration */}
        <div className="mb-8">
          <div className="w-32 h-32 mx-auto bg-gradient-to-br from-amber-500 to-orange-500 rounded-3xl flex items-center justify-center shadow-2xl shadow-amber-500/30">
            <svg className="w-16 h-16 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>

        {/* Error code */}
        <h1 className="text-8xl font-bold text-gray-200 dark:text-gray-700 mb-4">429</h1>

        {/* Title */}
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Too Many Requests
        </h2>

        {/* Description */}
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          You've made too many requests in a short period. Please wait a moment before trying again.
        </p>

        {/* Countdown */}
        <div className="bg-gray-100 dark:bg-gray-800 rounded-xl p-6 mb-8 inline-block">
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
            You can retry in
          </p>
          <div className="text-4xl font-bold text-primary-600 dark:text-primary-400">
            {countdown}s
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button
            variant="primary"
            size="lg"
            onClick={handleRetry}
            disabled={countdown > 0}
          >
            {countdown > 0 ? `Wait ${countdown}s` : 'Retry Now'}
          </Button>
          <Link to="/dashboard">
            <Button variant="outline" size="lg">
              Go to Dashboard
            </Button>
          </Link>
        </div>

        {/* Tips */}
        <div className="mt-12 pt-8 border-t border-gray-200 dark:border-gray-700 text-left">
          <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
            Tips to avoid this error:
          </p>
          <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
            <li className="flex items-start">
              <svg className="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Avoid rapidly clicking buttons or refreshing pages
            </li>
            <li className="flex items-start">
              <svg className="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Wait for pages to fully load before navigating
            </li>
            <li className="flex items-start">
              <svg className="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Contact support if this happens frequently
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default Error429;
