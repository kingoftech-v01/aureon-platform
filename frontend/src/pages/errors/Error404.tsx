/**
 * 404 Not Found Error Page
 * Aureon by Rhematek Solutions
 */

import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Button from '@/components/common/Button';

const Error404: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <div className="text-center max-w-lg">
        {/* Illustration */}
        <div className="mb-8 relative">
          <div className="w-32 h-32 mx-auto bg-gradient-to-br from-primary-500 to-accent-500 rounded-3xl flex items-center justify-center shadow-2xl shadow-primary-500/30">
            <svg className="w-16 h-16 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="absolute -top-2 -right-8 w-8 h-8 bg-yellow-400 rounded-full animate-bounce"></div>
          <div className="absolute -bottom-2 -left-4 w-6 h-6 bg-primary-400 rounded-full animate-pulse"></div>
        </div>

        {/* Error code */}
        <h1 className="text-8xl font-bold text-gray-200 dark:text-gray-700 mb-4">404</h1>

        {/* Title */}
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Page Not Found
        </h2>

        {/* Description */}
        <p className="text-gray-600 dark:text-gray-400 mb-8">
          Oops! The page you're looking for doesn't exist or has been moved. Let's get you back on track.
        </p>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button variant="primary" size="lg" onClick={() => navigate(-1)}>
            <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Go Back
          </Button>
          <Link to="/dashboard">
            <Button variant="outline" size="lg">
              Go to Dashboard
            </Button>
          </Link>
        </div>

        {/* Quick links */}
        <div className="mt-12 pt-8 border-t border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
            Popular destinations:
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link to="/clients" className="text-sm text-primary-600 dark:text-primary-400 hover:underline">
              Clients
            </Link>
            <Link to="/contracts" className="text-sm text-primary-600 dark:text-primary-400 hover:underline">
              Contracts
            </Link>
            <Link to="/invoices" className="text-sm text-primary-600 dark:text-primary-400 hover:underline">
              Invoices
            </Link>
            <Link to="/settings" className="text-sm text-primary-600 dark:text-primary-400 hover:underline">
              Settings
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Error404;
