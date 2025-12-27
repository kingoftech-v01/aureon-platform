/**
 * Reset Password Page
 * Aureon by Rhematek Solutions
 *
 * Password reset confirmation page
 */

import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { authService } from '@/services';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Card, { CardContent } from '@/components/common/Card';

const ResetPassword: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const { error: showErrorToast, success: showSuccessToast } = useToast();

  const [formData, setFormData] = useState({
    password: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!token) {
      showErrorToast('Invalid or missing reset token');
      return false;
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password)) {
      newErrors.password = 'Password must contain uppercase, lowercase, and number';
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    setIsLoading(true);

    try {
      await authService.confirmPasswordReset(token, formData.password);
      showSuccessToast('Password reset successfully! You can now sign in.');
      setTimeout(() => {
        navigate('/auth/login');
      }, 2000);
    } catch (err: any) {
      showErrorToast(
        err.response?.data?.message || 'Failed to reset password. The link may have expired.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 via-white to-accent-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 px-4">
        <div className="w-full max-w-md">
          <Card padding="lg" shadow="lg">
            <CardContent>
              <div className="text-center space-y-4">
                <div className="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto">
                  <svg
                    className="w-8 h-8 text-red-500"
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
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Invalid Reset Link
                </h2>
                <p className="text-gray-600 dark:text-gray-400">
                  This password reset link is invalid or has expired.
                </p>
                <Link to="/auth/forgot-password">
                  <Button variant="primary" size="lg" fullWidth>
                    Request New Link
                  </Button>
                </Link>
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
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Reset Password</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Enter your new password below
          </p>
        </div>

        {/* Reset Form */}
        <Card padding="lg" shadow="lg">
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* New Password */}
              <Input
                id="password"
                name="password"
                type="password"
                label="New Password"
                placeholder="Min. 8 characters"
                value={formData.password}
                onChange={handleChange}
                error={errors.password}
                hint="Must contain uppercase, lowercase, and number"
                fullWidth
                leftIcon={
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                    />
                  </svg>
                }
              />

              {/* Confirm New Password */}
              <Input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                label="Confirm New Password"
                placeholder="Re-enter password"
                value={formData.confirmPassword}
                onChange={handleChange}
                error={errors.confirmPassword}
                fullWidth
                leftIcon={
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                }
              />

              {/* Password strength indicator */}
              {formData.password && (
                <div className="space-y-2">
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    Password strength:
                  </p>
                  <div className="flex space-x-1">
                    {[...Array(4)].map((_, i) => {
                      const strength = formData.password.length >= 12 ? 4 : formData.password.length >= 8 ? 3 : formData.password.length >= 6 ? 2 : 1;
                      return (
                        <div
                          key={i}
                          className={`h-1 flex-1 rounded ${
                            i < strength
                              ? strength >= 4
                                ? 'bg-green-500'
                                : strength >= 3
                                ? 'bg-yellow-500'
                                : 'bg-red-500'
                              : 'bg-gray-200 dark:bg-gray-700'
                          }`}
                        />
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Submit button */}
              <Button
                type="submit"
                variant="primary"
                size="lg"
                fullWidth
                isLoading={isLoading}
              >
                Reset Password
              </Button>

              {/* Back to login */}
              <div className="text-center">
                <Link
                  to="/auth/login"
                  className="text-sm text-primary-500 hover:text-primary-600 dark:text-primary-400 dark:hover:text-primary-300"
                >
                  ← Back to Sign In
                </Link>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ResetPassword;
