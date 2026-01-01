/**
 * Tenant Inactive Page
 * Aureon by Rhematek Solutions
 *
 * Shown when a tenant workspace has been deactivated
 */

import React from 'react';
import { Link } from 'react-router-dom';
import Button from '@/components/common/Button';

interface TenantInactiveProps {
  tenantName?: string;
}

const TenantInactive: React.FC<TenantInactiveProps> = ({
  tenantName = 'This Workspace'
}) => {
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
        <div className="mb-8">
          <div className="w-32 h-32 mx-auto bg-gradient-to-br from-gray-400 to-gray-500 rounded-3xl flex items-center justify-center shadow-2xl shadow-gray-500/30">
            <svg className="w-16 h-16 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
            </svg>
          </div>
        </div>

        {/* Title */}
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-4">
          Workspace Inactive
        </h1>

        {/* Description */}
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          <strong className="text-gray-900 dark:text-white">{tenantName}</strong> has been deactivated and is currently unavailable.
        </p>
        <p className="text-gray-600 dark:text-gray-400 mb-8">
          This could be due to billing issues, account suspension, or the workspace being closed by the owner.
        </p>

        {/* Info box */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-6 mb-8 text-left">
          <div className="flex items-start space-x-3">
            <svg className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <p className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-2">
                What you can do:
              </p>
              <ul className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
                <li>Contact the workspace administrator</li>
                <li>Check if your billing information is up to date</li>
                <li>Reach out to Aureon support for assistance</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <a href="mailto:support@aureon.io">
            <Button variant="primary" size="lg">
              <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              Contact Support
            </Button>
          </a>
          <a href="https://aureon.io">
            <Button variant="outline" size="lg">
              Visit Aureon.io
            </Button>
          </a>
        </div>

        {/* Footer */}
        <p className="mt-12 text-sm text-gray-500 dark:text-gray-400">
          If you believe this is an error, please contact{' '}
          <a href="mailto:support@aureon.io" className="text-primary-600 dark:text-primary-400 hover:underline">
            support@aureon.io
          </a>
        </p>
      </div>
    </div>
  );
};

export default TenantInactive;
