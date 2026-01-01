/**
 * MFA Disable Page
 * Aureon by Rhematek Solutions
 *
 * Page for disabling two-factor authentication
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import api from '@/services/api';

const MFADisable: React.FC = () => {
  const navigate = useNavigate();
  const { checkAuth } = useAuth();
  const { error: showErrorToast, success: showSuccessToast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [password, setPassword] = useState('');
  const [showConfirm, setShowConfirm] = useState(false);

  const handleDisable = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!password) {
      showErrorToast('Please enter your password');
      return;
    }

    try {
      setIsLoading(true);
      await api.post('/api/auth/mfa/totp/deactivate/', { password });
      showSuccessToast('Two-factor authentication disabled');
      await checkAuth();
      navigate('/settings');
    } catch (err: any) {
      showErrorToast(err.response?.data?.message || 'Failed to disable MFA. Check your password.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-gray-50 dark:bg-gray-900">
      <div className="w-full max-w-md">
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-gradient-to-br from-red-500 to-red-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-red-500/30">
              <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Disable Two-Factor Authentication
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mt-2">
              This will remove the extra security from your account
            </p>
          </div>

          {/* Warning */}
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 mb-6">
            <div className="flex items-start space-x-3">
              <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div>
                <p className="text-sm font-medium text-red-800 dark:text-red-200">
                  Security Warning
                </p>
                <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                  Disabling two-factor authentication will make your account less secure. Your account will only be protected by your password.
                </p>
              </div>
            </div>
          </div>

          {!showConfirm ? (
            <div className="space-y-4">
              <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
                Are you sure you want to disable two-factor authentication?
              </p>
              <div className="flex gap-3">
                <Link to="/settings" className="flex-1">
                  <Button variant="outline" size="lg" fullWidth>
                    Cancel
                  </Button>
                </Link>
                <Button
                  variant="primary"
                  size="lg"
                  onClick={() => setShowConfirm(true)}
                  className="flex-1 !bg-red-600 hover:!bg-red-700"
                >
                  Continue
                </Button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleDisable} className="space-y-6">
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Enter your password to confirm
                </label>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  fullWidth
                  leftIcon={
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
                    </svg>
                  }
                />
              </div>

              <div className="flex gap-3">
                <Button
                  type="button"
                  variant="outline"
                  size="lg"
                  fullWidth
                  onClick={() => setShowConfirm(false)}
                >
                  Back
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  fullWidth
                  isLoading={isLoading}
                  className="!bg-red-600 hover:!bg-red-700"
                >
                  Disable MFA
                </Button>
              </div>
            </form>
          )}

          {/* Back link */}
          <div className="mt-6 text-center">
            <Link
              to="/settings"
              className="text-sm text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400"
            >
              Back to Settings
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MFADisable;
