/**
 * Tenant Welcome Page
 * Aureon by Rhematek Solutions
 *
 * Welcome page shown to unauthenticated users on tenant subdomains
 */

import React from 'react';
import { Link } from 'react-router-dom';
import Button from '@/components/common/Button';

interface TenantWelcomeProps {
  tenantName?: string;
  tenantLogo?: string;
}

const TenantWelcome: React.FC<TenantWelcomeProps> = ({
  tenantName = 'Your Workspace',
  tenantLogo
}) => {
  return (
    <div className="min-h-screen flex">
      {/* Left Side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary-600 via-primary-700 to-accent-600 relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <defs>
              <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
                <path d="M 10 0 L 0 0 0 10" fill="none" stroke="white" strokeWidth="0.5"/>
              </pattern>
            </defs>
            <rect width="100" height="100" fill="url(#grid)"/>
          </svg>
        </div>

        {/* Floating elements */}
        <div className="absolute top-20 left-20 w-20 h-20 bg-white/10 rounded-2xl animate-float"></div>
        <div className="absolute bottom-32 right-20 w-16 h-16 bg-white/10 rounded-full animate-float-delayed"></div>
        <div className="absolute top-1/2 left-1/3 w-12 h-12 bg-white/5 rounded-xl animate-pulse"></div>

        {/* Content */}
        <div className="relative z-10 flex flex-col justify-between p-12 w-full">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            {tenantLogo ? (
              <img src={tenantLogo} alt={tenantName} className="w-10 h-10 rounded-xl" />
            ) : (
              <div className="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center">
                <span className="text-white font-bold text-xl">A</span>
              </div>
            )}
            <span className="text-xl font-bold text-white">Aureon</span>
          </div>

          {/* Main Content */}
          <div className="max-w-md">
            <h1 className="text-4xl font-bold text-white leading-tight mb-6">
              Welcome to {tenantName}
            </h1>
            <p className="text-lg text-white/80 mb-8">
              Sign in to access your dashboard, manage clients, create contracts, and track your business finances.
            </p>

            {/* Features List */}
            <div className="space-y-4">
              {[
                'Manage clients and contacts',
                'Create and track contracts',
                'Send invoices and collect payments',
                'View analytics and reports',
              ].map((feature) => (
                <div key={feature} className="flex items-center space-x-3">
                  <div className="w-6 h-6 bg-white/20 rounded-full flex items-center justify-center flex-shrink-0">
                    <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <span className="text-white/90">{feature}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Footer */}
          <div className="text-white/60 text-sm">
            Powered by Aureon
          </div>
        </div>
      </div>

      {/* Right Side - Welcome Content */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-12 bg-white dark:bg-gray-900">
        <div className="w-full max-w-md text-center">
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center justify-center space-x-3 mb-8">
            {tenantLogo ? (
              <img src={tenantLogo} alt={tenantName} className="w-10 h-10 rounded-xl" />
            ) : (
              <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-accent-500 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/30">
                <span className="text-white font-bold text-xl">A</span>
              </div>
            )}
            <span className="text-xl font-bold text-gray-900 dark:text-white">Aureon</span>
          </div>

          {/* Workspace Icon */}
          <div className="w-20 h-20 bg-gradient-to-br from-primary-500 to-accent-500 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-primary-500/30">
            <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          </div>

          {/* Header */}
          <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-4">
            {tenantName}
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-8">
            Sign in to access your workspace and manage your business
          </p>

          {/* Actions */}
          <div className="space-y-4">
            <Link to="/auth/login" className="block">
              <Button variant="primary" size="lg" fullWidth className="!py-3">
                Sign In
              </Button>
            </Link>
            <Link to="/auth/register" className="block">
              <Button variant="outline" size="lg" fullWidth className="!py-3">
                Create Account
              </Button>
            </Link>
          </div>

          {/* Footer */}
          <p className="text-center text-xs text-gray-500 dark:text-gray-400 mt-8">
            By continuing, you agree to our{' '}
            <Link to="/terms" className="text-primary-600 dark:text-primary-400 hover:underline">
              Terms of Service
            </Link>{' '}
            and{' '}
            <Link to="/privacy" className="text-primary-600 dark:text-primary-400 hover:underline">
              Privacy Policy
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default TenantWelcome;
