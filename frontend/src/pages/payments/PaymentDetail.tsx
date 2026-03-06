/**
 * Payment Detail Page
 * Aureon by Rhematek Solutions
 *
 * Detailed view of a single payment with Stripe details and refund capability
 */

import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { paymentService } from '@/services';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import { SkeletonCard } from '@/components/common/Skeleton';
import type { Payment, PaymentStatus } from '@/types';

const PaymentDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success: showSuccessToast, error: showErrorToast } = useToast();
  const [showRefundModal, setShowRefundModal] = useState(false);
  const [refundAmount, setRefundAmount] = useState('');
  const [refundReason, setRefundReason] = useState('');

  // Fetch payment data
  const { data: payment, isLoading, error } = useQuery({
    queryKey: ['payment', id],
    queryFn: () => paymentService.getPayment(id!),
    enabled: !!id,
  });

  // Fetch payment history/timeline
  const { data: history } = useQuery({
    queryKey: ['payment-history', id],
    queryFn: () => paymentService.getPaymentHistory(id!),
    enabled: !!id,
  });

  // Refund mutation
  const refundMutation = useMutation({
    mutationFn: (data: { amount?: number; reason?: string }) =>
      paymentService.refundPayment(id!, data),
    onSuccess: () => {
      showSuccessToast('Refund processed successfully');
      queryClient.invalidateQueries({ queryKey: ['payment', id] });
      queryClient.invalidateQueries({ queryKey: ['payments'] });
      queryClient.invalidateQueries({ queryKey: ['payment-history', id] });
      setShowRefundModal(false);
      setRefundAmount('');
      setRefundReason('');
    },
    onError: (error: any) => {
      showErrorToast(error.response?.data?.message || 'Failed to process refund');
    },
  });

  // Send receipt mutation
  const sendReceiptMutation = useMutation({
    mutationFn: () => paymentService.sendReceipt(id!),
    onSuccess: () => {
      showSuccessToast('Receipt sent successfully');
    },
    onError: (error: any) => {
      showErrorToast(error.response?.data?.message || 'Failed to send receipt');
    },
  });

  // Retry payment mutation
  const retryMutation = useMutation({
    mutationFn: () => paymentService.retryPayment(id!),
    onSuccess: () => {
      showSuccessToast('Payment retry initiated');
      queryClient.invalidateQueries({ queryKey: ['payment', id] });
      queryClient.invalidateQueries({ queryKey: ['payments'] });
    },
    onError: (error: any) => {
      showErrorToast(error.response?.data?.message || 'Failed to retry payment');
    },
  });

  // Handle refund submission
  const handleRefundSubmit = () => {
    const data: { amount?: number; reason?: string } = {};
    if (refundAmount) {
      data.amount = parseFloat(refundAmount);
    }
    if (refundReason) {
      data.reason = refundReason;
    }
    refundMutation.mutate(data);
  };

  // Payment status badge colors
  const getStatusBadge = (status: PaymentStatus) => {
    const variants: Record<PaymentStatus, 'default' | 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
      pending: 'warning',
      processing: 'info',
      succeeded: 'success',
      failed: 'danger',
      refunded: 'default',
      partially_refunded: 'warning',
      cancelled: 'default',
    };
    return <Badge variant={variants[status]}>{status.replace('_', ' ')}</Badge>;
  };

  // Payment method icon
  const getPaymentMethodIcon = (method: string) => {
    switch (method?.toLowerCase()) {
      case 'card':
      case 'credit_card':
        return (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
          </svg>
        );
      case 'bank_transfer':
        return (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z" />
          </svg>
        );
      default:
        return (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        );
    }
  };

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
      month: 'long',
      day: 'numeric',
    });
  };

  // Format datetime
  const formatDateTime = (date: string) => {
    return new Date(date).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Download receipt
  const handleDownloadReceipt = async () => {
    try {
      const blob = await paymentService.getReceipt(id!);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `receipt-${payment?.transaction_id || id}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      showSuccessToast('Receipt downloaded');
    } catch (error: any) {
      showErrorToast('Failed to download receipt');
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        <SkeletonCard />
        <SkeletonCard />
      </div>
    );
  }

  // Error state
  if (error || !payment) {
    return (
      <div className="max-w-4xl mx-auto">
        <Card>
          <CardContent className="p-12 text-center">
            <div className="w-16 h-16 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              Payment not found
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              The payment you're looking for doesn't exist or has been deleted.
            </p>
            <Link to="/payments">
              <Button variant="primary">Back to Payments</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Extract client display name from invoice
  const clientName = payment.invoice?.client
    ? payment.invoice.client.type === 'individual'
      ? `${payment.invoice.client.first_name} ${payment.invoice.client.last_name}`
      : payment.invoice.client.company_name
    : 'Unknown Client';

  // Extract payment method info
  const paymentMethodType = typeof payment.payment_method === 'object'
    ? payment.payment_method.type
    : payment.payment_method;
  const cardLast4 = typeof payment.payment_method === 'object'
    ? payment.payment_method.last4
    : undefined;
  const cardBrand = typeof payment.payment_method === 'object'
    ? payment.payment_method.brand
    : undefined;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center space-x-4 mb-2">
            <button
              onClick={() => navigate('/payments')}
              className="p-2 -ml-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              title="Back to payments"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </button>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              <span className="font-mono">{payment.transaction_id || payment.payment_number || payment.id.substring(0, 12)}</span>
            </h1>
            {getStatusBadge(payment.status)}
          </div>
          <p className="text-gray-600 dark:text-gray-400 ml-9">
            Payment recorded on {formatDate(payment.created_at)}
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-3">
          {payment.status === 'succeeded' && (
            <Button
              variant="outline"
              onClick={() => setShowRefundModal(true)}
            >
              <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
              </svg>
              Process Refund
            </Button>
          )}
          {payment.status === 'failed' && (
            <Button
              variant="primary"
              onClick={() => retryMutation.mutate()}
              isLoading={retryMutation.isPending}
            >
              <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Retry Payment
            </Button>
          )}
          {payment.status === 'succeeded' && (
            <Button variant="outline" onClick={handleDownloadReceipt}>
              <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Download Receipt
            </Button>
          )}
          {payment.status === 'succeeded' && (
            <Button
              variant="outline"
              onClick={() => sendReceiptMutation.mutate()}
              isLoading={sendReceiptMutation.isPending}
            >
              <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              Send Receipt
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Payment Info Card */}
          <Card>
            <CardHeader>
              <CardTitle>Payment Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Amount Display */}
              <div className="text-center py-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Amount</p>
                <p className="text-4xl font-bold text-gray-900 dark:text-white">
                  {formatCurrency(payment.amount, payment.currency)}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 uppercase">
                  {payment.currency || 'USD'}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Payment Method</label>
                  <div className="flex items-center space-x-2 mt-1">
                    <span className="text-gray-500 dark:text-gray-400">
                      {getPaymentMethodIcon(paymentMethodType)}
                    </span>
                    <span className="text-gray-900 dark:text-white capitalize">
                      {paymentMethodType?.replace('_', ' ') || 'Unknown'}
                    </span>
                    {cardLast4 && (
                      <span className="text-gray-500 dark:text-gray-400 font-mono">
                        **** {cardLast4}
                      </span>
                    )}
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Status</label>
                  <div className="mt-1">{getStatusBadge(payment.status)}</div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <div>
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Created</label>
                  <p className="text-gray-900 dark:text-white mt-1">{formatDateTime(payment.created_at)}</p>
                </div>
                {payment.paid_at && (
                  <div>
                    <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Paid At</label>
                    <p className="text-green-600 dark:text-green-400 font-medium mt-1">
                      {formatDateTime(payment.paid_at)}
                    </p>
                  </div>
                )}
              </div>

              {payment.notes && (
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Notes</label>
                  <p className="text-gray-900 dark:text-white mt-1">{payment.notes}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Invoice Link Card */}
          {payment.invoice && (
            <Card>
              <CardHeader>
                <CardTitle>Related Invoice</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <p className="font-medium text-gray-900 dark:text-white">
                      {payment.invoice.invoice_number}
                    </p>
                    {payment.invoice.client && (
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {clientName}
                      </p>
                    )}
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Total: {formatCurrency(payment.invoice.total, payment.invoice.currency)}
                    </p>
                  </div>
                  <Link to={`/invoices/${payment.invoice.id}`}>
                    <Button variant="outline" size="sm">
                      <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                      View Invoice
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Stripe Details Card */}
          {(payment.stripe_payment_intent_id || cardLast4 || cardBrand) && (
            <Card>
              <CardHeader>
                <CardTitle>
                  <div className="flex items-center space-x-2">
                    <svg className="w-5 h-5 text-purple-600 dark:text-purple-400" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M13.976 9.15c-2.172-.806-3.356-1.426-3.356-2.409 0-.831.683-1.305 1.901-1.305 2.227 0 4.515.858 6.09 1.631l.89-5.494C18.252.975 15.697 0 12.165 0 9.667 0 7.589.654 6.104 1.872 4.56 3.147 3.757 4.992 3.757 7.218c0 4.039 2.467 5.76 6.476 7.219 2.585.92 3.445 1.574 3.445 2.583 0 .98-.84 1.545-2.354 1.545-1.875 0-4.965-.921-7.076-2.19l-.89 5.494C5.108 22.88 8.102 24 11.738 24c2.666 0 4.836-.749 6.213-1.872 1.659-1.36 2.497-3.291 2.497-5.758 0-4.153-2.544-5.822-6.472-7.22z" />
                    </svg>
                    <span>Stripe Details</span>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {payment.stripe_payment_intent_id && (
                  <div>
                    <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Payment Intent ID</label>
                    <p className="text-gray-900 dark:text-white mt-1 font-mono text-sm break-all">
                      {payment.stripe_payment_intent_id}
                    </p>
                  </div>
                )}
                {payment.transaction_id && (
                  <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
                    <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Transaction / Charge ID</label>
                    <p className="text-gray-900 dark:text-white mt-1 font-mono text-sm break-all">
                      {payment.transaction_id}
                    </p>
                  </div>
                )}
                {cardBrand && (
                  <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
                    <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Card Brand</label>
                    <p className="text-gray-900 dark:text-white mt-1 capitalize">{cardBrand}</p>
                  </div>
                )}
                {cardLast4 && (
                  <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
                    <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Card Last 4</label>
                    <p className="text-gray-900 dark:text-white mt-1 font-mono">**** **** **** {cardLast4}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Amount</label>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                  {formatCurrency(payment.amount, payment.currency)}
                </p>
              </div>

              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Status</label>
                <div className="mt-1">{getStatusBadge(payment.status)}</div>
              </div>

              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Currency</label>
                <p className="text-gray-900 dark:text-white mt-1 uppercase">{payment.currency || 'USD'}</p>
              </div>

              {payment.invoice?.client && (
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Client</label>
                  <Link
                    to={`/clients/${payment.invoice.client.id}`}
                    className="text-primary-600 hover:underline dark:text-primary-400 mt-1 inline-block"
                  >
                    {clientName}
                  </Link>
                </div>
              )}

              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Created</label>
                <p className="text-gray-900 dark:text-white mt-1">{formatDate(payment.created_at)}</p>
              </div>

              {payment.updated_at && (
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Last Updated</label>
                  <p className="text-gray-900 dark:text-white mt-1">{formatDate(payment.updated_at)}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Payment Timeline */}
          <Card>
            <CardHeader>
              <CardTitle>Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-0">
                {/* Created event */}
                <div className="relative pl-8 pb-6">
                  <div className="absolute left-0 top-1.5 w-6 h-6 rounded-full bg-blue-500 border-2 border-blue-500 flex items-center justify-center">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="absolute left-3 top-8 bottom-0 w-0.5 bg-gray-200 dark:bg-gray-700" />
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">Payment Created</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                      {formatDateTime(payment.created_at)}
                    </p>
                  </div>
                </div>

                {/* Paid event */}
                {payment.paid_at && (
                  <div className="relative pl-8 pb-6">
                    <div className="absolute left-0 top-1.5 w-6 h-6 rounded-full bg-green-500 border-2 border-green-500 flex items-center justify-center">
                      <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                    {(payment.status === 'refunded' || payment.status === 'partially_refunded') && (
                      <div className="absolute left-3 top-8 bottom-0 w-0.5 bg-gray-200 dark:bg-gray-700" />
                    )}
                    <div>
                      <p className="font-medium text-green-600 dark:text-green-400">Payment Succeeded</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                        {formatDateTime(payment.paid_at)}
                      </p>
                    </div>
                  </div>
                )}

                {/* Failed event */}
                {payment.status === 'failed' && !payment.paid_at && (
                  <div className="relative pl-8 pb-6">
                    <div className="absolute left-0 top-1.5 w-6 h-6 rounded-full bg-red-500 border-2 border-red-500 flex items-center justify-center">
                      <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div>
                      <p className="font-medium text-red-600 dark:text-red-400">Payment Failed</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                        {formatDateTime(payment.updated_at)}
                      </p>
                    </div>
                  </div>
                )}

                {/* Refunded event */}
                {(payment.status === 'refunded' || payment.status === 'partially_refunded') && (
                  <div className="relative pl-8 pb-2">
                    <div className="absolute left-0 top-1.5 w-6 h-6 rounded-full bg-gray-500 border-2 border-gray-500 flex items-center justify-center">
                      <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M7.707 3.293a1 1 0 010 1.414L5.414 7H11a7 7 0 017 7v2a1 1 0 11-2 0v-2a5 5 0 00-5-5H5.414l2.293 2.293a1 1 0 11-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div>
                      <p className="font-medium text-gray-600 dark:text-gray-300">
                        {payment.status === 'refunded' ? 'Fully Refunded' : 'Partially Refunded'}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                        {formatDateTime(payment.updated_at)}
                      </p>
                    </div>
                  </div>
                )}

                {/* Dynamic history events */}
                {history && history.length > 0 && (
                  <div className="pt-4 mt-4 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-4">
                      Detailed History
                    </p>
                    {history.map((event, index) => (
                      <div key={index} className="relative pl-8 pb-4 last:pb-0">
                        <div className="absolute left-0 top-1.5 w-4 h-4 rounded-full bg-gray-300 dark:bg-gray-600 ml-1" />
                        {index < history.length - 1 && (
                          <div className="absolute left-3 top-6 bottom-0 w-0.5 bg-gray-200 dark:bg-gray-700" />
                        )}
                        <div>
                          <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                            {event.event}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                            {event.description}
                          </p>
                          <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
                            {formatDateTime(event.timestamp)}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {payment.receipt_url && (
                <a href={payment.receipt_url} target="_blank" rel="noopener noreferrer" className="block">
                  <Button variant="outline" fullWidth>
                    <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                    View Stripe Receipt
                  </Button>
                </a>
              )}
              {payment.invoice && (
                <Button variant="outline" fullWidth onClick={() => navigate(`/invoices/${payment.invoice.id}`)}>
                  <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  View Invoice
                </Button>
              )}
              {payment.invoice?.client && (
                <Button variant="outline" fullWidth onClick={() => navigate(`/clients/${payment.invoice.client.id}`)}>
                  <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  View Client
                </Button>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Refund Modal */}
      {showRefundModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md m-4">
            <CardHeader>
              <CardTitle>Process Refund</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <p className="text-gray-600 dark:text-gray-400">
                  Original payment amount: <span className="font-semibold text-gray-900 dark:text-white">{formatCurrency(payment.amount, payment.currency)}</span>
                </p>

                <div>
                  <label htmlFor="refund-amount" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Refund Amount (leave empty for full refund)
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 dark:text-gray-400">$</span>
                    <input
                      id="refund-amount"
                      type="number"
                      step="0.01"
                      min="0.01"
                      max={payment.amount}
                      placeholder={payment.amount.toFixed(2)}
                      value={refundAmount}
                      onChange={(e) => setRefundAmount(e.target.value)}
                      className="w-full pl-8 pr-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="refund-reason" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Reason for Refund
                  </label>
                  <textarea
                    id="refund-reason"
                    rows={3}
                    placeholder="Describe the reason for this refund..."
                    value={refundReason}
                    onChange={(e) => setRefundReason(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>

                <div className="flex justify-end space-x-3 pt-2">
                  <Button
                    variant="outline"
                    onClick={() => {
                      setShowRefundModal(false);
                      setRefundAmount('');
                      setRefundReason('');
                    }}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="danger"
                    onClick={handleRefundSubmit}
                    isLoading={refundMutation.isPending}
                  >
                    <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
                    </svg>
                    Process Refund
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

export default PaymentDetail;
