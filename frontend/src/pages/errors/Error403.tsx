/**
 * 403 Forbidden Error Page
 * Aureon by Rhematek Solutions
 */

import React from 'react';
import { Link } from 'react-router-dom';
import Button from '@/components/common/Button';

const Error403: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <div className="text-center max-w-lg">
        {/* Illustration */}
        <div className="mb-8">
          <div className="w-32 h-32 mx-auto bg-gradient-to-br from-red-500 to-red-600 rounded-3xl flex items-center justify-center shadow-2xl shadow-red-500/30 transform rotate-3">
            <svg className="w-16 h-16 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
            </svg>
          </div>
        </div>

        {/* Error code */}
        <h1 className="text-8xl font-bold text-gray-200 dark:text-gray-700 mb-4">403</h1>

        {/* Title */}
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Access Forbidden
        </h2>

        {/* Description */}
        <p className="text-gray-600 dark:text-gray-400 mb-8">
          You don't have permission to access this resource. If you believe this is an error, please contact your administrator.
        </p>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link to="/dashboard">
            <Button variant="primary" size="lg">
              Go to Dashboard
            </Button>
          </Link>
          <Link to="/">
            <Button variant="outline" size="lg">
              Back to Home
            </Button>
          </Link>
        </div>

        {/* Help link */}
        <p className="mt-8 text-sm text-gray-500 dark:text-gray-400">
          Need help?{' '}
          <a href="mailto:support@aureon.io" className="text-primary-600 dark:text-primary-400 hover:underline">
            Contact Support
          </a>
        </p>
      </div>
    </div>
  );
};

export default Error403;
