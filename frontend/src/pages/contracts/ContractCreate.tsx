/**
 * Contract Create Page
 * Aureon by Rhematek Solutions
 *
 * Form to create a new contract
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { contractService, clientService } from '@/services';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Select from '@/components/common/Select';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import type { ContractFormData, ContractStatus } from '@/types';

const ContractCreate: React.FC = () => {
  const navigate = useNavigate();
  const { success: showSuccessToast, error: showErrorToast } = useToast();

  const [formData, setFormData] = useState<Partial<ContractFormData>>({
    status: 'draft',
    currency: 'USD',
    total_value: 0,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Fetch clients for dropdown
  const { data: clientsData } = useQuery({
    queryKey: ['clients', { page: 1, pageSize: 100 }],
    queryFn: () => clientService.getClients({ page: 1, pageSize: 100 }),
  });

  // Create contract mutation
  const createMutation = useMutation({
    mutationFn: (data: ContractFormData) => contractService.createContract(data),
    onSuccess: (contract) => {
      showSuccessToast('Contract created successfully!');
      navigate(`/contracts/${contract.id}`);
    },
    onError: (error: any) => {
      showErrorToast(error.response?.data?.message || 'Failed to create contract');
    },
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear field error
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.client_id) {
      newErrors.client_id = 'Client is required';
    }

    if (!formData.title?.trim()) {
      newErrors.title = 'Title is required';
    }

    if (!formData.total_value || formData.total_value < 0) {
      newErrors.total_value = 'Total value must be a positive number';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    createMutation.mutate(formData as ContractFormData);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Create New Contract</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Create a new contract for a client
          </p>
        </div>
        <Button variant="ghost" onClick={() => navigate('/contracts')}>
          Cancel
        </Button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <Card>
          <CardHeader>
            <CardTitle>Basic Information</CardTitle>
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

            <Input
              id="title"
              name="title"
              label="Contract Title"
              placeholder="e.g., Website Development Agreement"
              value={formData.title || ''}
              onChange={handleChange}
              error={errors.title}
              fullWidth
              required
            />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                id="total_value"
                name="total_value"
                type="number"
                label="Total Value"
                placeholder="0.00"
                value={formData.total_value || ''}
                onChange={handleChange}
                error={errors.total_value}
                fullWidth
                required
                leftIcon={
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                }
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
                  { value: 'signed', label: 'Signed' },
                  { value: 'active', label: 'Active' },
                  { value: 'completed', label: 'Completed' },
                ]}
                fullWidth
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                id="start_date"
                name="start_date"
                type="date"
                label="Start Date (Optional)"
                value={formData.start_date || ''}
                onChange={handleChange}
                fullWidth
              />

              <Input
                id="end_date"
                name="end_date"
                type="date"
                label="End Date (Optional)"
                value={formData.end_date || ''}
                onChange={handleChange}
                fullWidth
              />
            </div>

            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Description (Optional)
              </label>
              <textarea
                id="description"
                name="description"
                rows={3}
                placeholder="Brief description of the contract..."
                value={formData.description || ''}
                onChange={handleChange}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </CardContent>
        </Card>

        {/* Contract Content */}
        <Card>
          <CardHeader>
            <CardTitle>Contract Content</CardTitle>
          </CardHeader>
          <CardContent>
            <div>
              <label htmlFor="content" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Contract Terms and Conditions
              </label>
              <textarea
                id="content"
                name="content"
                rows={12}
                placeholder="Enter the full contract text here..."
                value={formData.content || ''}
                onChange={handleChange}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 font-mono text-sm"
              />
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                You can use templates or enter custom contract text
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Milestones */}
        <Card>
          <CardHeader>
            <CardTitle>Milestones (Optional)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8">
              <svg className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <p className="text-gray-500 dark:text-gray-400 mb-2">
                Add milestones after creating the contract
              </p>
              <p className="text-sm text-gray-400 dark:text-gray-500">
                You can define payment milestones and deliverables in the contract detail page
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex items-center justify-end space-x-4">
          <Button
            type="button"
            variant="outline"
            size="lg"
            onClick={() => navigate('/contracts')}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            size="lg"
            isLoading={createMutation.isPending}
          >
            Create Contract
          </Button>
        </div>
      </form>
    </div>
  );
};

export default ContractCreate;
