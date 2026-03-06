/**
 * Payment Create Page
 * Aureon by Rhematek Solutions
 *
 * Form to record a manual payment against an invoice
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { paymentService, invoiceService } from '@/services';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Select from '@/components/common/Select';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import type { Invoice } from '@/types';

const PaymentCreate: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { success: showSuccessToast, error: showErrorToast } = useToast();

  const invoiceParam = searchParams.get('invoice');

  const [formData, setFormData] = useState({
    invoice_id: invoiceParam || '',
    amount: '',
    payment_method: 'card',
    payment_date: new Date().toISOString().split('T')[0],
    notes: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Fetch invoices for dropdown
  const { data: invoicesData } = useQuery({
    queryKey: ['invoices', { page: 1, pageSize: 100 }],
    queryFn: () =>
      invoiceService.getInvoices(
        { page: 1, pageSize: 100, page_size: 100 },
        { status: undefined },
      ),
  });

  // Fetch specific invoice if passed via URL param
  const { data: selectedInvoice } = useQuery({
    queryKey: ['invoice', invoiceParam],
    queryFn: () => invoiceService.getInvoice(invoiceParam!),
    enabled: !!invoiceParam,
  });

  // Auto-populate amount from invoice
  useEffect(() => {
    if (selectedInvoice && !formData.amount) {
      setFormData((prev) => ({
        ...prev,
        invoice_id: selectedInvoice.id,
        amount: selectedInvoice.total.toString(),
      }));
    }
  }, [selectedInvoice]);

  // Create payment mutation
  const createMutation = useMutation({
    mutationFn: (data: {
      invoice_id: string;
      amount: number;
      payment_method: string;
      payment_date: string;
      notes?: string;
    }) => paymentService.createPayment(data),
    onSuccess: (payment) => {
      showSuccessToast('Payment recorded successfully!');
      navigate(`/payments/${payment.id}`);
    },
    onError: (error: any) => {
      showErrorToast(error.response?.data?.message || 'Failed to record payment');
    },
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  // When invoice selection changes, auto-fill amount
  const handleInvoiceChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const invoiceId = e.target.value;
    setFormData((prev) => ({ ...prev, invoice_id: invoiceId }));

    if (invoiceId && invoicesData) {
      const invoice = invoicesData.results.find((inv: Invoice) => inv.id === invoiceId);
      if (invoice) {
        setFormData((prev) => ({
          ...prev,
          invoice_id: invoiceId,
          amount: invoice.total.toString(),
        }));
      }
    }

    if (errors.invoice_id) {
      setErrors((prev) => ({ ...prev, invoice_id: '' }));
    }
  };

  // Format currency for display
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.invoice_id) {
      newErrors.invoice_id = 'Invoice is required';
    }

    if (!formData.amount || parseFloat(formData.amount) <= 0) {
      newErrors.amount = 'A valid amount is required';
    }

    if (!formData.payment_method) {
      newErrors.payment_method = 'Payment method is required';
    }

    if (!formData.payment_date) {
      newErrors.payment_date = 'Payment date is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    createMutation.mutate({
      invoice_id: formData.invoice_id,
      amount: parseFloat(formData.amount),
      payment_method: formData.payment_method,
      payment_date: formData.payment_date,
      notes: formData.notes || undefined,
    });
  };

  // Get the selected invoice details for display
  const currentInvoice = selectedInvoice || invoicesData?.results.find((inv: Invoice) => inv.id === formData.invoice_id);

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/payments')}
              className="p-2 -ml-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              title="Back to payments"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </button>
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Record Payment</h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Manually record a payment against an invoice
              </p>
            </div>
          </div>
        </div>
        <Button variant="ghost" onClick={() => navigate('/payments')}>
          Cancel
        </Button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Invoice Selection */}
        <Card>
          <CardHeader>
            <CardTitle>Invoice</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Select
              id="invoice_id"
              name="invoice_id"
              label="Select Invoice"
              value={formData.invoice_id}
              onChange={handleInvoiceChange}
              options={[
                { value: '', label: 'Select an invoice...' },
                ...(invoicesData?.results.map((invoice: Invoice) => ({
                  value: invoice.id,
                  label: `${invoice.invoice_number} - ${
                    invoice.client?.type === 'individual'
                      ? `${invoice.client.first_name} ${invoice.client.last_name}`
                      : invoice.client?.company_name || 'Unknown'
                  } - ${formatCurrency(invoice.total)}`,
                })) || []),
              ]}
              error={errors.invoice_id}
              fullWidth
              required
            />

            {/* Invoice Summary */}
            {currentInvoice && (
              <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Invoice Number</p>
                    <p className="font-medium text-gray-900 dark:text-white">{currentInvoice.invoice_number}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Client</p>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {currentInvoice.client?.type === 'individual'
                        ? `${currentInvoice.client.first_name} ${currentInvoice.client.last_name}`
                        : currentInvoice.client?.company_name || 'Unknown'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Invoice Total</p>
                    <p className="font-semibold text-gray-900 dark:text-white">
                      {formatCurrency(currentInvoice.total)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Status</p>
                    <p className="font-medium text-gray-900 dark:text-white capitalize">
                      {currentInvoice.status?.replace('_', ' ')}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Payment Details */}
        <Card>
          <CardHeader>
            <CardTitle>Payment Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                id="amount"
                name="amount"
                type="number"
                step="0.01"
                min="0.01"
                label="Amount"
                placeholder="0.00"
                value={formData.amount}
                onChange={handleChange}
                error={errors.amount}
                fullWidth
                required
                leftIcon={
                  <span className="text-gray-500 dark:text-gray-400 font-medium">$</span>
                }
              />

              <Select
                id="payment_method"
                name="payment_method"
                label="Payment Method"
                value={formData.payment_method}
                onChange={handleChange}
                options={[
                  { value: 'card', label: 'Credit/Debit Card' },
                  { value: 'bank_transfer', label: 'Bank Transfer' },
                  { value: 'cash', label: 'Cash' },
                  { value: 'check', label: 'Check' },
                  { value: 'paypal', label: 'PayPal' },
                  { value: 'other', label: 'Other' },
                ]}
                error={errors.payment_method}
                fullWidth
                required
              />
            </div>

            <Input
              id="payment_date"
              name="payment_date"
              type="date"
              label="Payment Date"
              value={formData.payment_date}
              onChange={handleChange}
              error={errors.payment_date}
              fullWidth
              required
            />
          </CardContent>
        </Card>

        {/* Notes */}
        <Card>
          <CardHeader>
            <CardTitle>Additional Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <div>
              <label htmlFor="notes" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Notes (Optional)
              </label>
              <textarea
                id="notes"
                name="notes"
                rows={3}
                placeholder="Add any notes about this payment..."
                value={formData.notes}
                onChange={handleChange}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </CardContent>
        </Card>

        {/* Summary */}
        {formData.amount && parseFloat(formData.amount) > 0 && (
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <span className="text-lg font-medium text-gray-700 dark:text-gray-300">
                  Payment Amount
                </span>
                <span className="text-2xl font-bold text-gray-900 dark:text-white">
                  {formatCurrency(parseFloat(formData.amount))}
                </span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Actions */}
        <div className="flex items-center justify-end space-x-4">
          <Button
            type="button"
            variant="outline"
            size="lg"
            onClick={() => navigate('/payments')}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            size="lg"
            isLoading={createMutation.isPending}
          >
            <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Record Payment
          </Button>
        </div>
      </form>
    </div>
  );
};

export default PaymentCreate;
