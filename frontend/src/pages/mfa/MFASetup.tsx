/**
 * MFA Setup Page
 * Aureon by Rhematek Solutions
 *
 * Page for setting up two-factor authentication
 */

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import api from '@/services/api';

const MFASetup: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { error: showErrorToast, success: showSuccessToast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [qrCode, setQrCode] = useState<string>('');
  const [secret, setSecret] = useState<string>('');
  const [verificationCode, setVerificationCode] = useState('');
  const [step, setStep] = useState<'setup' | 'verify'>('setup');

  useEffect(() => {
    fetchTOTPSetup();
  }, []);

  const fetchTOTPSetup = async () => {
    try {
      setIsLoading(true);
      const response = await api.post('/api/auth/mfa/totp/setup/');
      setQrCode(response.data.qr_code);
      setSecret(response.data.secret);
      setStep('verify');
    } catch (err: any) {
      showErrorToast(err.response?.data?.message || 'Failed to initialize MFA setup');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();

    if (verificationCode.length !== 6) {
      showErrorToast('Please enter a 6-digit code');
      return;
    }

    try {
      setIsLoading(true);
      await api.post('/api/auth/mfa/totp/activate/', {
        code: verificationCode,
      });
      showSuccessToast('Two-factor authentication enabled successfully!');
      navigate('/settings');
    } catch (err: any) {
      showErrorToast(err.response?.data?.message || 'Invalid verification code');
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
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Set Up Two-Factor Authentication
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mt-2">
              Add an extra layer of security to your account
            </p>
          </div>

          {step === 'verify' && qrCode && (
            <form onSubmit={handleVerify} className="space-y-6">
              {/* QR Code */}
              <div className="text-center">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)
                </p>
                <div className="bg-white p-4 rounded-xl inline-block mb-4">
                  <img src={qrCode} alt="QR Code for TOTP" className="w-48 h-48" />
                </div>
              </div>

              {/* Manual entry secret */}
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                  Can't scan? Enter this code manually:
                </p>
                <code className="text-sm font-mono text-gray-900 dark:text-white break-all">
                  {secret}
                </code>
              </div>

              {/* Verification input */}
              <div>
                <label htmlFor="code" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Enter the 6-digit code from your app
                </label>
                <Input
                  id="code"
                  name="code"
                  type="text"
                  placeholder="000000"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  fullWidth
                  className="text-center text-2xl tracking-widest"
                  maxLength={6}
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
                Verify and Enable
              </Button>
            </form>
          )}

          {isLoading && !qrCode && (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
            </div>
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

export default MFASetup;
