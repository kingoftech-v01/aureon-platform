/**
 * Invoice PDF Preview Page
 * Aureon by Rhematek Solutions
 *
 * Full-width preview of an invoice styled like a paper document with action controls
 */

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { invoiceService } from '@/services';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Badge from '@/components/common/Badge';
import { SkeletonCard } from '@/components/common/Skeleton';
import type { Invoice, InvoiceStatus } from '@/types';

const InvoicePDFPreview: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { success: showSuccessToast, error: showErrorToast } = useToast();

  // Fetch invoice data
  const { data: invoice, isLoading, error } = useQuery({
    queryKey: ['invoice', id],
    queryFn: () => invoiceService.getInvoice(id!),
    enabled: !!id,
  });

  // Send invoice mutation
  const sendMutation = useMutation({
    mutationFn: () => invoiceService.sendInvoice(id!),
    onSuccess: () => {
      showSuccessToast('Invoice sent to client successfully');
    },
    onError: (err: any) => {
      showErrorToast(err.response?.data?.message || 'Failed to send invoice');
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
  const getStatusVariant = (status: InvoiceStatus): 'default' | 'primary' | 'success' | 'warning' | 'info' | 'danger' => {
    const map: Record<string, 'default' | 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
      draft: 'default',
      sent: 'info',
      paid: 'success',
      overdue: 'danger',
      cancelled: 'default',
      void: 'default',
    };
    return map[status] || 'default';
  };

  // Download PDF handler
  const handleDownloadPDF = async () => {
    try {
      const blob = await invoiceService.generatePDF(id!);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `invoice-${invoice?.invoice_number || id}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      showSuccessToast('Invoice PDF downloaded');
    } catch (err: any) {
      showErrorToast('Failed to download PDF');
    }
  };

  // Print handler
  const handlePrint = () => {
    window.print();
  };

  // Client info
  const getClientName = (inv: Invoice) => {
    if (!inv.client) return 'N/A';
    return inv.client.type === 'individual'
      ? `${inv.client.first_name} ${inv.client.last_name}`
      : inv.client.company_name || 'N/A';
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto space-y-6">
        <SkeletonCard />
        <SkeletonCard />
      </div>
    );
  }

  // Error state
  if (error || !invoice) {
    return (
      <div className="max-w-5xl mx-auto text-center py-16">
        <div className="w-16 h-16 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Invoice not found</h3>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          The invoice you are looking for does not exist or has been deleted.
        </p>
        <Button variant="primary" onClick={() => navigate('/invoices')}>Back to Invoices</Button>
      </div>
    );
  }

  const lineItems = invoice.items || [];
  const subtotal = invoice.subtotal || lineItems.reduce((sum: number, item: any) => sum + (item.amount || item.quantity * item.unit_price), 0);
  const taxAmount = invoice.tax_amount || 0;
  const discount = invoice.discount_amount || 0;
  const total = invoice.total || subtotal + taxAmount - discount;

  return (
    <div className="max-w-5xl mx-auto">
      {/* Action Bar - Hidden on print */}
      <div className="print:hidden flex items-center justify-between mb-6">
        <button
          onClick={() => navigate(`/invoices/${id}`)}
          className="flex items-center space-x-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span>Back to Invoice</span>
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
            onClick={() => sendMutation.mutate()}
            isLoading={sendMutation.isPending}
            disabled={invoice.status === 'paid' || invoice.status === 'cancelled'}
          >
            <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
            Send to Client
          </Button>
          <Button variant="ghost" onClick={() => navigate(`/invoices/${id}/edit`)}>
            <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Edit Invoice
          </Button>
        </div>
      </div>

      {/* Invoice Paper Document */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700 print:shadow-none print:border-none print:rounded-none">
        {/* Header */}
        <div className="px-10 py-8 border-b border-gray-100 dark:border-gray-700 print:border-gray-200">
          <div className="flex items-start justify-between">
            {/* Company Info */}
            <div className="space-y-2">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-gradient-to-br from-primary-400 to-primary-600 rounded-lg flex items-center justify-center print:bg-primary-500">
                  <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900 dark:text-white print:text-gray-900">
                    Aureon Finance
                  </h1>
                  <p className="text-sm text-gray-500 dark:text-gray-400 print:text-gray-500">
                    Rhematek Solutions
                  </p>
                </div>
              </div>
            </div>

            {/* Invoice Title and Status */}
            <div className="text-right">
              <h2 className="text-3xl font-bold text-gray-900 dark:text-white tracking-wide print:text-gray-900">
                INVOICE
              </h2>
              <p className="text-lg font-mono font-semibold text-primary-600 dark:text-primary-400 mt-1 print:text-primary-600">
                {invoice.invoice_number}
              </p>
              <div className="mt-2 print:hidden">
                <Badge variant={getStatusVariant(invoice.status)} size="lg">
                  {invoice.status.toUpperCase()}
                </Badge>
              </div>
              <p className="mt-2 hidden print:block text-sm font-medium text-gray-700">
                Status: {invoice.status.toUpperCase()}
              </p>
            </div>
          </div>
        </div>

        {/* Dates and Bill To */}
        <div className="px-10 py-6 grid grid-cols-2 gap-8 border-b border-gray-100 dark:border-gray-700 print:border-gray-200">
          {/* Invoice Dates */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider print:text-gray-500">
              Invoice Information
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400 print:text-gray-600">Issue Date:</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white print:text-gray-900">
                  {formatDate(invoice.issue_date || invoice.created_at)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400 print:text-gray-600">Due Date:</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white print:text-gray-900">
                  {invoice.due_date ? formatDate(invoice.due_date) : 'Upon Receipt'}
                </span>
              </div>
              {invoice.payment_terms && (
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400 print:text-gray-600">Terms:</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white print:text-gray-900">
                    {invoice.payment_terms}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Bill To */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider print:text-gray-500">
              Bill To
            </h3>
            <div className="space-y-1">
              <p className="text-sm font-semibold text-gray-900 dark:text-white print:text-gray-900">
                {getClientName(invoice)}
              </p>
              {invoice.client?.email && (
                <p className="text-sm text-gray-600 dark:text-gray-400 print:text-gray-600">
                  {invoice.client.email}
                </p>
              )}
              {invoice.client?.phone && (
                <p className="text-sm text-gray-600 dark:text-gray-400 print:text-gray-600">
                  {invoice.client.phone}
                </p>
              )}
              {invoice.client?.address && (
                <p className="text-sm text-gray-600 dark:text-gray-400 print:text-gray-600">
                  {[invoice.client.address, invoice.client.city, invoice.client.state, invoice.client.postal_code, invoice.client.country].filter(Boolean).join(', ')}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Line Items */}
        <div className="px-10 py-6">
          <table className="w-full">
            <thead>
              <tr className="border-b-2 border-gray-200 dark:border-gray-600 print:border-gray-300">
                <th className="text-left py-3 text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider print:text-gray-500 w-1/2">
                  Description
                </th>
                <th className="text-center py-3 text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider print:text-gray-500">
                  Qty
                </th>
                <th className="text-right py-3 text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider print:text-gray-500">
                  Unit Price
                </th>
                <th className="text-right py-3 text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider print:text-gray-500">
                  Amount
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700 print:divide-gray-200">
              {lineItems.length > 0 ? (
                lineItems.map((item: any, index: number) => (
                  <tr key={item.id || index}>
                    <td className="py-4 print:text-gray-900">
                      <p className="text-sm font-medium text-gray-900 dark:text-white print:text-gray-900">
                        {item.description || item.name}
                      </p>
                    </td>
                    <td className="py-4 text-sm text-center text-gray-600 dark:text-gray-400 print:text-gray-600">
                      {item.quantity}
                    </td>
                    <td className="py-4 text-sm text-right text-gray-600 dark:text-gray-400 print:text-gray-600">
                      {formatCurrency(item.unit_price || item.rate, invoice.currency)}
                    </td>
                    <td className="py-4 text-sm text-right font-medium text-gray-900 dark:text-white print:text-gray-900">
                      {formatCurrency(item.amount || item.quantity * (item.unit_price || item.rate), invoice.currency)}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td className="py-4 text-sm text-gray-900 dark:text-white print:text-gray-900">
                    {invoice.description || 'Professional Services'}
                  </td>
                  <td className="py-4 text-sm text-center text-gray-600 dark:text-gray-400 print:text-gray-600">1</td>
                  <td className="py-4 text-sm text-right text-gray-600 dark:text-gray-400 print:text-gray-600">
                    {formatCurrency(total, invoice.currency)}
                  </td>
                  <td className="py-4 text-sm text-right font-medium text-gray-900 dark:text-white print:text-gray-900">
                    {formatCurrency(total, invoice.currency)}
                  </td>
                </tr>
              )}
            </tbody>
          </table>

          {/* Totals */}
          <div className="mt-6 flex justify-end">
            <div className="w-72 space-y-2">
              <div className="flex justify-between py-1">
                <span className="text-sm text-gray-600 dark:text-gray-400 print:text-gray-600">Subtotal:</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white print:text-gray-900">
                  {formatCurrency(subtotal, invoice.currency)}
                </span>
              </div>
              {discount > 0 && (
                <div className="flex justify-between py-1">
                  <span className="text-sm text-gray-600 dark:text-gray-400 print:text-gray-600">Discount:</span>
                  <span className="text-sm font-medium text-red-600 dark:text-red-400 print:text-red-600">
                    -{formatCurrency(discount, invoice.currency)}
                  </span>
                </div>
              )}
              {taxAmount > 0 && (
                <div className="flex justify-between py-1">
                  <span className="text-sm text-gray-600 dark:text-gray-400 print:text-gray-600">
                    Tax{invoice.tax_rate ? ` (${invoice.tax_rate}%)` : ''}:
                  </span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white print:text-gray-900">
                    {formatCurrency(taxAmount, invoice.currency)}
                  </span>
                </div>
              )}
              <div className="flex justify-between py-2 border-t-2 border-gray-300 dark:border-gray-600 print:border-gray-400">
                <span className="text-lg font-bold text-gray-900 dark:text-white print:text-gray-900">Total:</span>
                <span className="text-lg font-bold text-gray-900 dark:text-white print:text-gray-900">
                  {formatCurrency(total, invoice.currency)}
                </span>
              </div>
              {invoice.amount_paid != null && invoice.amount_paid > 0 && invoice.amount_paid < total && (
                <>
                  <div className="flex justify-between py-1">
                    <span className="text-sm text-gray-600 dark:text-gray-400 print:text-gray-600">Amount Paid:</span>
                    <span className="text-sm font-medium text-green-600 dark:text-green-400 print:text-green-600">
                      -{formatCurrency(invoice.amount_paid, invoice.currency)}
                    </span>
                  </div>
                  <div className="flex justify-between py-1 border-t border-gray-200 dark:border-gray-600 print:border-gray-300">
                    <span className="text-sm font-semibold text-gray-900 dark:text-white print:text-gray-900">Balance Due:</span>
                    <span className="text-sm font-bold text-red-600 dark:text-red-400 print:text-red-600">
                      {formatCurrency(total - invoice.amount_paid, invoice.currency)}
                    </span>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Notes and Terms */}
        {(invoice.notes || invoice.terms) && (
          <div className="px-10 py-6 border-t border-gray-100 dark:border-gray-700 print:border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {invoice.notes && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2 print:text-gray-500">
                    Notes
                  </h4>
                  <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap print:text-gray-700">
                    {invoice.notes}
                  </p>
                </div>
              )}
              {invoice.terms && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2 print:text-gray-500">
                    Terms & Conditions
                  </h4>
                  <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap print:text-gray-700">
                    {invoice.terms}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="px-10 py-6 bg-gray-50 dark:bg-gray-900/30 rounded-b-lg border-t border-gray-200 dark:border-gray-700 print:bg-gray-50 print:border-gray-300">
          <div className="text-center space-y-1">
            <p className="text-xs text-gray-500 dark:text-gray-400 print:text-gray-500">
              Thank you for your business.
            </p>
            <p className="text-xs text-gray-400 dark:text-gray-500 print:text-gray-400">
              Aureon Finance Management -- Powered by Rhematek Solutions
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InvoicePDFPreview;
