/**
 * Invoice Detail Page
 * Aureon by Rhematek Solutions
 *
 * Detailed view of a single invoice with PDF preview
 */

import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { invoiceService } from '@/services';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import { SkeletonCard } from '@/components/common/Skeleton';
import type { Invoice, InvoiceStatus } from '@/types';

const InvoiceDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success: showSuccessToast, error: showErrorToast } = useToast();
  const [showMarkPaidModal, setShowMarkPaidModal] = useState(false);

  // Fetch invoice data
  const { data: invoice, isLoading, error } = useQuery({
    queryKey: ['invoice', id],
    queryFn: () => invoiceService.getInvoice(id!),
    enabled: !!id,
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: () => invoiceService.deleteInvoice(id!),
    onSuccess: () => {
      showSuccessToast('Invoice deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      navigate('/invoices');
    },
    onError: (error: any) => {
      showErrorToast(error.response?.data?.message || 'Failed to delete invoice');
    },
  });

  // Send invoice mutation
  const sendMutation = useMutation({
    mutationFn: () => invoiceService.sendInvoice(id!),
    onSuccess: () => {
      showSuccessToast('Invoice sent successfully');
      queryClient.invalidateQueries({ queryKey: ['invoice', id] });
    },
    onError: (error: any) => {
      showErrorToast(error.response?.data?.message || 'Failed to send invoice');
    },
  });

  // Mark as paid mutation
  const markPaidMutation = useMutation({
    mutationFn: (data: { payment_date?: string }) =>
      invoiceService.markAsPaid(id!, data),
    onSuccess: () => {
      showSuccessToast('Invoice marked as paid');
      queryClient.invalidateQueries({ queryKey: ['invoice', id] });
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      setShowMarkPaidModal(false);
    },
    onError: (error: any) => {
      showErrorToast(error.response?.data?.message || 'Failed to mark invoice as paid');
    },
  });

  // Download PDF
  const handleDownloadPDF = async () => {
    try {
      await invoiceService.downloadPDF(id!, `invoice-${invoice?.invoice_number}.pdf`);
      showSuccessToast('Invoice PDF downloaded');
    } catch (error: any) {
      showErrorToast('Failed to download PDF');
    }
  };

  // Handle delete
  const handleDelete = () => {
    if (window.confirm('Are you sure you want to delete this invoice? This action cannot be undone.')) {
      deleteMutation.mutate();
    }
  };

  // Invoice status badge
  const getStatusBadge = (status: InvoiceStatus) => {
    const variants: Record<InvoiceStatus, 'default' | 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
      draft: 'default',
      sent: 'info',
      viewed: 'primary',
      paid: 'success',
      partially_paid: 'warning',
      overdue: 'danger',
      cancelled: 'default',
    };
    return <Badge variant={variants[status]}>{status.replace('_', ' ')}</Badge>;
  };

  // Format currency
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
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

  // Check if overdue
  const isOverdue = (invoice: Invoice) => {
    if (invoice.status === 'paid' || invoice.status === 'cancelled') {
      return false;
    }
    return new Date(invoice.due_date) < new Date();
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
  if (error || !invoice) {
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
              Invoice not found
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              The invoice you're looking for doesn't exist or has been deleted.
            </p>
            <Link to="/invoices">
              <Button variant="primary">Back to Invoices</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center space-x-3 mb-2">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              {invoice.invoice_number}
            </h1>
            <div className="flex items-center space-x-2">
              {getStatusBadge(invoice.status)}
              {isOverdue(invoice) && <Badge variant="danger">Overdue</Badge>}
            </div>
          </div>
          <Link
            to={`/clients/${invoice.client.id}`}
            className="text-primary-600 hover:underline dark:text-primary-400"
          >
            {invoice.client.type === 'individual'
              ? `${invoice.client.first_name} ${invoice.client.last_name}`
              : invoice.client.company_name}
          </Link>
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-3">
          {invoice.status === 'draft' && (
            <Button
              variant="primary"
              onClick={() => sendMutation.mutate()}
              isLoading={sendMutation.isPending}
            >
              <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              Send Invoice
            </Button>
          )}
          {invoice.status !== 'paid' && invoice.status !== 'cancelled' && (
            <Button variant="success" onClick={() => setShowMarkPaidModal(true)}>
              <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Mark as Paid
            </Button>
          )}
          <Button variant="outline" onClick={handleDownloadPDF}>
            <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Download PDF
          </Button>
          <Link to={`/invoices/${invoice.id}/edit`}>
            <Button variant="outline">
              <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              Edit
            </Button>
          </Link>
          <Button
            variant="outline"
            onClick={handleDelete}
            isLoading={deleteMutation.isPending}
            className="text-red-600 hover:text-red-700 hover:border-red-600 dark:text-red-400"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Invoice Details */}
          <Card>
            <CardHeader>
              <CardTitle>Invoice Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Issue Date</label>
                  <p className="text-gray-900 dark:text-white mt-1">{formatDate(invoice.issue_date)}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Due Date</label>
                  <p className={`mt-1 ${isOverdue(invoice) ? 'text-red-600 dark:text-red-400 font-medium' : 'text-gray-900 dark:text-white'}`}>
                    {formatDate(invoice.due_date)}
                  </p>
                </div>
              </div>

              {invoice.paid_date && (
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Paid On</label>
                  <p className="text-green-600 dark:text-green-400 font-medium mt-1">
                    {formatDate(invoice.paid_date)}
                  </p>
                </div>
              )}

              {invoice.payment_terms && (
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Payment Terms</label>
                  <p className="text-gray-900 dark:text-white mt-1">{invoice.payment_terms}</p>
                </div>
              )}

              {invoice.notes && (
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Notes</label>
                  <p className="text-gray-900 dark:text-white mt-1">{invoice.notes}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Line Items */}
          <Card>
            <CardHeader>
              <CardTitle>Line Items</CardTitle>
            </CardHeader>
            <CardContent>
              {invoice.items && invoice.items.length > 0 ? (
                <div className="space-y-4">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-gray-200 dark:border-gray-700">
                          <th className="text-left py-3 text-sm font-medium text-gray-500 dark:text-gray-400">
                            Description
                          </th>
                          <th className="text-right py-3 text-sm font-medium text-gray-500 dark:text-gray-400">
                            Qty
                          </th>
                          <th className="text-right py-3 text-sm font-medium text-gray-500 dark:text-gray-400">
                            Rate
                          </th>
                          <th className="text-right py-3 text-sm font-medium text-gray-500 dark:text-gray-400">
                            Amount
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {invoice.items.map((item) => (
                          <tr key={item.id} className="border-b border-gray-100 dark:border-gray-800">
                            <td className="py-3 text-gray-900 dark:text-white">
                              <div>
                                <p className="font-medium">{item.description}</p>
                                {item.notes && (
                                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                                    {item.notes}
                                  </p>
                                )}
                              </div>
                            </td>
                            <td className="py-3 text-right text-gray-900 dark:text-white">
                              {item.quantity}
                            </td>
                            <td className="py-3 text-right text-gray-900 dark:text-white">
                              {formatCurrency(item.unit_price)}
                            </td>
                            <td className="py-3 text-right font-medium text-gray-900 dark:text-white">
                              {formatCurrency(item.amount)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Totals */}
                  <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600 dark:text-gray-400">Subtotal</span>
                        <span className="text-gray-900 dark:text-white">
                          {formatCurrency(invoice.subtotal)}
                        </span>
                      </div>
                      {invoice.discount_amount > 0 && (
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600 dark:text-gray-400">Discount</span>
                          <span className="text-red-600 dark:text-red-400">
                            -{formatCurrency(invoice.discount_amount)}
                          </span>
                        </div>
                      )}
                      {invoice.tax_amount > 0 && (
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600 dark:text-gray-400">
                            Tax ({invoice.tax_rate}%)
                          </span>
                          <span className="text-gray-900 dark:text-white">
                            {formatCurrency(invoice.tax_amount)}
                          </span>
                        </div>
                      )}
                      <div className="flex justify-between pt-2 border-t border-gray-200 dark:border-gray-700">
                        <span className="text-lg font-semibold text-gray-900 dark:text-white">
                          Total
                        </span>
                        <span className="text-lg font-bold text-gray-900 dark:text-white">
                          {formatCurrency(invoice.total)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-500 dark:text-gray-400">No line items</p>
                </div>
              )}
            </CardContent>
          </Card>
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
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Amount</label>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                  {formatCurrency(invoice.total)}
                </p>
              </div>

              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Status</label>
                <div className="mt-1">{getStatusBadge(invoice.status)}</div>
              </div>

              {invoice.contract && (
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Related Contract</label>
                  <Link
                    to={`/contracts/${invoice.contract}`}
                    className="text-primary-600 hover:underline dark:text-primary-400 mt-1 inline-block"
                  >
                    View Contract
                  </Link>
                </div>
              )}

              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Created</label>
                <p className="text-gray-900 dark:text-white mt-1">{formatDate(invoice.created_at)}</p>
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" fullWidth onClick={() => sendMutation.mutate()}>
                <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                Send Reminder
              </Button>
              <Button variant="outline" fullWidth onClick={() => navigate(`/invoices/create?duplicate=${id}`)}>
                <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Duplicate Invoice
              </Button>
              <Button variant="outline" fullWidth onClick={() => navigate(`/payments/create?invoice=${id}`)}>
                <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Record Payment
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Mark as Paid Modal */}
      {showMarkPaidModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md m-4">
            <CardHeader>
              <CardTitle>Mark Invoice as Paid</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Are you sure you want to mark this invoice as paid?
              </p>
              <div className="flex justify-end space-x-3">
                <Button variant="outline" onClick={() => setShowMarkPaidModal(false)}>
                  Cancel
                </Button>
                <Button
                  variant="success"
                  onClick={() => markPaidMutation.mutate({ payment_date: new Date().toISOString() })}
                  isLoading={markPaidMutation.isPending}
                >
                  Mark as Paid
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default InvoiceDetail;
