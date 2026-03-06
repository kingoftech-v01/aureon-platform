/**
 * Recurring Invoices Page
 * Aureon by Rhematek Solutions
 *
 * Manage recurring invoice templates with create, toggle, edit, and delete actions
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { invoiceService, clientService } from '@/services';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Select from '@/components/common/Select';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Table, { TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '@/components/common/Table';
import Badge from '@/components/common/Badge';
import Modal, { ModalHeader, ModalBody, ModalFooter } from '@/components/common/Modal';
import { SkeletonTable } from '@/components/common/Skeleton';
import type { RecurringInvoice, RecurrenceFrequency, Client } from '@/types';

interface RecurringInvoiceForm {
  client_id: string;
  description: string;
  amount: number;
  frequency: RecurrenceFrequency | '';
  start_date: string;
  end_date: string;
}

const initialFormState: RecurringInvoiceForm = {
  client_id: '',
  description: '',
  amount: 0,
  frequency: '',
  start_date: '',
  end_date: '',
};

const RecurringInvoices: React.FC = () => {
  const queryClient = useQueryClient();
  const { success: showSuccess, error: showError } = useToast();

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingInvoice, setEditingInvoice] = useState<RecurringInvoice | null>(null);
  const [formData, setFormData] = useState<RecurringInvoiceForm>(initialFormState);

  // Fetch recurring invoices
  const { data: recurringInvoices, isLoading, error } = useQuery({
    queryKey: ['recurring-invoices'],
    queryFn: () => invoiceService.getRecurringInvoices(),
  });

  // Fetch clients for the selector
  const { data: clientsData } = useQuery({
    queryKey: ['clients', { page: 1, pageSize: 100 }],
    queryFn: () => clientService.getClients({ page: 1, pageSize: 100 }),
  });

  // Handle errors
  React.useEffect(() => {
    if (error) {
      showError('Failed to load recurring invoices');
    }
  }, [error, showError]);

  // Create recurring invoice mutation
  const createMutation = useMutation({
    mutationFn: (data: Partial<RecurringInvoice>) => invoiceService.createRecurringInvoice(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recurring-invoices'] });
      showSuccess('Recurring invoice created successfully');
      handleCloseModal();
    },
    onError: () => {
      showError('Failed to create recurring invoice');
    },
  });

  // Update recurring invoice mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<RecurringInvoice> }) =>
      invoiceService.updateRecurringInvoice(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recurring-invoices'] });
      showSuccess('Recurring invoice updated successfully');
      handleCloseModal();
    },
    onError: () => {
      showError('Failed to update recurring invoice');
    },
  });

  // Pause mutation
  const pauseMutation = useMutation({
    mutationFn: (id: string) => invoiceService.pauseRecurringInvoice(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recurring-invoices'] });
      showSuccess('Recurring invoice paused');
    },
    onError: () => {
      showError('Failed to pause recurring invoice');
    },
  });

  // Resume mutation
  const resumeMutation = useMutation({
    mutationFn: (id: string) => invoiceService.resumeRecurringInvoice(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recurring-invoices'] });
      showSuccess('Recurring invoice resumed');
    },
    onError: () => {
      showError('Failed to resume recurring invoice');
    },
  });

  // Cancel mutation
  const cancelMutation = useMutation({
    mutationFn: (id: string) => invoiceService.cancelRecurringInvoice(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recurring-invoices'] });
      showSuccess('Recurring invoice cancelled');
    },
    onError: () => {
      showError('Failed to cancel recurring invoice');
    },
  });

  // Get client display name
  const getClientName = (client: Client) => {
    if (client.type === 'individual') {
      return `${client.first_name} ${client.last_name}`;
    }
    return client.company_name || '';
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
      month: 'short',
      day: 'numeric',
    });
  };

  // Get status info
  const getStatusBadge = (invoice: RecurringInvoice) => {
    if (invoice.is_active) {
      return <Badge variant="success">Active</Badge>;
    }
    return <Badge variant="default">Paused</Badge>;
  };

  // Frequency display
  const getFrequencyLabel = (frequency: RecurrenceFrequency) => {
    const labels: Record<RecurrenceFrequency, string> = {
      weekly: 'Weekly',
      biweekly: 'Bi-Weekly',
      monthly: 'Monthly',
      quarterly: 'Quarterly',
      annually: 'Annually',
    };
    return labels[frequency] || frequency;
  };

  // Handle toggle active/pause
  const handleToggle = (invoice: RecurringInvoice) => {
    if (invoice.is_active) {
      pauseMutation.mutate(invoice.id);
    } else {
      resumeMutation.mutate(invoice.id);
    }
  };

  // Open create modal
  const handleOpenCreate = () => {
    setFormData(initialFormState);
    setEditingInvoice(null);
    setShowCreateModal(true);
  };

  // Open edit modal
  const handleOpenEdit = (invoice: RecurringInvoice) => {
    setEditingInvoice(invoice);
    setFormData({
      client_id: invoice.client.id,
      description: invoice.template_invoice?.notes || '',
      amount: invoice.template_invoice?.total || 0,
      frequency: invoice.frequency,
      start_date: invoice.start_date,
      end_date: invoice.end_date || '',
    });
    setShowCreateModal(true);
  };

  // Close modal
  const handleCloseModal = () => {
    setShowCreateModal(false);
    setEditingInvoice(null);
    setFormData(initialFormState);
  };

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.client_id || !formData.frequency || !formData.start_date) {
      showError('Please fill in all required fields');
      return;
    }

    const payload: Partial<RecurringInvoice> = {
      client: { id: formData.client_id } as Client,
      frequency: formData.frequency as RecurrenceFrequency,
      start_date: formData.start_date,
      end_date: formData.end_date || undefined,
      is_active: true,
    };

    if (editingInvoice) {
      updateMutation.mutate({ id: editingInvoice.id, data: payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  // Handle form field change
  const handleFieldChange = (field: keyof RecurringInvoiceForm, value: string | number) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Recurring Invoices</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Manage automated recurring billing templates
          </p>
        </div>
        <Button variant="primary" size="lg" onClick={handleOpenCreate}>
          <svg
            className="w-5 h-5 mr-2"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 6v6m0 0v6m0-6h6m-6 0H6"
            />
          </svg>
          Create Recurring
        </Button>
      </div>

      {/* Recurring Invoices Table */}
      <Card>
        <CardHeader>
          <CardTitle>
            {recurringInvoices
              ? `${recurringInvoices.length} Recurring Invoice${recurringInvoices.length !== 1 ? 's' : ''}`
              : 'Recurring Invoices'}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6">
              <SkeletonTable rows={5} columns={7} />
            </div>
          ) : recurringInvoices && recurringInvoices.length > 0 ? (
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeaderCell>Client</TableHeaderCell>
                  <TableHeaderCell>Description</TableHeaderCell>
                  <TableHeaderCell align="right">Amount</TableHeaderCell>
                  <TableHeaderCell>Frequency</TableHeaderCell>
                  <TableHeaderCell>Next Generate Date</TableHeaderCell>
                  <TableHeaderCell>Status</TableHeaderCell>
                  <TableHeaderCell align="right">Actions</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {recurringInvoices.map((invoice: RecurringInvoice) => (
                  <TableRow key={invoice.id} hoverable>
                    <TableCell>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {getClientName(invoice.client)}
                      </p>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {invoice.template_invoice?.notes || 'Recurring billing'}
                      </span>
                    </TableCell>
                    <TableCell align="right">
                      <span className="font-medium text-gray-900 dark:text-white">
                        {formatCurrency(invoice.template_invoice?.total || 0)}
                      </span>
                    </TableCell>
                    <TableCell>
                      <Badge variant="info">{getFrequencyLabel(invoice.frequency)}</Badge>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {formatDate(invoice.next_invoice_date)}
                      </span>
                    </TableCell>
                    <TableCell>{getStatusBadge(invoice)}</TableCell>
                    <TableCell align="right">
                      <div className="flex items-center justify-end space-x-2">
                        {/* Toggle Active/Pause */}
                        <button
                          onClick={() => handleToggle(invoice)}
                          className={`p-1 transition-colors ${
                            invoice.is_active
                              ? 'text-yellow-500 hover:text-yellow-600'
                              : 'text-green-500 hover:text-green-600'
                          }`}
                          title={invoice.is_active ? 'Pause' : 'Resume'}
                          disabled={pauseMutation.isPending || resumeMutation.isPending}
                        >
                          {invoice.is_active ? (
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          ) : (
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          )}
                        </button>

                        {/* Edit */}
                        <button
                          onClick={() => handleOpenEdit(invoice)}
                          className="p-1 text-gray-400 hover:text-primary-500 transition-colors"
                          title="Edit"
                        >
                          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                            />
                          </svg>
                        </button>

                        {/* Delete / Cancel */}
                        <button
                          onClick={() => cancelMutation.mutate(invoice.id)}
                          className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                          title="Cancel recurring invoice"
                          disabled={cancelMutation.isPending}
                        >
                          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                            />
                          </svg>
                        </button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-8 h-8 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No recurring invoices
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Set up automated billing by creating your first recurring invoice
              </p>
              <Button variant="primary" onClick={handleOpenCreate}>
                Create Recurring Invoice
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create / Edit Modal */}
      <Modal isOpen={showCreateModal} onClose={handleCloseModal} size="lg">
        <ModalHeader>
          {editingInvoice ? 'Edit Recurring Invoice' : 'Create Recurring Invoice'}
        </ModalHeader>
        <form onSubmit={handleSubmit}>
          <ModalBody>
            <div className="space-y-4">
              {/* Client Selector */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Client <span className="text-red-500">*</span>
                </label>
                <Select
                  value={formData.client_id}
                  onChange={(e) => handleFieldChange('client_id', e.target.value)}
                  options={[
                    { value: '', label: 'Select a client' },
                    ...(clientsData?.results || []).map((client: Client) => ({
                      value: client.id,
                      label:
                        client.type === 'individual'
                          ? `${client.first_name} ${client.last_name}`
                          : client.company_name || '',
                    })),
                  ]}
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Description
                </label>
                <Input
                  type="text"
                  placeholder="Monthly retainer, subscription, etc."
                  value={formData.description}
                  onChange={(e) => handleFieldChange('description', e.target.value)}
                />
              </div>

              {/* Amount */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Amount
                </label>
                <Input
                  type="number"
                  placeholder="0.00"
                  value={formData.amount || ''}
                  onChange={(e) => handleFieldChange('amount', parseFloat(e.target.value) || 0)}
                  leftIcon={<span className="text-gray-500">$</span>}
                />
              </div>

              {/* Frequency */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Frequency <span className="text-red-500">*</span>
                </label>
                <Select
                  value={formData.frequency}
                  onChange={(e) => handleFieldChange('frequency', e.target.value)}
                  options={[
                    { value: '', label: 'Select frequency' },
                    { value: 'weekly', label: 'Weekly' },
                    { value: 'biweekly', label: 'Bi-Weekly' },
                    { value: 'monthly', label: 'Monthly' },
                    { value: 'quarterly', label: 'Quarterly' },
                    { value: 'annually', label: 'Annually' },
                  ]}
                />
              </div>

              {/* Start Date */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Start Date <span className="text-red-500">*</span>
                </label>
                <Input
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => handleFieldChange('start_date', e.target.value)}
                />
              </div>

              {/* End Date (optional) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  End Date <span className="text-gray-400">(optional)</span>
                </label>
                <Input
                  type="date"
                  value={formData.end_date}
                  onChange={(e) => handleFieldChange('end_date', e.target.value)}
                />
              </div>
            </div>
          </ModalBody>
          <ModalFooter>
            <Button variant="outline" onClick={handleCloseModal} type="button">
              Cancel
            </Button>
            <Button
              variant="primary"
              type="submit"
              disabled={createMutation.isPending || updateMutation.isPending}
            >
              {createMutation.isPending || updateMutation.isPending
                ? 'Saving...'
                : editingInvoice
                ? 'Update'
                : 'Create'}
            </Button>
          </ModalFooter>
        </form>
      </Modal>
    </div>
  );
};

export default RecurringInvoices;
