/**
 * 404 Not Found Page
 * Aureon by Rhematek Solutions
 */

import React from 'react';
import { Link } from 'react-router-dom';
import Button from '@/components/common/Button';

const NotFound: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <div className="max-w-md w-full text-center">
        <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-primary-500 to-accent-500 rounded-2xl mb-8">
          <span className="text-white font-bold text-4xl">404</span>
        </div>

        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
          Page Not Found
        </h1>

        <p className="text-lg text-gray-600 dark:text-gray-400 mb-8">
          Sorry, we couldn't find the page you're looking for.
        </p>

        <div className="space-y-3">
          <Link to="/dashboard">
            <Button variant="primary" size="lg" fullWidth>
              Go to Dashboard
            </Button>
          </Link>

          <button
            onClick={() => window.history.back()}
            className="w-full px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
          >
            ← Go Back
          </button>
        </div>
      </div>
    </div>
  );
};

export default NotFound;
