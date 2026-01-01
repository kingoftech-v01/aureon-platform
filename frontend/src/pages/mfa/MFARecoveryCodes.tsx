/**
 * MFA Recovery Codes Page
 * Aureon by Rhematek Solutions
 *
 * Page for viewing and regenerating recovery codes
 */

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import api from '@/services/api';

const MFARecoveryCodes: React.FC = () => {
  const navigate = useNavigate();
  const { error: showErrorToast, success: showSuccessToast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([]);
  const [showConfirmRegenerate, setShowConfirmRegenerate] = useState(false);

  useEffect(() => {
    fetchRecoveryCodes();
  }, []);

  const fetchRecoveryCodes = async () => {
    try {
      setIsLoading(true);
      const response = await api.get('/api/auth/mfa/recovery-codes/');
      setRecoveryCodes(response.data.codes || []);
    } catch (err: any) {
      showErrorToast(err.response?.data?.message || 'Failed to fetch recovery codes');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegenerate = async () => {
    try {
      setIsLoading(true);
      const response = await api.post('/api/auth/mfa/recovery-codes/regenerate/');
      setRecoveryCodes(response.data.codes || []);
      setShowConfirmRegenerate(false);
      showSuccessToast('Recovery codes regenerated successfully!');
    } catch (err: any) {
      showErrorToast(err.response?.data?.message || 'Failed to regenerate codes');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = () => {
    const content = recoveryCodes.join('\n');
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'aureon-recovery-codes.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showSuccessToast('Recovery codes downloaded!');
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(recoveryCodes.join('\n'));
      showSuccessToast('Recovery codes copied to clipboard!');
    } catch {
      showErrorToast('Failed to copy codes');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-gray-50 dark:bg-gray-900">
      <div className="w-full max-w-lg">
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-gradient-to-br from-primary-500 to-accent-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-primary-500/30">
              <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Recovery Codes
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mt-2">
              Save these codes in a safe place. You can use them to access your account if you lose your authenticator.
            </p>
          </div>

          {/* Warning */}
          <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl p-4 mb-6">
            <div className="flex items-start space-x-3">
              <svg className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div>
                <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                  Keep these codes secret
                </p>
                <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
                  Each code can only be used once. Store them securely.
                </p>
              </div>
            </div>
          </div>

          {/* Recovery codes grid */}
          {isLoading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
            </div>
          ) : (
            <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4 mb-6">
              <div className="grid grid-cols-2 gap-3">
                {recoveryCodes.map((code, index) => (
                  <div
                    key={index}
                    className="bg-white dark:bg-gray-800 rounded-lg px-4 py-2 text-center font-mono text-sm text-gray-900 dark:text-white border border-gray-200 dark:border-gray-600"
                  >
                    {code}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-col sm:flex-row gap-3">
            <Button
              variant="outline"
              size="md"
              fullWidth
              onClick={handleCopy}
              disabled={isLoading || recoveryCodes.length === 0}
            >
              <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              Copy
            </Button>
            <Button
              variant="outline"
              size="md"
              fullWidth
              onClick={handleDownload}
              disabled={isLoading || recoveryCodes.length === 0}
            >
              <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download
            </Button>
          </div>

          {/* Regenerate section */}
          {!showConfirmRegenerate ? (
            <button
              onClick={() => setShowConfirmRegenerate(true)}
              className="w-full mt-4 text-sm text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
            >
              Generate new recovery codes
            </button>
          ) : (
            <div className="mt-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4">
              <p className="text-sm text-red-700 dark:text-red-300 mb-4">
                This will invalidate your current recovery codes. Are you sure?
              </p>
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  size="sm"
                  fullWidth
                  onClick={() => setShowConfirmRegenerate(false)}
                >
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  fullWidth
                  onClick={handleRegenerate}
                  isLoading={isLoading}
                  className="!bg-red-600 hover:!bg-red-700"
                >
                  Regenerate
                </Button>
              </div>
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

export default MFARecoveryCodes;
