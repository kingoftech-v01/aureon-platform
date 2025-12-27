/**
 * Contract Edit Page
 * Aureon by Rhematek Solutions
 *
 * Form to edit an existing contract
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { contractService, clientService } from '@/services';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Select from '@/components/common/Select';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import { SkeletonCard } from '@/components/common/Skeleton';
import type { ContractFormData } from '@/types';

const ContractEdit: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success: showSuccessToast, error: showErrorToast } = useToast();

  const [formData, setFormData] = useState<Partial<ContractFormData>>({
    status: 'draft',
    currency: 'USD',
    total_value: 0,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Fetch existing contract data
  const { data: contract, isLoading } = useQuery({
    queryKey: ['contract', id],
    queryFn: () => contractService.getContract(id!),
    enabled: !!id,
  });

  // Fetch clients for dropdown
  const { data: clientsData } = useQuery({
    queryKey: ['clients', { page: 1, pageSize: 100 }],
    queryFn: () => clientService.getClients({ page: 1, pageSize: 100 }),
  });

  // Populate form when contract data is loaded
  useEffect(() => {
    if (contract) {
      setFormData({
        client_id: contract.client.id,
        title: contract.title,
        description: contract.description || '',
        content: contract.content || '',
        status: contract.status,
        start_date: contract.start_date || '',
        end_date: contract.end_date || '',
        total_value: contract.total_value,
        currency: contract.currency,
      });
    }
  }, [contract]);

  // Update contract mutation
  const updateMutation = useMutation({
    mutationFn: (data: Partial<ContractFormData>) => contractService.updateContract(id!, data),
    onSuccess: (updatedContract) => {
      showSuccessToast('Contract updated successfully!');
      queryClient.invalidateQueries({ queryKey: ['contract', id] });
      queryClient.invalidateQueries({ queryKey: ['contracts'] });
      navigate(`/contracts/${updatedContract.id}`);
    },
    onError: (error: any) => {
      showErrorToast(error.response?.data?.message || 'Failed to update contract');
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

    updateMutation.mutate(formData);
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
  if (!contract) {
    return (
      <div className="max-w-4xl mx-auto">
        <Card>
          <CardContent className="p-12 text-center">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              Contract not found
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              The contract you're trying to edit doesn't exist.
            </p>
            <Button variant="primary" onClick={() => navigate('/contracts')}>
              Back to Contracts
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Edit Contract</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Update contract information
          </p>
        </div>
        <Button variant="ghost" onClick={() => navigate(`/contracts/${id}`)}>
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
                  { value: 'terminated', label: 'Terminated' },
                  { value: 'expired', label: 'Expired' },
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
            </div>
          </CardContent>
        </Card>

        {/* Milestones Note */}
        <Card>
          <CardHeader>
            <CardTitle>Milestones</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <div className="flex">
                <svg className="w-5 h-5 text-blue-600 dark:text-blue-400 mr-3 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <h4 className="text-sm font-medium text-blue-900 dark:text-blue-200 mb-1">
                    Manage Milestones
                  </h4>
                  <p className="text-sm text-blue-700 dark:text-blue-300">
                    You can add, edit, and complete milestones from the contract detail page after saving your changes.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex items-center justify-end space-x-4">
          <Button
            type="button"
            variant="outline"
            size="lg"
            onClick={() => navigate(`/contracts/${id}`)}
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

export default ContractEdit;
