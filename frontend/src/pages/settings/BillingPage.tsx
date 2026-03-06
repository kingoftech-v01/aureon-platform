/**
 * Billing Page
 * Aureon by Rhematek Solutions
 *
 * Full billing management with plan info, usage meters,
 * plan comparison, payment methods, and billing history.
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import Table, { TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '@/components/common/Table';
import Modal, { ModalHeader, ModalBody, ModalFooter } from '@/components/common/Modal';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import { SkeletonTable } from '@/components/common/Skeleton';
import apiClient from '@/services/api';

interface Plan {
  id: string;
  name: string;
  price: number;
  interval: string;
  features: string[];
  limits: {
    clients: number;
    invoices_per_month: number;
    storage_gb: number;
  };
}

interface Subscription {
  id: string;
  plan: Plan;
  status: string;
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
}

interface Usage {
  active_clients: number;
  active_clients_limit: number;
  invoices_this_month: number;
  invoices_limit: number;
  storage_used_gb: number;
  storage_limit_gb: number;
}

interface PaymentMethod {
  id: string;
  brand: string;
  last4: string;
  exp_month: number;
  exp_year: number;
  is_default: boolean;
}

interface BillingRecord {
  id: string;
  date: string;
  description: string;
  amount: number;
  status: string;
  invoice_pdf: string | null;
}

const plans: Plan[] = [
  {
    id: 'free',
    name: 'Free',
    price: 0,
    interval: 'month',
    features: ['5 active clients', '10 invoices/month', '1 GB storage', 'Basic templates', 'Email support'],
    limits: { clients: 5, invoices_per_month: 10, storage_gb: 1 },
  },
  {
    id: 'pro',
    name: 'Professional',
    price: 49,
    interval: 'month',
    features: ['50 active clients', '100 invoices/month', '10 GB storage', 'Custom templates', 'Priority support', 'E-signatures', 'API access'],
    limits: { clients: 50, invoices_per_month: 100, storage_gb: 10 },
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: 149,
    interval: 'month',
    features: ['Unlimited clients', 'Unlimited invoices', '100 GB storage', 'Custom branding', 'Dedicated support', 'E-signatures', 'API access', 'SSO/SAML', 'Audit logs', 'Custom integrations'],
    limits: { clients: -1, invoices_per_month: -1, storage_gb: 100 },
  },
];

const BillingPage: React.FC = () => {
  const { success: showSuccess, error: showError } = useToast();
  const queryClient = useQueryClient();
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);

  // Fetch current subscription
  const { data: subscription, isLoading: loadingSubscription } = useQuery<Subscription>({
    queryKey: ['subscription'],
    queryFn: async () => {
      const response = await apiClient.get('/subscriptions/current/');
      return response.data;
    },
  });

  // Fetch usage data
  const { data: usage } = useQuery<Usage>({
    queryKey: ['billing-usage'],
    queryFn: async () => {
      const response = await apiClient.get('/subscriptions/usage/');
      return response.data;
    },
  });

  // Fetch payment methods
  const { data: paymentMethods } = useQuery<PaymentMethod[]>({
    queryKey: ['payment-methods'],
    queryFn: async () => {
      const response = await apiClient.get('/subscriptions/payment-methods/');
      return response.data;
    },
  });

  // Fetch billing history
  const { data: billingHistory, isLoading: loadingHistory } = useQuery<BillingRecord[]>({
    queryKey: ['billing-history'],
    queryFn: async () => {
      const response = await apiClient.get('/payments/?type=subscription');
      return response.data.results || response.data;
    },
  });

  // Upgrade/downgrade mutation
  const upgradeMutation = useMutation({
    mutationFn: async (planId: string) => {
      const response = await apiClient.post('/subscriptions/upgrade/', { plan_id: planId });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscription'] });
      queryClient.invalidateQueries({ queryKey: ['billing-usage'] });
      showSuccess('Plan updated successfully');
      setShowUpgradeModal(false);
    },
    onError: () => {
      showError('Failed to update plan');
    },
  });

  // Format currency
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
  };

  // Format date
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  // Usage bar component
  const UsageBar = ({ used, limit, label }: { used: number; limit: number; label: string }) => {
    const percentage = limit === -1 ? 0 : Math.min((used / limit) * 100, 100);
    const isUnlimited = limit === -1;
    const isNearLimit = percentage >= 80;

    return (
      <div>
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{label}</span>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {used} / {isUnlimited ? 'Unlimited' : limit}
          </span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
          <div
            className={`h-2.5 rounded-full transition-all duration-500 ${
              isNearLimit ? 'bg-red-500' : 'bg-primary-500'
            }`}
            style={{ width: `${isUnlimited ? 5 : percentage}%` }}
          />
        </div>
      </div>
    );
  };

  // Card brand icon
  const getCardBrandIcon = (brand: string) => {
    const brandLower = brand.toLowerCase();
    if (brandLower === 'visa') return 'Visa';
    if (brandLower === 'mastercard') return 'MC';
    if (brandLower === 'amex') return 'Amex';
    return brand;
  };

  const handleUpgradeClick = (plan: Plan) => {
    setSelectedPlan(plan);
    setShowUpgradeModal(true);
  };

  if (loadingSubscription) {
    return (
      <div className="flex items-center justify-center h-96">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const currentPlanId = subscription?.plan?.id || 'free';

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-500 to-primary-600 rounded-2xl p-8 text-white">
        <h1 className="text-3xl font-bold">Billing & Subscription</h1>
        <p className="mt-2 text-primary-100">Manage your plan, payment methods, and billing history</p>
      </div>

      {/* Current Plan */}
      <Card>
        <CardHeader>
          <CardTitle>Current Plan</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center space-x-3">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                  {subscription?.plan?.name || 'Free Plan'}
                </h2>
                <Badge variant={subscription?.status === 'active' ? 'success' : 'warning'}>
                  {subscription?.status || 'active'}
                </Badge>
              </div>
              <p className="text-3xl font-bold text-primary-600 dark:text-primary-400 mt-2">
                {formatCurrency(subscription?.plan?.price || 0)}
                <span className="text-base font-normal text-gray-500 dark:text-gray-400">/month</span>
              </p>
              {subscription?.current_period_end && (
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                  {subscription.cancel_at_period_end
                    ? `Cancels on ${formatDate(subscription.current_period_end)}`
                    : `Next billing date: ${formatDate(subscription.current_period_end)}`}
                </p>
              )}
            </div>
            <div className="flex flex-col space-y-2">
              <Button variant="outline" onClick={() => setShowUpgradeModal(true)}>
                Change Plan
              </Button>
            </div>
          </div>
          {/* Plan Features */}
          <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
            <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
              Included Features
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {(subscription?.plan?.features || plans[0].features).map((feature, idx) => (
                <div key={idx} className="flex items-center text-sm text-gray-600 dark:text-gray-300">
                  <svg className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  {feature}
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Usage Meters */}
      <Card>
        <CardHeader>
          <CardTitle>Usage This Month</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <UsageBar
              used={usage?.active_clients || 0}
              limit={usage?.active_clients_limit || 5}
              label="Active Clients"
            />
            <UsageBar
              used={usage?.invoices_this_month || 0}
              limit={usage?.invoices_limit || 10}
              label="Invoices This Month"
            />
            <UsageBar
              used={usage?.storage_used_gb || 0}
              limit={usage?.storage_limit_gb || 1}
              label="Storage (GB)"
            />
          </div>
        </CardContent>
      </Card>

      {/* Plan Comparison Grid */}
      <Card>
        <CardHeader>
          <CardTitle>Compare Plans</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {plans.map((plan) => {
              const isCurrent = plan.id === currentPlanId;
              return (
                <div
                  key={plan.id}
                  className={`relative rounded-xl border-2 p-6 transition-all ${
                    isCurrent
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/10 shadow-lg'
                      : 'border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-700'
                  }`}
                >
                  {isCurrent && (
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <Badge variant="primary" size="sm">Current Plan</Badge>
                    </div>
                  )}
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white">{plan.name}</h3>
                  <p className="mt-2">
                    <span className="text-3xl font-bold text-gray-900 dark:text-white">
                      {plan.price === 0 ? 'Free' : formatCurrency(plan.price)}
                    </span>
                    {plan.price > 0 && (
                      <span className="text-sm text-gray-500 dark:text-gray-400">/month</span>
                    )}
                  </p>
                  <ul className="mt-4 space-y-2">
                    {plan.features.map((feature, idx) => (
                      <li key={idx} className="flex items-start text-sm text-gray-600 dark:text-gray-300">
                        <svg className="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        {feature}
                      </li>
                    ))}
                  </ul>
                  <div className="mt-6">
                    {isCurrent ? (
                      <Button variant="outline" fullWidth disabled>
                        Current Plan
                      </Button>
                    ) : (
                      <Button
                        variant={plan.price > (subscription?.plan?.price || 0) ? 'primary' : 'outline'}
                        fullWidth
                        onClick={() => handleUpgradeClick(plan)}
                      >
                        {plan.price > (subscription?.plan?.price || 0) ? 'Upgrade' : 'Downgrade'}
                      </Button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Payment Method */}
      <Card>
        <CardHeader>
          <CardTitle>Payment Method</CardTitle>
        </CardHeader>
        <CardContent>
          {paymentMethods && paymentMethods.length > 0 ? (
            <div className="space-y-3">
              {paymentMethods.map((method) => (
                <div
                  key={method.id}
                  className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
                >
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded flex items-center justify-center">
                      <span className="text-white text-xs font-bold">{getCardBrandIcon(method.brand)}</span>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {method.brand} ending in {method.last4}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        Expires {String(method.exp_month).padStart(2, '0')}/{method.exp_year}
                      </p>
                    </div>
                    {method.is_default && <Badge variant="primary" size="sm">Default</Badge>}
                  </div>
                  <Button variant="outline" size="sm">Update</Button>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-8 bg-gray-300 dark:bg-gray-600 rounded flex items-center justify-center">
                  <svg className="w-6 h-6 text-gray-500 dark:text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                  </svg>
                </div>
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">No payment method</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Add a card to manage your subscription</p>
                </div>
              </div>
              <Button variant="primary" size="sm">Add Card</Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Billing History */}
      <Card>
        <CardHeader>
          <CardTitle>Billing History</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loadingHistory ? (
            <div className="p-6">
              <SkeletonTable rows={5} columns={5} />
            </div>
          ) : billingHistory && billingHistory.length > 0 ? (
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeaderCell>Date</TableHeaderCell>
                  <TableHeaderCell>Description</TableHeaderCell>
                  <TableHeaderCell align="right">Amount</TableHeaderCell>
                  <TableHeaderCell>Status</TableHeaderCell>
                  <TableHeaderCell align="right">Invoice</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {billingHistory.map((record) => (
                  <TableRow key={record.id}>
                    <TableCell>
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {formatDate(record.date)}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {record.description}
                      </span>
                    </TableCell>
                    <TableCell align="right">
                      <span className="font-semibold text-gray-900 dark:text-white">
                        {formatCurrency(record.amount)}
                      </span>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          record.status === 'paid'
                            ? 'success'
                            : record.status === 'pending'
                            ? 'warning'
                            : record.status === 'failed'
                            ? 'danger'
                            : 'default'
                        }
                      >
                        {record.status}
                      </Badge>
                    </TableCell>
                    <TableCell align="right">
                      {record.invoice_pdf ? (
                        <a
                          href={record.invoice_pdf}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary-600 dark:text-primary-400 hover:underline text-sm inline-flex items-center"
                        >
                          <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          PDF
                        </a>
                      ) : (
                        <span className="text-gray-400 text-sm">--</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No billing history</h3>
              <p className="text-gray-600 dark:text-gray-400">Your billing transactions will appear here.</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Upgrade/Downgrade Modal */}
      <Modal isOpen={showUpgradeModal} onClose={() => setShowUpgradeModal(false)} size="md">
        <ModalHeader>
          {selectedPlan
            ? `${selectedPlan.price > (subscription?.plan?.price || 0) ? 'Upgrade' : 'Switch'} to ${selectedPlan.name}`
            : 'Change Plan'}
        </ModalHeader>
        <ModalBody>
          {selectedPlan ? (
            <div className="space-y-4">
              <p className="text-gray-600 dark:text-gray-400">
                You are about to switch from <strong>{subscription?.plan?.name || 'Free'}</strong> to{' '}
                <strong>{selectedPlan.name}</strong>.
              </p>
              <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">New monthly price</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {formatCurrency(selectedPlan.price)}<span className="text-sm font-normal">/month</span>
                </p>
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Changes will take effect at the start of your next billing cycle. Any price difference will be prorated.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {plans.filter((p) => p.id !== currentPlanId).map((plan) => (
                <button
                  key={plan.id}
                  onClick={() => setSelectedPlan(plan)}
                  className="w-full p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-primary-500 transition-colors text-left"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-gray-900 dark:text-white">{plan.name}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {plan.price === 0 ? 'Free' : `${formatCurrency(plan.price)}/month`}
                      </p>
                    </div>
                    <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </button>
              ))}
            </div>
          )}
        </ModalBody>
        <ModalFooter>
          <Button variant="ghost" onClick={() => { setShowUpgradeModal(false); setSelectedPlan(null); }}>
            Cancel
          </Button>
          {selectedPlan && (
            <Button
              variant="primary"
              onClick={() => upgradeMutation.mutate(selectedPlan.id)}
              isLoading={upgradeMutation.isPending}
            >
              Confirm Change
            </Button>
          )}
        </ModalFooter>
      </Modal>
    </div>
  );
};

export default BillingPage;
