/**
 * Invoice Edit Page
 * Aureon by Rhematek Solutions
 *
 * Form to edit an existing invoice
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { invoiceService, clientService } from '@/services';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Select from '@/components/common/Select';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import { SkeletonCard } from '@/components/common/Skeleton';
import type { InvoiceFormData, InvoiceItem } from '@/types';

const InvoiceEdit: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success: showSuccessToast, error: showErrorToast } = useToast();

  const [formData, setFormData] = useState<Partial<InvoiceFormData>>({
    status: 'draft',
    currency: 'USD',
    tax_rate: 0,
    discount_amount: 0,
  });
  const [items, setItems] = useState<Partial<InvoiceItem>[]>([
    { description: '', quantity: 1, unit_price: 0, amount: 0 },
  ]);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Fetch existing invoice data
  const { data: invoice, isLoading } = useQuery({
    queryKey: ['invoice', id],
    queryFn: () => invoiceService.getInvoice(id!),
    enabled: !!id,
  });

  // Fetch clients for dropdown
  const { data: clientsData } = useQuery({
    queryKey: ['clients', { page: 1, pageSize: 100 }],
    queryFn: () => clientService.getClients({ page: 1, pageSize: 100 }),
  });

  // Populate form when invoice data is loaded
  useEffect(() => {
    if (invoice) {
      setFormData({
        client_id: invoice.client.id,
        issue_date: invoice.issue_date,
        due_date: invoice.due_date,
        status: invoice.status,
        payment_terms: invoice.payment_terms || '',
        notes: invoice.notes || '',
        tax_rate: invoice.tax_rate,
        discount_amount: invoice.discount_amount,
        currency: invoice.currency,
      });
      if (invoice.items && invoice.items.length > 0) {
        setItems(invoice.items);
      }
    }
  }, [invoice]);

  // Update invoice mutation
  const updateMutation = useMutation({
    mutationFn: (data: Partial<InvoiceFormData>) => invoiceService.updateInvoice(id!, data),
    onSuccess: (updatedInvoice) => {
      showSuccessToast('Invoice updated successfully!');
      queryClient.invalidateQueries({ queryKey: ['invoice', id] });
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      navigate(`/invoices/${updatedInvoice.id}`);
    },
    onError: (error: any) => {
      showErrorToast(error.response?.data?.message || 'Failed to update invoice');
    },
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  const handleItemChange = (index: number, field: keyof InvoiceItem, value: any) => {
    const newItems = [...items];
    newItems[index] = { ...newItems[index], [field]: value };

    // Recalculate amount
    if (field === 'quantity' || field === 'unit_price') {
      const quantity = field === 'quantity' ? parseFloat(value) || 0 : newItems[index].quantity || 0;
      const unitPrice = field === 'unit_price' ? parseFloat(value) || 0 : newItems[index].unit_price || 0;
      newItems[index].amount = quantity * unitPrice;
    }

    setItems(newItems);
  };

  const addItem = () => {
    setItems([...items, { description: '', quantity: 1, unit_price: 0, amount: 0 }]);
  };

  const removeItem = (index: number) => {
    if (items.length > 1) {
      setItems(items.filter((_, i) => i !== index));
    }
  };

  const calculateSubtotal = () => {
    return items.reduce((sum, item) => sum + (item.amount || 0), 0);
  };

  const calculateTax = () => {
    const subtotal = calculateSubtotal();
    const taxRate = parseFloat(formData.tax_rate as any) || 0;
    return (subtotal * taxRate) / 100;
  };

  const calculateTotal = () => {
    const subtotal = calculateSubtotal();
    const tax = calculateTax();
    const discount = parseFloat(formData.discount_amount as any) || 0;
    return subtotal + tax - discount;
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.client_id) {
      newErrors.client_id = 'Client is required';
    }

    if (!formData.issue_date) {
      newErrors.issue_date = 'Issue date is required';
    }

    if (!formData.due_date) {
      newErrors.due_date = 'Due date is required';
    }

    if (items.length === 0 || items.every(item => !item.description)) {
      newErrors.items = 'At least one line item is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    const subtotal = calculateSubtotal();
    const taxAmount = calculateTax();
    const total = calculateTotal();

    const invoiceData: Partial<InvoiceFormData> = {
      ...formData,
      items: items.filter(item => item.description),
      subtotal,
      tax_amount: taxAmount,
      total,
    };

    updateMutation.mutate(invoiceData);
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
  if (!invoice) {
    return (
      <div className="max-w-4xl mx-auto">
        <Card>
          <CardContent className="p-12 text-center">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              Invoice not found
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              The invoice you're trying to edit doesn't exist.
            </p>
            <Button variant="primary" onClick={() => navigate('/invoices')}>
              Back to Invoices
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Edit Invoice</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Update invoice information
          </p>
        </div>
        <Button variant="ghost" onClick={() => navigate(`/invoices/${id}`)}>
          Cancel
        </Button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <Card>
          <CardHeader>
            <CardTitle>Invoice Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Select
              id="client_id"
              name="client_id"
              label="Client"
              value={formData.client_id || ''}
              onChange={handleChange}
              options={[
                { value: '', label: 'Select a client...' },
                ...(clientsData?.results.map((client) => ({
                  value: client.id,
                  label:
                    client.type === 'individual'
                      ? `${client.first_name} ${client.last_name}`
                      : client.company_name || '',
                })) || []),
              ]}
              error={errors.client_id}
              fullWidth
              required
            />

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Input
                id="issue_date"
                name="issue_date"
                type="date"
                label="Issue Date"
                value={formData.issue_date || ''}
                onChange={handleChange}
                error={errors.issue_date}
                fullWidth
                required
              />

              <Input
                id="due_date"
                name="due_date"
                type="date"
                label="Due Date"
                value={formData.due_date || ''}
                onChange={handleChange}
                error={errors.due_date}
                fullWidth
                required
              />

              <Select
                id="status"
                name="status"
                label="Status"
                value={formData.status || 'draft'}
                onChange={handleChange}
                options={[
                  { value: 'draft', label: 'Draft' },
                  { value: 'sent', label: 'Sent' },
                  { value: 'viewed', label: 'Viewed' },
                  { value: 'paid', label: 'Paid' },
                  { value: 'partially_paid', label: 'Partially Paid' },
                  { value: 'overdue', label: 'Overdue' },
                  { value: 'cancelled', label: 'Cancelled' },
                ]}
                fullWidth
              />
            </div>

            <div>
              <label htmlFor="payment_terms" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Payment Terms (Optional)
              </label>
              <textarea
                id="payment_terms"
                name="payment_terms"
                rows={2}
                placeholder="e.g., Net 30 days"
                value={formData.payment_terms || ''}
                onChange={handleChange}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </CardContent>
        </Card>

        {/* Line Items */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Line Items</CardTitle>
              <Button type="button" variant="outline" size="sm" onClick={addItem}>
                <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Add Item
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {items.map((item, index) => (
                <div key={index} className="flex items-start space-x-4 pb-4 border-b border-gray-200 dark:border-gray-700 last:border-0">
                  <div className="flex-1 grid grid-cols-1 md:grid-cols-12 gap-4">
                    <div className="md:col-span-5">
                      <Input
                        label={index === 0 ? 'Description' : ''}
                        placeholder="Item description"
                        value={item.description || ''}
                        onChange={(e) => handleItemChange(index, 'description', e.target.value)}
                        fullWidth
                        required
                      />
                    </div>
                    <div className="md:col-span-2">
                      <Input
                        label={index === 0 ? 'Quantity' : ''}
                        type="number"
                        placeholder="1"
                        value={item.quantity || ''}
                        onChange={(e) => handleItemChange(index, 'quantity', e.target.value)}
                        fullWidth
                        required
                      />
                    </div>
                    <div className="md:col-span-2">
                      <Input
                        label={index === 0 ? 'Rate' : ''}
                        type="number"
                        placeholder="0.00"
                        value={item.unit_price || ''}
                        onChange={(e) => handleItemChange(index, 'unit_price', e.target.value)}
                        fullWidth
                        required
                      />
                    </div>
                    <div className="md:col-span-3">
                      <Input
                        label={index === 0 ? 'Amount' : ''}
                        type="number"
                        value={item.amount || 0}
                        readOnly
                        fullWidth
                        className="bg-gray-50 dark:bg-gray-900"
                      />
                    </div>
                  </div>
                  {items.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeItem(index)}
                      className="mt-8 p-2 text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                      title="Remove item"
                    >
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  )}
                </div>
              ))}
              {errors.items && (
                <p className="text-sm text-red-600 dark:text-red-400">{errors.items}</p>
              )}
            </div>

            {/* Totals */}
            <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
              <div className="max-w-md ml-auto space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Subtotal</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    ${calculateSubtotal().toFixed(2)}
                  </span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-gray-600 dark:text-gray-400">Tax Rate (%)</span>
                  <Input
                    type="number"
                    name="tax_rate"
                    placeholder="0"
                    value={formData.tax_rate || ''}
                    onChange={handleChange}
                    className="w-24"
                  />
                </div>

                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Tax Amount</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    ${calculateTax().toFixed(2)}
                  </span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-gray-600 dark:text-gray-400">Discount</span>
                  <Input
                    type="number"
                    name="discount_amount"
                    placeholder="0.00"
                    value={formData.discount_amount || ''}
                    onChange={handleChange}
                    className="w-24"
                  />
                </div>

                <div className="flex justify-between pt-3 border-t border-gray-200 dark:border-gray-700">
                  <span className="text-lg font-semibold text-gray-900 dark:text-white">Total</span>
                  <span className="text-lg font-bold text-gray-900 dark:text-white">
                    ${calculateTotal().toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Notes */}
        <Card>
          <CardHeader>
            <CardTitle>Additional Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <textarea
              id="notes"
              name="notes"
              rows={4}
              placeholder="Add any additional notes or terms..."
              value={formData.notes || ''}
              onChange={handleChange}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex items-center justify-end space-x-4">
          <Button
            type="button"
            variant="outline"
            size="lg"
            onClick={() => navigate(`/invoices/${id}`)}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            size="lg"
            isLoading={updateMutation.isPending}
          >
            Save Changes
          </Button>
        </div>
      </form>
    </div>
  );
};

export default InvoiceEdit;
