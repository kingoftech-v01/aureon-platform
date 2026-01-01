/**
 * Tenant Not Found Page
 * Aureon by Rhematek Solutions
 *
 * Shown when a tenant subdomain doesn't exist
 */

import React from 'react';
import Button from '@/components/common/Button';

interface TenantNotFoundProps {
  host?: string;
}

const TenantNotFound: React.FC<TenantNotFoundProps> = ({ host }) => {
  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <div className="text-center max-w-lg">
        {/* Logo */}
        <div className="flex items-center justify-center space-x-3 mb-12">
          <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-accent-500 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/30">
            <span className="text-white font-bold text-xl">A</span>
          </div>
          <span className="text-xl font-bold text-gray-900 dark:text-white">Aureon</span>
        </div>

        {/* Illustration */}
        <div className="mb-8 relative">
          <div className="w-32 h-32 mx-auto bg-gradient-to-br from-primary-500 to-accent-500 rounded-3xl flex items-center justify-center shadow-2xl shadow-primary-500/30">
            <svg className="w-16 h-16 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <div className="absolute -top-2 -right-4 w-8 h-8 bg-red-400 rounded-full flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
        </div>

        {/* Title */}
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-4">
          Workspace Not Found
        </h1>

        {/* Description */}
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          We couldn't find a workspace at this address.
        </p>
        {host && (
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-6 font-mono bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-2 inline-block">
            {host}
          </p>
        )}
        <p className="text-gray-600 dark:text-gray-400 mb-8">
          The workspace may have been moved, deleted, or the URL might be incorrect.
        </p>

        {/* Suggestions */}
        <div className="bg-gray-100 dark:bg-gray-800 rounded-xl p-6 mb-8 text-left">
          <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
            Things to try:
          </p>
          <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-3">
            <li className="flex items-start">
              <svg className="w-4 h-4 text-primary-500 mr-2 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Check the URL for typos
            </li>
            <li className="flex items-start">
              <svg className="w-4 h-4 text-primary-500 mr-2 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Contact your workspace administrator for the correct link
            </li>
            <li className="flex items-start">
              <svg className="w-4 h-4 text-primary-500 mr-2 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Create a new workspace if you're just getting started
            </li>
          </ul>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <a href="https://aureon.io/signup">
            <Button variant="primary" size="lg">
              Create a Workspace
            </Button>
          </a>
          <a href="https://aureon.io">
            <Button variant="outline" size="lg">
              Go to Aureon.io
            </Button>
          </a>
        </div>

        {/* Help */}
        <p className="mt-12 text-sm text-gray-500 dark:text-gray-400">
          Need help finding your workspace?{' '}
          <a href="mailto:support@aureon.io" className="text-primary-600 dark:text-primary-400 hover:underline">
            Contact Support
          </a>
        </p>
      </div>
    </div>
  );
};

export default TenantNotFound;
