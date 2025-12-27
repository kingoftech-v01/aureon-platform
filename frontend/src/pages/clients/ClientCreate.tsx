/**
 * Client Create Page
 * Aureon by Rhematek Solutions
 *
 * Form to create a new client
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { clientService } from '@/services';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Select from '@/components/common/Select';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import type { ClientFormData, ClientType, LifecycleStage } from '@/types';

const ClientCreate: React.FC = () => {
  const navigate = useNavigate();
  const { success: showSuccessToast, error: showErrorToast } = useToast();

  const [clientType, setClientType] = useState<ClientType>('individual');
  const [formData, setFormData] = useState<Partial<ClientFormData>>({
    type: 'individual',
    lifecycle_stage: 'lead',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Create client mutation
  const createMutation = useMutation({
    mutationFn: (data: ClientFormData) => clientService.createClient(data),
    onSuccess: (client) => {
      showSuccessToast('Client created successfully!');
      navigate(`/clients/${client.id}`);
    },
    onError: (error: any) => {
      showErrorToast(error.response?.data?.message || 'Failed to create client');
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

  const handleClientTypeChange = (type: ClientType) => {
    setClientType(type);
    setFormData((prev) => ({ ...prev, type }));
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email address';
    }

    if (clientType === 'individual') {
      if (!formData.first_name?.trim()) {
        newErrors.first_name = 'First name is required';
      }
      if (!formData.last_name?.trim()) {
        newErrors.last_name = 'Last name is required';
      }
    } else {
      if (!formData.company_name?.trim()) {
        newErrors.company_name = 'Company name is required';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    createMutation.mutate(formData as ClientFormData);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Add New Client</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Create a new client record
          </p>
        </div>
        <Button variant="ghost" onClick={() => navigate('/clients')}>
          Cancel
        </Button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Client Type Selection */}
        <Card>
          <CardHeader>
            <CardTitle>Client Type</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => handleClientTypeChange('individual')}
                className={`p-4 border-2 rounded-lg transition-colors ${
                  clientType === 'individual'
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <div className="flex items-center justify-center mb-2">
                  <svg className="w-8 h-8 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <h3 className="font-medium text-gray-900 dark:text-white">Individual</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  A single person or freelancer
                </p>
              </button>

              <button
                type="button"
                onClick={() => handleClientTypeChange('company')}
                className={`p-4 border-2 rounded-lg transition-colors ${
                  clientType === 'company'
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <div className="flex items-center justify-center mb-2">
                  <svg className="w-8 h-8 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                </div>
                <h3 className="font-medium text-gray-900 dark:text-white">Company</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  A business or organization
                </p>
              </button>
            </div>
          </CardContent>
        </Card>

        {/* Basic Information */}
        <Card>
          <CardHeader>
            <CardTitle>Basic Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {clientType === 'individual' ? (
              <div className="grid grid-cols-2 gap-4">
                <Input
                  id="first_name"
                  name="first_name"
                  label="First Name"
                  placeholder="John"
                  value={formData.first_name || ''}
                  onChange={handleChange}
                  error={errors.first_name}
                  fullWidth
                  required
                />
                <Input
                  id="last_name"
                  name="last_name"
                  label="Last Name"
                  placeholder="Doe"
                  value={formData.last_name || ''}
                  onChange={handleChange}
                  error={errors.last_name}
                  fullWidth
                  required
                />
              </div>
            ) : (
              <div className="space-y-4">
                <Input
                  id="company_name"
                  name="company_name"
                  label="Company Name"
                  placeholder="Acme Corporation"
                  value={formData.company_name || ''}
                  onChange={handleChange}
                  error={errors.company_name}
                  fullWidth
                  required
                />
                <Input
                  id="contact_person"
                  name="contact_person"
                  label="Contact Person (Optional)"
                  placeholder="John Doe"
                  value={formData.contact_person || ''}
                  onChange={handleChange}
                  fullWidth
                />
              </div>
            )}

            <Select
              id="lifecycle_stage"
              name="lifecycle_stage"
              label="Lifecycle Stage"
              value={formData.lifecycle_stage || 'lead'}
              onChange={handleChange}
              options={[
                { value: 'lead', label: 'Lead' },
                { value: 'prospect', label: 'Prospect' },
                { value: 'customer', label: 'Customer' },
                { value: 'inactive', label: 'Inactive' },
              ]}
              fullWidth
            />
          </CardContent>
        </Card>

        {/* Contact Information */}
        <Card>
          <CardHeader>
            <CardTitle>Contact Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              id="email"
              name="email"
              type="email"
              label="Email Address"
              placeholder="client@example.com"
              value={formData.email || ''}
              onChange={handleChange}
              error={errors.email}
              fullWidth
              required
              leftIcon={
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
                </svg>
              }
            />

            <div className="grid grid-cols-2 gap-4">
              <Input
                id="phone"
                name="phone"
                type="tel"
                label="Phone Number (Optional)"
                placeholder="+1 (555) 123-4567"
                value={formData.phone || ''}
                onChange={handleChange}
                fullWidth
                leftIcon={
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                  </svg>
                }
              />

              <Input
                id="website"
                name="website"
                type="url"
                label="Website (Optional)"
                placeholder="https://example.com"
                value={formData.website || ''}
                onChange={handleChange}
                fullWidth
                leftIcon={
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                  </svg>
                }
              />
            </div>
          </CardContent>
        </Card>

        {/* Address */}
        <Card>
          <CardHeader>
            <CardTitle>Address (Optional)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              id="address"
              name="address"
              label="Street Address"
              placeholder="123 Main St"
              value={formData.address || ''}
              onChange={handleChange}
              fullWidth
            />

            <div className="grid grid-cols-2 gap-4">
              <Input
                id="city"
                name="city"
                label="City"
                placeholder="New York"
                value={formData.city || ''}
                onChange={handleChange}
                fullWidth
              />

              <Input
                id="state"
                name="state"
                label="State/Province"
                placeholder="NY"
                value={formData.state || ''}
                onChange={handleChange}
                fullWidth
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <Input
                id="postal_code"
                name="postal_code"
                label="Postal Code"
                placeholder="10001"
                value={formData.postal_code || ''}
                onChange={handleChange}
                fullWidth
              />

              <Input
                id="country"
                name="country"
                label="Country"
                placeholder="United States"
                value={formData.country || ''}
                onChange={handleChange}
                fullWidth
              />
            </div>
          </CardContent>
        </Card>

        {/* Notes */}
        <Card>
          <CardHeader>
            <CardTitle>Notes (Optional)</CardTitle>
          </CardHeader>
          <CardContent>
            <textarea
              id="notes"
              name="notes"
              rows={4}
              placeholder="Add any additional notes about this client..."
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
            onClick={() => navigate('/clients')}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            size="lg"
            isLoading={createMutation.isPending}
          >
            Create Client
          </Button>
        </div>
      </form>
    </div>
  );
};

export default ClientCreate;
