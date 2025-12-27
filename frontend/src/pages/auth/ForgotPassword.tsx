/**
 * Forgot Password Page
 * Aureon by Rhematek Solutions
 *
 * Password reset request page
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { authService } from '@/services';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Card, { CardContent } from '@/components/common/Card';

const ForgotPassword: React.FC = () => {
  const { error: showErrorToast, success: showSuccessToast } = useToast();
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const [error, setError] = useState('');

  const validate = (): boolean => {
    if (!email) {
      setError('Email is required');
      return false;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Invalid email address');
      return false;
    }
    setError('');
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    setIsLoading(true);

    try {
      await authService.requestPasswordReset(email);
      setEmailSent(true);
      showSuccessToast('Password reset instructions sent to your email');
    } catch (err: any) {
      showErrorToast(err.response?.data?.message || 'Failed to send reset email. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend = async () => {
    setIsLoading(true);

    try {
      await authService.requestPasswordReset(email);
      showSuccessToast('Email sent again');
    } catch (err: any) {
      showErrorToast('Failed to resend email');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 via-white to-accent-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-primary-500 to-accent-500 rounded-2xl mb-4">
            <span className="text-white font-bold text-2xl">A</span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            {emailSent ? 'Check Your Email' : 'Forgot Password?'}
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            {emailSent
              ? 'We sent password reset instructions to your email'
              : 'Enter your email to receive reset instructions'}
          </p>
        </div>

        {/* Form */}
        <Card padding="lg" shadow="lg">
          <CardContent>
            {emailSent ? (
              // Success state
              <div className="space-y-6">
                <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                  <div className="flex items-center">
                    <svg
                      className="w-6 h-6 text-green-500 mr-3"
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
                    <div className="flex-1">
                      <p className="text-sm font-medium text-green-800 dark:text-green-200">
                        Email sent successfully
                      </p>
                      <p className="text-sm text-green-700 dark:text-green-300 mt-1">
                        Check your inbox at <strong>{email}</strong>
                      </p>
                    </div>
                  </div>
                </div>

                <div className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
                  <p>Please check your email for password reset instructions.</p>
                  <p>
                    If you don't see the email, check your spam folder or{' '}
                    <button
                      onClick={handleResend}
                      disabled={isLoading}
                      className="text-primary-500 hover:text-primary-600 font-medium"
                    >
                      resend the email
                    </button>
                    .
                  </p>
                </div>

                <Link to="/auth/login">
                  <Button variant="primary" size="lg" fullWidth>
                    Back to Sign In
                  </Button>
                </Link>
              </div>
            ) : (
              // Form state
              <form onSubmit={handleSubmit} className="space-y-4">
                <Input
                  id="email"
                  name="email"
                  type="email"
                  label="Email Address"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    setError('');
                  }}
                  error={error}
                  fullWidth
                  leftIcon={
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207"
                      />
                    </svg>
                  }
                />

                <Button type="submit" variant="primary" size="lg" fullWidth isLoading={isLoading}>
                  Send Reset Instructions
                </Button>

                <div className="text-center">
                  <Link
                    to="/auth/login"
                    className="text-sm text-primary-500 hover:text-primary-600 dark:text-primary-400 dark:hover:text-primary-300"
                  >
                    ← Back to Sign In
                  </Link>
                </div>
              </form>
            )}
          </CardContent>
        </Card>

        {/* Additional help */}
        {!emailSent && (
          <p className="text-center text-xs text-gray-500 dark:text-gray-400 mt-6">
            Need help?{' '}
            <Link to="/support" className="text-primary-500 hover:underline">
              Contact Support
            </Link>
          </p>
        )}
      </div>
    </div>
  );
};

export default ForgotPassword;
