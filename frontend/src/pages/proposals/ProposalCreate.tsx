/**
 * Proposal Create/Edit Page
 * Aureon by Rhematek Solutions
 *
 * Full proposal creation form with client selector, line items,
 * terms, and save/send actions.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import apiClient from '@/services/api';
import { clientService } from '@/services';

interface LineItem {
  id: string;
  description: string;
  quantity: number;
  rate: number;
  amount: number;
}

interface Client {
  id: string;
  type: string;
  first_name?: string;
  last_name?: string;
  company_name?: string;
  email?: string;
}

interface ProposalFormData {
  client_id: string;
  title: string;
  description: string;
  line_items: Omit<LineItem, 'id'>[];
  terms_and_conditions: string;
  validity_days: number;
  tax_rate: number;
  notes: string;
}

const generateTempId = () => Math.random().toString(36).substring(2, 9);

const ProposalCreate: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEditing = !!id;
  const { success: showSuccess, error: showError } = useToast();

  // Client search state
  const [clientSearch, setClientSearch] = useState('');
  const [showClientDropdown, setShowClientDropdown] = useState(false);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);

  // Form state
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [lineItems, setLineItems] = useState<LineItem[]>([
    { id: generateTempId(), description: '', quantity: 1, rate: 0, amount: 0 },
  ]);
  const [termsAndConditions, setTermsAndConditions] = useState(
    'Payment terms: Net 30 days from the date of invoice.\nAll prices are in USD unless otherwise specified.\nThis proposal is valid for the period specified above.'
  );
  const [validityDays, setValidityDays] = useState(30);
  const [taxRate, setTaxRate] = useState(0);
  const [notes, setNotes] = useState('');

  // Search clients
  const { data: clientResults } = useQuery<Client[]>({
    queryKey: ['client-search', clientSearch],
    queryFn: () => clientService.searchClients(clientSearch),
    enabled: clientSearch.length >= 2,
  });

  // Load existing proposal for editing
  const { data: existingProposal, isLoading: loadingProposal } = useQuery({
    queryKey: ['proposal', id],
    queryFn: async () => {
      const response = await apiClient.get(`/contracts/proposals/${id}/`);
      return response.data;
    },
    enabled: isEditing,
  });

  // Populate form when editing
  useEffect(() => {
    if (existingProposal) {
      setTitle(existingProposal.title || '');
      setDescription(existingProposal.description || '');
      setTermsAndConditions(existingProposal.terms_and_conditions || '');
      setValidityDays(existingProposal.validity_days || 30);
      setTaxRate(existingProposal.tax_rate || 0);
      setNotes(existingProposal.notes || '');
      if (existingProposal.client) {
        setSelectedClient(existingProposal.client);
      }
      if (existingProposal.line_items && existingProposal.line_items.length > 0) {
        setLineItems(
          existingProposal.line_items.map((item: any) => ({
            id: item.id || generateTempId(),
            description: item.description,
            quantity: item.quantity,
            rate: item.rate,
            amount: item.quantity * item.rate,
          }))
        );
      }
    }
  }, [existingProposal]);

  // Create proposal mutation
  const createMutation = useMutation({
    mutationFn: async (data: ProposalFormData & { send?: boolean }) => {
      const { send, ...payload } = data;
      if (isEditing) {
        const response = await apiClient.put(`/contracts/proposals/${id}/`, payload);
        if (send) await apiClient.post(`/contracts/proposals/${id}/send/`);
        return response.data;
      } else {
        const response = await apiClient.post('/contracts/proposals/', payload);
        if (send) await apiClient.post(`/contracts/proposals/${response.data.id}/send/`);
        return response.data;
      }
    },
    onSuccess: (_, variables) => {
      showSuccess(variables.send ? 'Proposal sent to client' : 'Proposal saved as draft');
      navigate('/proposals');
    },
    onError: () => {
      showError('Failed to save proposal');
    },
  });

  // Update line item
  const updateLineItem = useCallback((itemId: string, field: keyof LineItem, value: string | number) => {
    setLineItems((prev) =>
      prev.map((item) => {
        if (item.id !== itemId) return item;
        const updated = { ...item, [field]: value };
        if (field === 'quantity' || field === 'rate') {
          updated.amount = Number(updated.quantity) * Number(updated.rate);
        }
        return updated;
      })
    );
  }, []);

  // Add line item
  const addLineItem = () => {
    setLineItems((prev) => [
      ...prev,
      { id: generateTempId(), description: '', quantity: 1, rate: 0, amount: 0 },
    ]);
  };

  // Remove line item
  const removeLineItem = (itemId: string) => {
    if (lineItems.length === 1) {
      showError('At least one line item is required');
      return;
    }
    setLineItems((prev) => prev.filter((item) => item.id !== itemId));
  };

  // Calculate totals
  const subtotal = lineItems.reduce((sum, item) => sum + item.amount, 0);
  const taxAmount = subtotal * (taxRate / 100);
  const total = subtotal + taxAmount;

  // Format currency
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
  };

  // Client name helper
  const getClientName = (client: Client) => {
    if (client.type === 'individual') {
      return `${client.first_name || ''} ${client.last_name || ''}`.trim();
    }
    return client.company_name || 'Unknown';
  };

  // Validate & submit
  const handleSubmit = (send: boolean) => {
    if (!selectedClient) {
      showError('Please select a client');
      return;
    }
    if (!title.trim()) {
      showError('Please enter a proposal title');
      return;
    }
    if (lineItems.some((item) => !item.description.trim())) {
      showError('Please fill in all line item descriptions');
      return;
    }
    if (lineItems.some((item) => item.rate <= 0)) {
      showError('All line items must have a positive rate');
      return;
    }

    createMutation.mutate({
      client_id: selectedClient.id,
      title,
      description,
      line_items: lineItems.map(({ description, quantity, rate, amount }) => ({
        description,
        quantity,
        rate,
        amount,
      })),
      terms_and_conditions: termsAndConditions,
      validity_days: validityDays,
      tax_rate: taxRate,
      notes,
      send,
    });
  };

  if (isEditing && loadingProposal) {
    return (
      <div className="flex items-center justify-center h-96">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            {isEditing ? 'Edit Proposal' : 'Create Proposal'}
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            {isEditing ? 'Update your proposal details' : 'Build a new proposal for your client'}
          </p>
        </div>
        <Button variant="ghost" onClick={() => navigate('/proposals')}>
          <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back
        </Button>
      </div>

      {/* Client Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Client</CardTitle>
        </CardHeader>
        <CardContent>
          {selectedClient ? (
            <div className="flex items-center justify-between p-4 bg-primary-50 dark:bg-primary-900/10 rounded-lg border border-primary-200 dark:border-primary-800">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-primary-500 rounded-full flex items-center justify-center text-white font-semibold">
                  {getClientName(selectedClient)[0]}
                </div>
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">{getClientName(selectedClient)}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{selectedClient.email}</p>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setSelectedClient(null)}>
                Change
              </Button>
            </div>
          ) : (
            <div className="relative">
              <Input
                placeholder="Search for a client by name or email..."
                value={clientSearch}
                onChange={(e) => {
                  setClientSearch(e.target.value);
                  setShowClientDropdown(true);
                }}
                onFocus={() => setShowClientDropdown(true)}
                fullWidth
                leftIcon={
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                }
              />
              {showClientDropdown && clientResults && clientResults.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                  {clientResults.map((client) => (
                    <button
                      key={client.id}
                      onClick={() => {
                        setSelectedClient(client);
                        setShowClientDropdown(false);
                        setClientSearch('');
                      }}
                      className="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex items-center space-x-3"
                    >
                      <div className="w-8 h-8 bg-gray-200 dark:bg-gray-600 rounded-full flex items-center justify-center text-sm font-medium text-gray-700 dark:text-gray-300">
                        {getClientName(client)[0]}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-white">{getClientName(client)}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">{client.email}</p>
                      </div>
                    </button>
                  ))}
                </div>
              )}
              {showClientDropdown && clientSearch.length >= 2 && (!clientResults || clientResults.length === 0) && (
                <div className="absolute z-10 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-4 text-center">
                  <p className="text-sm text-gray-500 dark:text-gray-400">No clients found</p>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Proposal Details */}
      <Card>
        <CardHeader>
          <CardTitle>Proposal Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            label="Proposal Title"
            placeholder="e.g., Website Development Proposal"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            fullWidth
            required
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              placeholder="Provide a summary of the proposal..."
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-3 text-gray-900 dark:text-white placeholder-gray-400 focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:outline-none transition-colors resize-none"
            />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Validity Period (days)"
              type="number"
              value={String(validityDays)}
              onChange={(e) => setValidityDays(parseInt(e.target.value) || 0)}
              fullWidth
              min={1}
            />
            <Input
              label="Tax Rate (%)"
              type="number"
              value={String(taxRate)}
              onChange={(e) => setTaxRate(parseFloat(e.target.value) || 0)}
              fullWidth
              min={0}
              step={0.01}
            />
          </div>
        </CardContent>
      </Card>

      {/* Line Items */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <CardTitle>Line Items</CardTitle>
            <Button variant="outline" size="sm" onClick={addLineItem}>
              <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Add Item
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Header */}
            <div className="hidden md:grid md:grid-cols-12 gap-3 text-sm font-medium text-gray-500 dark:text-gray-400 px-1">
              <div className="col-span-5">Description</div>
              <div className="col-span-2 text-right">Quantity</div>
              <div className="col-span-2 text-right">Rate</div>
              <div className="col-span-2 text-right">Amount</div>
              <div className="col-span-1"></div>
            </div>

            {/* Items */}
            {lineItems.map((item, index) => (
              <div key={item.id} className="grid grid-cols-1 md:grid-cols-12 gap-3 items-start p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                <div className="md:col-span-5">
                  <label className="md:hidden text-xs text-gray-500 dark:text-gray-400 mb-1 block">
                    Description
                  </label>
                  <input
                    type="text"
                    placeholder={`Item ${index + 1} description`}
                    value={item.description}
                    onChange={(e) => updateLineItem(item.id, 'description', e.target.value)}
                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="md:hidden text-xs text-gray-500 dark:text-gray-400 mb-1 block">
                    Quantity
                  </label>
                  <input
                    type="number"
                    min={1}
                    value={item.quantity}
                    onChange={(e) => updateLineItem(item.id, 'quantity', parseInt(e.target.value) || 0)}
                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-right text-gray-900 dark:text-white focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="md:hidden text-xs text-gray-500 dark:text-gray-400 mb-1 block">
                    Rate ($)
                  </label>
                  <input
                    type="number"
                    min={0}
                    step={0.01}
                    value={item.rate}
                    onChange={(e) => updateLineItem(item.id, 'rate', parseFloat(e.target.value) || 0)}
                    className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-right text-gray-900 dark:text-white focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none"
                  />
                </div>
                <div className="md:col-span-2 flex items-center justify-end">
                  <label className="md:hidden text-xs text-gray-500 dark:text-gray-400 mr-2">
                    Amount:
                  </label>
                  <span className="text-sm font-semibold text-gray-900 dark:text-white py-2">
                    {formatCurrency(item.amount)}
                  </span>
                </div>
                <div className="md:col-span-1 flex items-center justify-center">
                  <button
                    onClick={() => removeLineItem(item.id)}
                    className="p-1.5 text-gray-400 hover:text-red-500 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                    title="Remove item"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}

            {/* Totals */}
            <div className="border-t border-gray-200 dark:border-gray-700 pt-4 mt-4">
              <div className="flex flex-col items-end space-y-2">
                <div className="flex items-center justify-between w-64">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Subtotal</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">{formatCurrency(subtotal)}</span>
                </div>
                {taxRate > 0 && (
                  <div className="flex items-center justify-between w-64">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Tax ({taxRate}%)</span>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">{formatCurrency(taxAmount)}</span>
                  </div>
                )}
                <div className="flex items-center justify-between w-64 pt-2 border-t border-gray-200 dark:border-gray-700">
                  <span className="text-base font-semibold text-gray-900 dark:text-white">Total</span>
                  <span className="text-lg font-bold text-primary-600 dark:text-primary-400">{formatCurrency(total)}</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Terms & Notes */}
      <Card>
        <CardHeader>
          <CardTitle>Terms & Conditions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Terms & Conditions
            </label>
            <textarea
              value={termsAndConditions}
              onChange={(e) => setTermsAndConditions(e.target.value)}
              rows={5}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-3 text-gray-900 dark:text-white placeholder-gray-400 focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:outline-none transition-colors resize-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Additional Notes (optional)
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              placeholder="Any additional notes for the client..."
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-3 text-gray-900 dark:text-white placeholder-gray-400 focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:outline-none transition-colors resize-none"
            />
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex items-center justify-between py-4">
        <Button variant="ghost" onClick={() => navigate('/proposals')}>
          Cancel
        </Button>
        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            onClick={() => handleSubmit(false)}
            isLoading={createMutation.isPending}
          >
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
            </svg>
            Save as Draft
          </Button>
          <Button
            variant="primary"
            onClick={() => handleSubmit(true)}
            isLoading={createMutation.isPending}
          >
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
            Send to Client
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ProposalCreate;
