/**
 * Verify Email Page
 * Aureon by Rhematek Solutions
 *
 * Email verification page
 */

import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { authService } from '@/services';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Card, { CardContent } from '@/components/common/Card';
import LoadingSpinner from '@/components/common/LoadingSpinner';

const VerifyEmail: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const email = searchParams.get('email') || '';
  const { error: showErrorToast, success: showSuccessToast } = useToast();

  const [verifying, setVerifying] = useState(true);
  const [verified, setVerified] = useState(false);
  const [error, setError] = useState('');
  const [resending, setResending] = useState(false);

  useEffect(() => {
    if (token) {
      verifyEmail();
    } else {
      setVerifying(false);
      setError('Invalid or missing verification token');
    }
  }, [token]);

  const verifyEmail = async () => {
    try {
      await authService.verifyEmail(token);
      setVerified(true);
      showSuccessToast('Email verified successfully!');
      setTimeout(() => {
        navigate('/auth/login');
      }, 3000);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to verify email. The link may have expired.');
      showErrorToast('Email verification failed');
    } finally {
      setVerifying(false);
    }
  };

  const handleResend = async () => {
    if (!email) {
      showErrorToast('Email address not found');
      return;
    }

    setResending(true);

    try {
      await authService.resendVerificationEmail(email);
      showSuccessToast('Verification email sent! Please check your inbox.');
    } catch (err: any) {
      showErrorToast('Failed to resend verification email');
    } finally {
      setResending(false);
    }
  };

  if (verifying) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 via-white to-accent-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 px-4">
        <div className="w-full max-w-md">
          <Card padding="lg" shadow="lg">
            <CardContent>
              <div className="text-center space-y-4">
                <LoadingSpinner size="xl" color="primary" />
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Verifying Your Email
                </h2>
                <p className="text-gray-600 dark:text-gray-400">
                  Please wait while we verify your email address...
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 via-white to-accent-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-primary-500 to-accent-500 rounded-2xl mb-4">
            <span className="text-white font-bold text-2xl">A</span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            {verified ? 'Email Verified!' : 'Verification Failed'}
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            {verified
              ? 'Your email has been successfully verified'
              : 'We could not verify your email address'}
          </p>
        </div>

        {/* Content Card */}
        <Card padding="lg" shadow="lg">
          <CardContent>
            <div className="space-y-6">
              {verified ? (
                // Success state
                <>
                  <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                    <div className="flex items-center">
                      <div className="w-12 h-12 bg-green-100 dark:bg-green-900/50 rounded-full flex items-center justify-center mr-4">
                        <svg
                          className="w-6 h-6 text-green-500"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-green-800 dark:text-green-200">
                          Email verified successfully
                        </p>
                        <p className="text-sm text-green-700 dark:text-green-300 mt-1">
                          You can now sign in to your account
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    <p>
                      Redirecting you to the login page in a few seconds...
                    </p>
                  </div>

                  <Link to="/auth/login">
                    <Button variant="primary" size="lg" fullWidth>
                      Continue to Sign In
                    </Button>
                  </Link>
                </>
              ) : (
                // Error state
                <>
                  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                    <div className="flex items-center">
                      <div className="w-12 h-12 bg-red-100 dark:bg-red-900/50 rounded-full flex items-center justify-center mr-4">
                        <svg
                          className="w-6 h-6 text-red-500"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M6 18L18 6M6 6l12 12"
                          />
                        </svg>
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-red-800 dark:text-red-200">
                          Verification failed
                        </p>
                        <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                          {error}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
                    <p>The verification link may have expired or is invalid.</p>
                    {email && (
                      <p>
                        Would you like to{' '}
                        <button
                          onClick={handleResend}
                          disabled={resending}
                          className="text-primary-500 hover:text-primary-600 font-medium"
                        >
                          resend the verification email
                        </button>
                        ?
                      </p>
                    )}
                  </div>

                  <div className="space-y-3">
                    {email && (
                      <Button
                        variant="primary"
                        size="lg"
                        fullWidth
                        isLoading={resending}
                        onClick={handleResend}
                      >
                        Resend Verification Email
                      </Button>
                    )}

                    <Link to="/auth/login">
                      <Button variant="outline" size="lg" fullWidth>
                        Back to Sign In
                      </Button>
                    </Link>
                  </div>
                </>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Help link */}
        <p className="text-center text-xs text-gray-500 dark:text-gray-400 mt-6">
          Need help?{' '}
          <Link to="/support" className="text-primary-500 hover:underline">
            Contact Support
          </Link>
        </p>
      </div>
    </div>
  );
};

export default VerifyEmail;
