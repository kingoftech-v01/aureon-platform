/**
 * Stripe Connect Onboarding Page
 * Aureon by Rhematek Solutions
 *
 * Manage Stripe Connect account: onboarding, status, payouts, and settings
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/services/api';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Card, { CardHeader, CardTitle, CardContent, CardFooter } from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import { SkeletonCard } from '@/components/common/Skeleton';

interface StripeStatus {
  status: 'not_connected' | 'pending' | 'active' | 'restricted';
  account_id?: string;
  details_submitted?: boolean;
  charges_enabled?: boolean;
  payouts_enabled?: boolean;
  dashboard_url?: string;
  requirements?: {
    currently_due: string[];
    past_due: string[];
    eventually_due: string[];
  };
  payout_schedule?: {
    interval: string;
    delay_days: number;
    weekly_anchor?: string;
    monthly_anchor?: number;
  };
  default_currency?: string;
}

interface Payout {
  id: string;
  amount: number;
  currency: string;
  status: 'paid' | 'pending' | 'in_transit' | 'canceled' | 'failed';
  arrival_date: string;
  created_at: string;
  destination: string;
  method: string;
}

const StripeConnect: React.FC = () => {
  const queryClient = useQueryClient();
  const { success: showSuccessToast, error: showErrorToast } = useToast();
  const [showDisconnectConfirm, setShowDisconnectConfirm] = useState(false);
  const [payoutFrequency, setPayoutFrequency] = useState('daily');
  const [minimumPayout, setMinimumPayout] = useState('100');

  // Fetch Stripe connection status
  const { data: stripeStatus, isLoading: statusLoading } = useQuery<StripeStatus>({
    queryKey: ['stripe-status'],
    queryFn: async () => {
      const response = await apiClient.get('/payments/stripe/status/');
      return response.data;
    },
  });

  // Fetch payout history (only when connected)
  const { data: payouts, isLoading: payoutsLoading } = useQuery<Payout[]>({
    queryKey: ['stripe-payouts'],
    queryFn: async () => {
      const response = await apiClient.get('/payments/stripe/payouts/');
      return response.data;
    },
    enabled: stripeStatus?.status === 'active',
  });

  // Connect mutation
  const connectMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/payments/stripe/connect/');
      return response.data;
    },
    onSuccess: (data) => {
      if (data.onboarding_url) {
        window.location.href = data.onboarding_url;
      } else {
        showSuccessToast('Stripe account connection initiated');
        queryClient.invalidateQueries({ queryKey: ['stripe-status'] });
      }
    },
    onError: (err: any) => {
      showErrorToast(err.response?.data?.message || 'Failed to connect Stripe account');
    },
  });

  // Disconnect mutation
  const disconnectMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/payments/stripe/disconnect/');
      return response.data;
    },
    onSuccess: () => {
      showSuccessToast('Stripe account disconnected');
      queryClient.invalidateQueries({ queryKey: ['stripe-status'] });
      setShowDisconnectConfirm(false);
    },
    onError: (err: any) => {
      showErrorToast(err.response?.data?.message || 'Failed to disconnect Stripe account');
      setShowDisconnectConfirm(false);
    },
  });

  // Update settings mutation
  const updateSettingsMutation = useMutation({
    mutationFn: async (settings: { payout_frequency: string; minimum_payout: number }) => {
      const response = await apiClient.patch('/payments/stripe/settings/', settings);
      return response.data;
    },
    onSuccess: () => {
      showSuccessToast('Payout settings updated');
      queryClient.invalidateQueries({ queryKey: ['stripe-status'] });
    },
    onError: (err: any) => {
      showErrorToast(err.response?.data?.message || 'Failed to update settings');
    },
  });

  // Format currency
  const formatCurrency = (amount: number, currency?: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency || 'USD',
    }).format(amount);
  };

  // Format date
  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // Payout status badge
  const getPayoutStatusBadge = (status: Payout['status']) => {
    const map: Record<Payout['status'], 'success' | 'warning' | 'info' | 'default' | 'danger'> = {
      paid: 'success',
      pending: 'warning',
      in_transit: 'info',
      canceled: 'default',
      failed: 'danger',
    };
    return <Badge variant={map[status]} size="sm">{status.replace('_', ' ')}</Badge>;
  };

  // Current status
  const status = stripeStatus?.status || 'not_connected';

  // Onboarding progress steps
  const onboardingSteps = [
    { key: 'created', label: 'Account Created', done: status !== 'not_connected' },
    { key: 'details', label: 'Details Submitted', done: stripeStatus?.details_submitted || false },
    { key: 'verification', label: 'Verification', done: stripeStatus?.charges_enabled || false },
    { key: 'active', label: 'Active', done: status === 'active' },
  ];

  // Loading
  if (statusLoading) {
    return (
      <div className="max-w-5xl mx-auto space-y-6">
        <SkeletonCard />
        <SkeletonCard />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-xl flex items-center justify-center">
            <svg className="w-6 h-6 text-white" viewBox="0 0 24 24" fill="currentColor">
              <path d="M13.976 9.15c-2.172-.806-3.356-1.426-3.356-2.409 0-.831.683-1.305 1.901-1.305 2.227 0 4.515.858 6.09 1.631l.89-5.494C18.252.975 15.697 0 12.165 0 9.667 0 7.589.654 6.104 1.872 4.56 3.147 3.757 4.992 3.757 7.218c0 4.039 2.467 5.76 6.476 7.219 2.585.92 3.445 1.574 3.445 2.583 0 .98-.84 1.545-2.354 1.545-1.875 0-4.965-.921-7.076-2.19l-.89 5.494C5.108 22.88 8.102 24 11.738 24c2.666 0 4.836-.749 6.213-1.872 1.659-1.36 2.497-3.291 2.497-5.758 0-4.153-2.544-5.822-6.472-7.22z" />
            </svg>
          </div>
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">Stripe Connect</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Manage your Stripe payment processing account
            </p>
          </div>
        </div>
      </div>

      {/* Status Card */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className={`w-14 h-14 rounded-full flex items-center justify-center ${
                status === 'active'
                  ? 'bg-green-100 dark:bg-green-900/20'
                  : status === 'pending'
                  ? 'bg-yellow-100 dark:bg-yellow-900/20'
                  : 'bg-gray-100 dark:bg-gray-800'
              }`}>
                {status === 'active' ? (
                  <svg className="w-7 h-7 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                ) : status === 'pending' ? (
                  <svg className="w-7 h-7 text-yellow-600 dark:text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                ) : (
                  <svg className="w-7 h-7 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                )}
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {status === 'active' ? 'Stripe Connected' : status === 'pending' ? 'Connection Pending' : 'Not Connected'}
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {status === 'active'
                    ? 'Your Stripe account is active and processing payments'
                    : status === 'pending'
                    ? 'Complete the verification steps to start accepting payments'
                    : 'Connect your Stripe account to start accepting payments'}
                </p>
              </div>
            </div>
            <Badge
              variant={status === 'active' ? 'success' : status === 'pending' ? 'warning' : 'default'}
              size="lg"
            >
              {status.replace('_', ' ').toUpperCase()}
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Not Connected State */}
      {status === 'not_connected' && (
        <Card>
          <CardContent className="p-8">
            <div className="text-center max-w-xl mx-auto">
              <div className="w-20 h-20 bg-gradient-to-br from-purple-100 to-indigo-100 dark:from-purple-900/20 dark:to-indigo-900/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <svg className="w-10 h-10 text-purple-600 dark:text-purple-400" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M13.976 9.15c-2.172-.806-3.356-1.426-3.356-2.409 0-.831.683-1.305 1.901-1.305 2.227 0 4.515.858 6.09 1.631l.89-5.494C18.252.975 15.697 0 12.165 0 9.667 0 7.589.654 6.104 1.872 4.56 3.147 3.757 4.992 3.757 7.218c0 4.039 2.467 5.76 6.476 7.219 2.585.92 3.445 1.574 3.445 2.583 0 .98-.84 1.545-2.354 1.545-1.875 0-4.965-.921-7.076-2.19l-.89 5.494C5.108 22.88 8.102 24 11.738 24c2.666 0 4.836-.749 6.213-1.872 1.659-1.36 2.497-3.291 2.497-5.758 0-4.153-2.544-5.822-6.472-7.22z" />
                </svg>
              </div>

              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3">
                Connect with Stripe to Accept Payments
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Securely accept credit cards, bank transfers, and more with Stripe, the world's leading payment processor.
              </p>

              {/* Benefits */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8 text-left">
                <div className="flex items-start space-x-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">Instant Payouts</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Get paid directly to your bank</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">135+ Currencies</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Accept payments globally</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
                  <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">PCI Compliant</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Bank-grade security</p>
                  </div>
                </div>
              </div>

              <Button
                variant="primary"
                size="lg"
                onClick={() => connectMutation.mutate()}
                isLoading={connectMutation.isPending}
              >
                <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M13.976 9.15c-2.172-.806-3.356-1.426-3.356-2.409 0-.831.683-1.305 1.901-1.305 2.227 0 4.515.858 6.09 1.631l.89-5.494C18.252.975 15.697 0 12.165 0 9.667 0 7.589.654 6.104 1.872 4.56 3.147 3.757 4.992 3.757 7.218c0 4.039 2.467 5.76 6.476 7.219 2.585.92 3.445 1.574 3.445 2.583 0 .98-.84 1.545-2.354 1.545-1.875 0-4.965-.921-7.076-2.19l-.89 5.494C5.108 22.88 8.102 24 11.738 24c2.666 0 4.836-.749 6.213-1.872 1.659-1.36 2.497-3.291 2.497-5.758 0-4.153-2.544-5.822-6.472-7.22z" />
                </svg>
                Connect with Stripe
              </Button>

              {/* Security Badges */}
              <div className="flex items-center justify-center space-x-4 mt-6">
                <div className="flex items-center space-x-1 text-gray-400 dark:text-gray-500">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                  <span className="text-xs">256-bit SSL</span>
                </div>
                <div className="flex items-center space-x-1 text-gray-400 dark:text-gray-500">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  <span className="text-xs">PCI DSS Level 1</span>
                </div>
                <div className="flex items-center space-x-1 text-gray-400 dark:text-gray-500">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-xs">SOC 2 Certified</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Pending State */}
      {status === 'pending' && (
        <Card>
          <CardHeader>
            <CardTitle>Onboarding Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between max-w-2xl mx-auto py-4">
              {onboardingSteps.map((step, index) => (
                <React.Fragment key={step.key}>
                  <div className="flex flex-col items-center">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                      step.done
                        ? 'bg-green-500 text-white'
                        : 'bg-gray-200 dark:bg-gray-700 text-gray-400'
                    }`}>
                      {step.done ? (
                        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        <span className="text-sm font-semibold">{index + 1}</span>
                      )}
                    </div>
                    <span className={`mt-2 text-xs font-medium text-center ${
                      step.done ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'
                    }`}>
                      {step.label}
                    </span>
                  </div>
                  {index < onboardingSteps.length - 1 && (
                    <div className={`flex-1 h-0.5 mx-3 ${
                      onboardingSteps[index + 1].done ? 'bg-green-500' : 'bg-gray-200 dark:bg-gray-700'
                    }`} />
                  )}
                </React.Fragment>
              ))}
            </div>

            {stripeStatus?.requirements?.currently_due && stripeStatus.requirements.currently_due.length > 0 && (
              <div className="mt-6 bg-yellow-50 dark:bg-yellow-900/10 rounded-lg p-4 border border-yellow-200 dark:border-yellow-800">
                <h4 className="text-sm font-semibold text-yellow-800 dark:text-yellow-300 mb-2">
                  Action Required
                </h4>
                <p className="text-sm text-yellow-700 dark:text-yellow-400 mb-3">
                  Complete the following to activate your account:
                </p>
                <ul className="space-y-1">
                  {stripeStatus.requirements.currently_due.map((req, idx) => (
                    <li key={idx} className="text-sm text-yellow-700 dark:text-yellow-400 flex items-center space-x-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-yellow-500" />
                      <span>{req.replace(/_/g, ' ').replace(/\./g, ' > ')}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="mt-6 text-center">
              <Button
                variant="primary"
                onClick={() => connectMutation.mutate()}
                isLoading={connectMutation.isPending}
              >
                Continue Setup
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Active State */}
      {status === 'active' && (
        <>
          {/* Account Info */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card>
              <CardContent className="p-6">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Connected Account</p>
                <p className="text-sm font-mono text-gray-900 dark:text-white mt-2">
                  {stripeStatus?.account_id || 'acct_xxxxxxxxxx'}
                </p>
                {stripeStatus?.dashboard_url && (
                  <a
                    href={stripeStatus.dashboard_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center text-sm text-primary-600 dark:text-primary-400 hover:underline mt-3"
                  >
                    Open Stripe Dashboard
                    <svg className="w-4 h-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                )}
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Payout Schedule</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white mt-2 capitalize">
                  {stripeStatus?.payout_schedule?.interval || 'Daily'}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {stripeStatus?.payout_schedule?.delay_days
                    ? `${stripeStatus.payout_schedule.delay_days} day delay`
                    : '2 day delay'}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Default Currency</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white mt-2 uppercase">
                  {stripeStatus?.default_currency || 'USD'}
                </p>
                <div className="flex items-center space-x-2 mt-1">
                  <Badge variant="success" size="sm" dot>Charges Enabled</Badge>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Payout History */}
          <Card>
            <CardHeader>
              <CardTitle>Payout History</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {payoutsLoading ? (
                <div className="p-6"><SkeletonCard /></div>
              ) : payouts && payouts.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200 dark:border-gray-700">
                        <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Date
                        </th>
                        <th className="text-right px-6 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Amount
                        </th>
                        <th className="text-center px-6 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Destination
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                      {payouts.map((payout) => (
                        <tr key={payout.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                          <td className="px-6 py-4">
                            <p className="text-sm font-medium text-gray-900 dark:text-white">
                              {formatDate(payout.arrival_date)}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              Initiated {formatDate(payout.created_at)}
                            </p>
                          </td>
                          <td className="px-6 py-4 text-right">
                            <span className="text-sm font-semibold text-gray-900 dark:text-white">
                              {formatCurrency(payout.amount, payout.currency)}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-center">
                            {getPayoutStatusBadge(payout.status)}
                          </td>
                          <td className="px-6 py-4">
                            <span className="text-sm text-gray-600 dark:text-gray-400 font-mono">
                              {payout.destination || 'Bank Account'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="px-6 py-12 text-center">
                  <svg className="w-12 h-12 text-gray-400 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                  </svg>
                  <p className="text-gray-600 dark:text-gray-400">No payouts yet. Payouts will appear here once payments are processed.</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Settings */}
          <Card>
            <CardHeader>
              <CardTitle>Payout Settings</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="payout_frequency" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Payout Frequency
                  </label>
                  <select
                    id="payout_frequency"
                    value={payoutFrequency}
                    onChange={(e) => setPayoutFrequency(e.target.value)}
                    className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  >
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="minimum_payout" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Minimum Payout Amount
                  </label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">$</span>
                    <input
                      id="minimum_payout"
                      type="number"
                      min="1"
                      step="1"
                      value={minimumPayout}
                      onChange={(e) => setMinimumPayout(e.target.value)}
                      className="w-full pl-8 pr-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex justify-between">
              <Button
                variant="primary"
                onClick={() => updateSettingsMutation.mutate({
                  payout_frequency: payoutFrequency,
                  minimum_payout: parseFloat(minimumPayout) || 100,
                })}
                isLoading={updateSettingsMutation.isPending}
              >
                Save Settings
              </Button>
              <Button
                variant="danger"
                onClick={() => setShowDisconnectConfirm(true)}
              >
                <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                Disconnect Stripe
              </Button>
            </CardFooter>
          </Card>
        </>
      )}

      {/* Disconnect Confirmation Modal */}
      {showDisconnectConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md m-4">
            <CardHeader>
              <CardTitle>Disconnect Stripe Account?</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <p className="text-gray-600 dark:text-gray-400">
                  Disconnecting your Stripe account will:
                </p>
                <ul className="space-y-2">
                  <li className="flex items-start space-x-2 text-sm text-gray-700 dark:text-gray-300">
                    <svg className="w-5 h-5 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    <span>Stop all payment processing</span>
                  </li>
                  <li className="flex items-start space-x-2 text-sm text-gray-700 dark:text-gray-300">
                    <svg className="w-5 h-5 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    <span>Disable automatic invoicing collections</span>
                  </li>
                  <li className="flex items-start space-x-2 text-sm text-gray-700 dark:text-gray-300">
                    <svg className="w-5 h-5 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    <span>Cancel any pending payouts</span>
                  </li>
                </ul>
                <div className="bg-red-50 dark:bg-red-900/10 rounded-lg p-3 border border-red-200 dark:border-red-800">
                  <p className="text-sm text-red-800 dark:text-red-300">
                    This action can be reversed by reconnecting, but any in-progress transactions may be affected.
                  </p>
                </div>
                <div className="flex justify-end space-x-3 pt-2">
                  <Button variant="outline" onClick={() => setShowDisconnectConfirm(false)}>
                    Cancel
                  </Button>
                  <Button
                    variant="danger"
                    onClick={() => disconnectMutation.mutate()}
                    isLoading={disconnectMutation.isPending}
                  >
                    Disconnect
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default StripeConnect;
