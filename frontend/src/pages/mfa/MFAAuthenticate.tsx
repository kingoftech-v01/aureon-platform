/**
 * MFA Authenticate Page
 * Aureon by Rhematek Solutions
 *
 * Page for verifying two-factor authentication during login
 */

import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import api from '@/services/api';

const MFAAuthenticate: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { checkAuth } = useAuth();
  const { error: showErrorToast, success: showSuccessToast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [code, setCode] = useState('');
  const [useRecoveryCode, setUseRecoveryCode] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!useRecoveryCode && code.length !== 6) {
      showErrorToast('Please enter a 6-digit code');
      return;
    }

    if (useRecoveryCode && code.length < 8) {
      showErrorToast('Please enter a valid recovery code');
      return;
    }

    try {
      setIsLoading(true);
      const endpoint = useRecoveryCode
        ? '/api/auth/mfa/recovery/verify/'
        : '/api/auth/mfa/totp/verify/';

      await api.post(endpoint, { code });
      showSuccessToast('Authentication successful!');
      await checkAuth();

      const from = location.state?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    } catch (err: any) {
      showErrorToast(err.response?.data?.message || 'Invalid code. Please try again.');
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
            <div className="w-16 h-16 bg-gradient-to-br from-primary-500 to-accent-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-primary-500/30">
              <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Two-Factor Authentication
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mt-2">
              {useRecoveryCode
                ? 'Enter one of your recovery codes'
                : 'Enter the code from your authenticator app'
              }
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Code input */}
            <div>
              <label htmlFor="code" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {useRecoveryCode ? 'Recovery Code' : 'Authentication Code'}
              </label>
              <Input
                id="code"
                name="code"
                type="text"
                placeholder={useRecoveryCode ? 'Enter recovery code' : '000000'}
                value={code}
                onChange={(e) => {
                  if (useRecoveryCode) {
                    setCode(e.target.value);
                  } else {
                    setCode(e.target.value.replace(/\D/g, '').slice(0, 6));
                  }
                }}
                fullWidth
                className={useRecoveryCode ? '' : 'text-center text-2xl tracking-widest'}
                maxLength={useRecoveryCode ? 20 : 6}
                leftIcon={
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                  </svg>
                }
              />
            </div>

            {/* Submit button */}
            <Button
              type="submit"
              variant="primary"
              size="lg"
              fullWidth
              isLoading={isLoading}
            >
              Verify
            </Button>
          </form>

          {/* Toggle recovery code */}
          <div className="mt-6 text-center">
            <button
              type="button"
              onClick={() => {
                setUseRecoveryCode(!useRecoveryCode);
                setCode('');
              }}
              className="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300"
            >
              {useRecoveryCode
                ? 'Use authenticator app instead'
                : "Can't access your authenticator? Use a recovery code"
              }
            </button>
          </div>

          {/* Back to login link */}
          <div className="mt-4 text-center">
            <Link
              to="/auth/login"
              className="text-sm text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400"
            >
              Back to Login
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MFAAuthenticate;
