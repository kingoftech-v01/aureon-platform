/**
 * Payment Receipt Page (Printable)
 * Aureon by Rhematek Solutions
 *
 * Generates a printable receipt for a completed payment with download and share options
 */

import React from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { paymentService } from '@/services';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Badge from '@/components/common/Badge';
import { SkeletonCard } from '@/components/common/Skeleton';
import type { Payment, PaymentStatus } from '@/types';

const PaymentReceipt: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { success: showSuccessToast, error: showErrorToast } = useToast();

  // Fetch payment data
  const { data: payment, isLoading, error } = useQuery({
    queryKey: ['payment', id],
    queryFn: () => paymentService.getPayment(id!),
    enabled: !!id,
  });

  // Send receipt via email mutation
  const sendReceiptMutation = useMutation({
    mutationFn: () => paymentService.sendReceipt(id!),
    onSuccess: () => {
      showSuccessToast('Receipt sent successfully via email');
    },
    onError: (err: any) => {
      showErrorToast(err.response?.data?.message || 'Failed to send receipt');
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
      month: 'long',
      day: 'numeric',
    });
  };

  // Status badge
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
    return <Badge variant={variants[status]} size="lg">{status.replace('_', ' ').toUpperCase()}</Badge>;
  };

  // Print handler
  const handlePrint = () => {
    window.print();
  };

  // Download PDF
  const handleDownloadPDF = async () => {
    try {
      const blob = await paymentService.getReceipt(id!);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `receipt-${payment?.transaction_id || payment?.payment_number || id}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      showSuccessToast('Receipt PDF downloaded');
    } catch (err: any) {
      showErrorToast('Failed to download receipt PDF');
    }
  };

  // Share via email
  const handleShareEmail = () => {
    sendReceiptMutation.mutate();
  };

  // Extract client info
  const getClientName = (p: Payment) => {
    if (!p.invoice?.client) return 'N/A';
    return p.invoice.client.type === 'individual'
      ? `${p.invoice.client.first_name} ${p.invoice.client.last_name}`
      : p.invoice.client.company_name || 'N/A';
  };

  const getClientEmail = (p: Payment) => {
    return p.invoice?.client?.email || 'N/A';
  };

  const getClientAddress = (p: Payment) => {
    const client = p.invoice?.client;
    if (!client) return null;
    const parts = [
      client.address,
      client.city,
      client.state,
      client.postal_code,
      client.country,
    ].filter(Boolean);
    return parts.length > 0 ? parts.join(', ') : null;
  };

  // Payment method display
  const getPaymentMethodDisplay = (p: Payment) => {
    const method = p.payment_method;
    if (typeof method === 'object' && method) {
      const brand = method.brand ? `${method.brand} ` : '';
      const last4 = method.last4 ? `**** ${method.last4}` : '';
      return `${brand}${method.type || 'Card'} ${last4}`.trim();
    }
    return typeof method === 'string' ? method.replace('_', ' ') : 'N/A';
  };

  // Generate receipt number
  const getReceiptNumber = (p: Payment) => {
    return p.transaction_id || p.payment_number || `RCT-${p.id.substring(0, 8).toUpperCase()}`;
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <SkeletonCard />
        <SkeletonCard />
      </div>
    );
  }

  // Error state
  if (error || !payment) {
    return (
      <div className="max-w-4xl mx-auto text-center py-16">
        <div className="w-16 h-16 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Payment not found</h3>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          The payment receipt you are looking for does not exist.
        </p>
        <Link to="/payments">
          <Button variant="primary">Back to Payments</Button>
        </Link>
      </div>
    );
  }

  // Mock line items from invoice or generate from payment
  const lineItems = payment.invoice?.items && payment.invoice.items.length > 0
    ? payment.invoice.items
    : [
        {
          id: '1',
          description: payment.invoice?.description || payment.notes || 'Payment',
          quantity: 1,
          rate: payment.amount,
          amount: payment.amount,
        },
      ];

  const subtotal = lineItems.reduce((sum: number, item: any) => sum + (item.amount || item.quantity * item.rate), 0);
  const taxRate = payment.invoice?.tax_rate || 0;
  const taxAmount = subtotal * (taxRate / 100);
  const total = payment.amount;

  return (
    <div className="max-w-4xl mx-auto">
      {/* Action Bar - Hidden on print */}
      <div className="print:hidden flex items-center justify-between mb-6">
        <button
          onClick={() => navigate(`/payments/${id}`)}
          className="flex items-center space-x-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span>Back to Payment</span>
        </button>

        <div className="flex items-center space-x-3">
          <Button variant="outline" onClick={handlePrint}>
            <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
            </svg>
            Print
          </Button>
          <Button variant="outline" onClick={handleDownloadPDF}>
            <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Download PDF
          </Button>
          <Button
            variant="primary"
            onClick={handleShareEmail}
            isLoading={sendReceiptMutation.isPending}
          >
            <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            Share via Email
          </Button>
        </div>
      </div>

      {/* Receipt Document */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 print:shadow-none print:border-none print:rounded-none">
        {/* Receipt Header */}
        <div className="px-8 py-8 border-b border-gray-200 dark:border-gray-700 print:border-gray-300">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-4">
              {/* Logo Placeholder */}
              <div className="w-16 h-16 bg-gradient-to-br from-primary-400 to-primary-600 rounded-xl flex items-center justify-center print:bg-primary-500">
                <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white print:text-gray-900">
                  Aureon Finance
                </h1>
                <p className="text-sm text-gray-500 dark:text-gray-400 print:text-gray-500">
                  Powered by Rhematek Solutions
                </p>
              </div>
            </div>
            <div className="text-right">
              <h2 className="text-3xl font-bold text-gray-900 dark:text-white tracking-wide print:text-gray-900">
                RECEIPT
              </h2>
              <div className="mt-2 print:hidden">
                {getStatusBadge(payment.status)}
              </div>
              <p className="mt-2 hidden print:block text-sm font-medium text-gray-700">
                Status: {payment.status.replace('_', ' ').toUpperCase()}
              </p>
            </div>
          </div>
        </div>

        {/* Receipt Details */}
        <div className="px-8 py-6 grid grid-cols-2 gap-8 border-b border-gray-200 dark:border-gray-700 print:border-gray-300">
          {/* Receipt Info */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider print:text-gray-500">
              Receipt Details
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400 print:text-gray-600">Receipt No:</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white font-mono print:text-gray-900">
                  {getReceiptNumber(payment)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400 print:text-gray-600">Date:</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white print:text-gray-900">
                  {formatDate(payment.paid_at || payment.created_at)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400 print:text-gray-600">Payment Method:</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white capitalize print:text-gray-900">
                  {getPaymentMethodDisplay(payment)}
                </span>
              </div>
              {payment.invoice?.invoice_number && (
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400 print:text-gray-600">Invoice:</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white font-mono print:text-gray-900">
                    {payment.invoice.invoice_number}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Payer Info */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider print:text-gray-500">
              Paid By
            </h3>
            <div className="space-y-1">
              <p className="text-sm font-medium text-gray-900 dark:text-white print:text-gray-900">
                {getClientName(payment)}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400 print:text-gray-600">
                {getClientEmail(payment)}
              </p>
              {getClientAddress(payment) && (
                <p className="text-sm text-gray-600 dark:text-gray-400 print:text-gray-600">
                  {getClientAddress(payment)}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Items Table */}
        <div className="px-8 py-6">
          <table className="w-full">
            <thead>
              <tr className="border-b-2 border-gray-200 dark:border-gray-700 print:border-gray-300">
                <th className="text-left py-3 text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider print:text-gray-500">
                  Description
                </th>
                <th className="text-center py-3 text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider print:text-gray-500">
                  Qty
                </th>
                <th className="text-right py-3 text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider print:text-gray-500">
                  Rate
                </th>
                <th className="text-right py-3 text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider print:text-gray-500">
                  Amount
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700 print:divide-gray-200">
              {lineItems.map((item: any, index: number) => (
                <tr key={item.id || index}>
                  <td className="py-4 text-sm text-gray-900 dark:text-white print:text-gray-900">
                    {item.description || item.name || 'Service'}
                  </td>
                  <td className="py-4 text-sm text-center text-gray-600 dark:text-gray-400 print:text-gray-600">
                    {item.quantity || 1}
                  </td>
                  <td className="py-4 text-sm text-right text-gray-600 dark:text-gray-400 print:text-gray-600">
                    {formatCurrency(item.rate || item.unit_price || item.amount, payment.currency)}
                  </td>
                  <td className="py-4 text-sm text-right font-medium text-gray-900 dark:text-white print:text-gray-900">
                    {formatCurrency(item.amount || (item.quantity * item.rate), payment.currency)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Totals */}
          <div className="mt-6 border-t-2 border-gray-200 dark:border-gray-700 pt-4 print:border-gray-300">
            <div className="flex flex-col items-end space-y-2">
              <div className="flex justify-between w-64">
                <span className="text-sm text-gray-600 dark:text-gray-400 print:text-gray-600">Subtotal:</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white print:text-gray-900">
                  {formatCurrency(subtotal, payment.currency)}
                </span>
              </div>
              {taxRate > 0 && (
                <div className="flex justify-between w-64">
                  <span className="text-sm text-gray-600 dark:text-gray-400 print:text-gray-600">
                    Tax ({taxRate}%):
                  </span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white print:text-gray-900">
                    {formatCurrency(taxAmount, payment.currency)}
                  </span>
                </div>
              )}
              <div className="flex justify-between w-64 pt-2 border-t border-gray-200 dark:border-gray-600 print:border-gray-300">
                <span className="text-base font-semibold text-gray-900 dark:text-white print:text-gray-900">
                  Total Paid:
                </span>
                <span className="text-base font-bold text-gray-900 dark:text-white print:text-gray-900">
                  {formatCurrency(total, payment.currency)}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Payment Status Banner */}
        <div className={`mx-8 mb-6 rounded-lg p-4 ${
          payment.status === 'succeeded'
            ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 print:bg-green-50 print:border-green-200'
            : payment.status === 'refunded'
            ? 'bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 print:bg-gray-50 print:border-gray-200'
            : 'bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 print:bg-yellow-50 print:border-yellow-200'
        }`}>
          <div className="flex items-center space-x-3">
            {payment.status === 'succeeded' ? (
              <svg className="w-6 h-6 text-green-600 dark:text-green-400 print:text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            ) : (
              <svg className="w-6 h-6 text-yellow-600 dark:text-yellow-400 print:text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}
            <div>
              <p className={`text-sm font-medium ${
                payment.status === 'succeeded'
                  ? 'text-green-800 dark:text-green-300 print:text-green-800'
                  : 'text-yellow-800 dark:text-yellow-300 print:text-yellow-800'
              }`}>
                {payment.status === 'succeeded'
                  ? 'Payment Confirmed'
                  : payment.status === 'refunded'
                  ? 'Payment Refunded'
                  : 'Payment Pending'}
              </p>
              <p className={`text-xs ${
                payment.status === 'succeeded'
                  ? 'text-green-600 dark:text-green-400 print:text-green-600'
                  : 'text-yellow-600 dark:text-yellow-400 print:text-yellow-600'
              }`}>
                {payment.status === 'succeeded' && payment.paid_at
                  ? `Processed on ${formatDate(payment.paid_at)}`
                  : `Created on ${formatDate(payment.created_at)}`}
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-8 py-6 bg-gray-50 dark:bg-gray-900/30 rounded-b-lg border-t border-gray-200 dark:border-gray-700 print:bg-gray-50 print:border-gray-300">
          <div className="text-center space-y-2">
            <p className="text-xs text-gray-500 dark:text-gray-400 print:text-gray-500">
              This is an automatically generated receipt. Please retain it for your records.
            </p>
            {payment.stripe_payment_intent_id && (
              <p className="text-xs text-gray-400 dark:text-gray-500 font-mono print:text-gray-400">
                Transaction ID: {payment.stripe_payment_intent_id}
              </p>
            )}
            <p className="text-xs text-gray-400 dark:text-gray-500 print:text-gray-400">
              Aureon Finance Management -- Powered by Rhematek Solutions
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaymentReceipt;
