/**
 * Webhook Management Page
 * Aureon by Rhematek Solutions
 *
 * Manage webhook endpoints and view event delivery history
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { webhookService } from '@/services';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Select from '@/components/common/Select';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Table, { TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '@/components/common/Table';
import Badge from '@/components/common/Badge';
import Modal, { ModalHeader, ModalBody, ModalFooter } from '@/components/common/Modal';
import { SkeletonTable } from '@/components/common/Skeleton';
import type { Webhook, PaginationConfig } from '@/types';

// Available webhook event types for the multi-select
const AVAILABLE_EVENT_TYPES = [
  { value: 'invoice_created', label: 'Invoice Created' },
  { value: 'invoice_paid', label: 'Invoice Paid' },
  { value: 'payment_received', label: 'Payment Received' },
  { value: 'payment_failed', label: 'Payment Failed' },
  { value: 'contract_signed', label: 'Contract Signed' },
  { value: 'contract_completed', label: 'Contract Completed' },
  { value: 'client_created', label: 'Client Created' },
  { value: 'milestone_completed', label: 'Milestone Completed' },
  { value: 'payment_refunded', label: 'Payment Refunded' },
];

// Retry policy options
const RETRY_OPTIONS = [
  { value: '3', label: '3 retries' },
  { value: '5', label: '5 retries' },
  { value: '10', label: '10 retries' },
  { value: '0', label: 'No retries' },
];

interface EndpointFormData {
  url: string;
  events: string[];
  description: string;
  secret: string;
  is_active: boolean;
  max_retries: string;
}

const initialFormData: EndpointFormData = {
  url: '',
  events: [],
  description: '',
  secret: '',
  is_active: true,
  max_retries: '3',
};

const WebhookManagement: React.FC = () => {
  const queryClient = useQueryClient();
  const { success: showSuccessToast, error: showErrorToast } = useToast();

  // State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingWebhook, setEditingWebhook] = useState<Webhook | null>(null);
  const [formData, setFormData] = useState<EndpointFormData>(initialFormData);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [expandedEventId, setExpandedEventId] = useState<string | null>(null);
  const [eventTypeFilter, setEventTypeFilter] = useState('');
  const [eventStatusFilter, setEventStatusFilter] = useState('');
  const [pagination] = useState<PaginationConfig>({ page: 1, page_size: 10, pageSize: 10 });

  // Fetch webhook endpoints
  const { data: webhooksData, isLoading: isLoadingWebhooks } = useQuery({
    queryKey: ['webhooks', pagination],
    queryFn: () => webhookService.getWebhooks(pagination),
  });

  // Fetch recent deliveries (across all webhooks)
  const { data: deliveriesData, isLoading: isLoadingDeliveries } = useQuery({
    queryKey: ['webhook-deliveries', eventTypeFilter, eventStatusFilter],
    queryFn: () =>
      webhookService.getAllDeliveries(
        { page: 1, page_size: 20, pageSize: 20 },
        {
          event_type: eventTypeFilter || undefined,
          status: (eventStatusFilter as 'success' | 'failed' | 'pending') || undefined,
        }
      ),
  });

  // Create webhook mutation
  const createMutation = useMutation({
    mutationFn: (data: { url: string; events: string[]; description?: string; secret?: string; is_active?: boolean }) =>
      webhookService.createWebhook(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhooks'] });
      showSuccessToast('Webhook endpoint created successfully');
      handleCloseModal();
    },
    onError: () => {
      showErrorToast('Failed to create webhook endpoint');
    },
  });

  // Update webhook mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: { url?: string; events?: string[]; description?: string; is_active?: boolean } }) =>
      webhookService.updateWebhook(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhooks'] });
      showSuccessToast('Webhook endpoint updated successfully');
      handleCloseModal();
    },
    onError: () => {
      showErrorToast('Failed to update webhook endpoint');
    },
  });

  // Delete webhook mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => webhookService.deleteWebhook(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhooks'] });
      showSuccessToast('Webhook endpoint deleted');
      setDeleteConfirmId(null);
    },
    onError: () => {
      showErrorToast('Failed to delete webhook endpoint');
    },
  });

  // Test webhook mutation
  const testMutation = useMutation({
    mutationFn: (id: string) => webhookService.testWebhook(id),
    onSuccess: (result) => {
      if (result.success) {
        showSuccessToast(`Test delivery successful (${result.status_code}, ${result.response_time_ms}ms)`);
      } else {
        showErrorToast(`Test delivery failed: ${result.error || 'Unknown error'}`);
      }
      setTestingId(null);
    },
    onError: () => {
      showErrorToast('Failed to send test event');
      setTestingId(null);
    },
  });

  // Generate a random secret key
  const generateSecret = (): string => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = 'whsec_';
    for (let i = 0; i < 32; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  };

  // Open modal for creating a new endpoint
  const handleAddEndpoint = () => {
    setEditingWebhook(null);
    setFormData({
      ...initialFormData,
      secret: generateSecret(),
    });
    setFormErrors({});
    setIsModalOpen(true);
  };

  // Open modal for editing an endpoint
  const handleEditEndpoint = (webhook: Webhook) => {
    setEditingWebhook(webhook);
    setFormData({
      url: webhook.url,
      events: Array.isArray(webhook.events) ? webhook.events.map((e: any) => (typeof e === 'string' ? e : e.toString())) : [],
      description: webhook.name || '',
      secret: webhook.secret || '',
      is_active: webhook.is_active,
      max_retries: '3',
    });
    setFormErrors({});
    setIsModalOpen(true);
  };

  // Close modal
  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingWebhook(null);
    setFormData(initialFormData);
    setFormErrors({});
  };

  // Toggle event type in form
  const handleToggleEvent = (eventValue: string) => {
    setFormData((prev) => ({
      ...prev,
      events: prev.events.includes(eventValue)
        ? prev.events.filter((e) => e !== eventValue)
        : [...prev.events, eventValue],
    }));
  };

  // Validate form
  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.url.trim()) {
      errors.url = 'URL is required';
    } else {
      try {
        new URL(formData.url);
      } catch {
        errors.url = 'Please enter a valid URL';
      }
    }

    if (formData.events.length === 0) {
      errors.events = 'Select at least one event type';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Submit form
  const handleSubmit = () => {
    if (!validateForm()) return;

    const payload = {
      url: formData.url,
      events: formData.events,
      description: formData.description || undefined,
      secret: formData.secret || undefined,
      is_active: formData.is_active,
    };

    if (editingWebhook) {
      updateMutation.mutate({ id: editingWebhook.id, data: payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  // Test a webhook endpoint
  const handleTestEndpoint = (id: string) => {
    setTestingId(id);
    testMutation.mutate(id);
  };

  // Format datetime
  const formatDateTime = (date: string) => {
    return new Date(date).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Get status badge for webhook
  const getWebhookStatusBadge = (isActive: boolean) => {
    return (
      <Badge variant={isActive ? 'success' : 'default'} dot>
        {isActive ? 'Active' : 'Inactive'}
      </Badge>
    );
  };

  // Get event status badge for deliveries
  const getEventStatusBadge = (status: string) => {
    const variants: Record<string, 'warning' | 'success' | 'danger' | 'default'> = {
      pending: 'warning',
      processed: 'success',
      success: 'success',
      failed: 'danger',
    };
    return (
      <Badge variant={variants[status] || 'default'}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  // Format event type as readable label
  const formatEventType = (eventType: string) => {
    return eventType
      .replace(/[._]/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase());
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Webhooks</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Manage webhook endpoints and monitor event deliveries
          </p>
        </div>
        <Button onClick={handleAddEndpoint}>
          <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Add Endpoint
        </Button>
      </div>

      {/* Section 1: Webhook Endpoints */}
      <Card>
        <CardHeader>
          <CardTitle>
            Webhook Endpoints
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoadingWebhooks ? (
            <div className="p-6">
              <SkeletonTable rows={3} columns={6} />
            </div>
          ) : webhooksData && webhooksData.results.length > 0 ? (
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeaderCell>URL</TableHeaderCell>
                  <TableHeaderCell>Event Types</TableHeaderCell>
                  <TableHeaderCell>Status</TableHeaderCell>
                  <TableHeaderCell>Delivery Stats</TableHeaderCell>
                  <TableHeaderCell>Last Delivery</TableHeaderCell>
                  <TableHeaderCell align="right">Actions</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {webhooksData.results.map((webhook: Webhook) => (
                  <TableRow key={webhook.id}>
                    <TableCell>
                      <div className="max-w-xs">
                        <p className="font-mono text-sm font-medium text-gray-900 dark:text-white truncate">
                          {webhook.url}
                        </p>
                        {webhook.name && (
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                            {webhook.name}
                          </p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1 max-w-xs">
                        {Array.isArray(webhook.events) &&
                          webhook.events.slice(0, 3).map((event: any, idx: number) => (
                            <Badge key={idx} variant="info" size="sm">
                              {formatEventType(typeof event === 'string' ? event : String(event))}
                            </Badge>
                          ))}
                        {Array.isArray(webhook.events) && webhook.events.length > 3 && (
                          <Badge variant="default" size="sm">
                            +{webhook.events.length - 3} more
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      {getWebhookStatusBadge(webhook.is_active)}
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        <span className="text-green-600 dark:text-green-400 font-medium">--</span>
                        <span className="text-gray-400 mx-1">/</span>
                        <span className="text-red-600 dark:text-red-400 font-medium">--</span>
                        <span className="text-xs text-gray-500 ml-1">(ok/fail)</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-gray-500 dark:text-gray-400">
                        {webhook.updated_at ? formatDateTime(webhook.updated_at) : 'Never'}
                      </span>
                    </TableCell>
                    <TableCell align="right">
                      <div className="flex items-center justify-end space-x-2">
                        {/* Edit */}
                        <button
                          onClick={() => handleEditEndpoint(webhook)}
                          className="p-1.5 text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                          title="Edit endpoint"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                        </button>

                        {/* Test */}
                        <button
                          onClick={() => handleTestEndpoint(webhook.id)}
                          disabled={testingId === webhook.id}
                          className="p-1.5 text-gray-400 hover:text-amber-600 dark:hover:text-amber-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors disabled:opacity-50"
                          title="Send test event"
                        >
                          {testingId === webhook.id ? (
                            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                            </svg>
                          ) : (
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                          )}
                        </button>

                        {/* Delete */}
                        <button
                          onClick={() => setDeleteConfirmId(webhook.id)}
                          className="p-1.5 text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                          title="Delete endpoint"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
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
                <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No webhook endpoints
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Create a webhook endpoint to receive real-time event notifications
              </p>
              <Button onClick={handleAddEndpoint}>
                <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Add Your First Endpoint
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Section 2: Recent Events */}
      <Card>
        <CardHeader
          action={
            <div className="flex items-center space-x-3">
              <Select
                value={eventTypeFilter}
                onChange={(e) => setEventTypeFilter(e.target.value)}
                options={[
                  { value: '', label: 'All Event Types' },
                  ...AVAILABLE_EVENT_TYPES,
                ]}
                className="w-44"
              />
              <Select
                value={eventStatusFilter}
                onChange={(e) => setEventStatusFilter(e.target.value)}
                options={[
                  { value: '', label: 'All Statuses' },
                  { value: 'pending', label: 'Pending' },
                  { value: 'success', label: 'Processed' },
                  { value: 'failed', label: 'Failed' },
                ]}
                className="w-36"
              />
            </div>
          }
        >
          <CardTitle>Recent Events</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoadingDeliveries ? (
            <div className="p-6">
              <SkeletonTable rows={5} columns={5} />
            </div>
          ) : deliveriesData && deliveriesData.results.length > 0 ? (
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeaderCell>Event Type</TableHeaderCell>
                  <TableHeaderCell>Source</TableHeaderCell>
                  <TableHeaderCell>Status</TableHeaderCell>
                  <TableHeaderCell>Received</TableHeaderCell>
                  <TableHeaderCell>Processing Time</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {deliveriesData.results.map((event: any) => (
                  <React.Fragment key={event.id}>
                    <TableRow
                      onClick={() =>
                        setExpandedEventId(expandedEventId === event.id ? null : event.id)
                      }
                    >
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <svg
                            className={`w-4 h-4 transition-transform duration-200 text-gray-400 ${
                              expandedEventId === event.id ? 'rotate-90' : ''
                            }`}
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                          <Badge variant="info" size="sm">
                            {formatEventType(event.event_type || event.event || 'unknown')}
                          </Badge>
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm text-gray-600 dark:text-gray-400 font-mono">
                          {event.webhook_url || event.source || '--'}
                        </span>
                      </TableCell>
                      <TableCell>
                        {getEventStatusBadge(event.status || 'pending')}
                      </TableCell>
                      <TableCell>
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          {event.created_at ? formatDateTime(event.created_at) : '--'}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm font-mono text-gray-600 dark:text-gray-400">
                          {event.response_time_ms ? `${event.response_time_ms}ms` : '--'}
                        </span>
                      </TableCell>
                    </TableRow>

                    {/* Expanded payload view */}
                    {expandedEventId === event.id && (
                      <tr>
                        <td colSpan={5} className="px-6 py-4 bg-gray-50 dark:bg-gray-800/50">
                          <div>
                            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
                              Event Payload
                            </p>
                            <pre className="bg-gray-900 dark:bg-gray-950 text-green-400 text-xs p-4 rounded-lg overflow-x-auto max-h-64 overflow-y-auto">
                              <code>
                                {JSON.stringify(
                                  event.payload || event.request_body || { event_type: event.event_type, id: event.id, timestamp: event.created_at },
                                  null,
                                  2
                                )}
                              </code>
                            </pre>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No recent events
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                {eventTypeFilter || eventStatusFilter
                  ? 'Try adjusting your filters'
                  : 'Webhook event deliveries will appear here'}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add/Edit Endpoint Modal */}
      <Modal isOpen={isModalOpen} onClose={handleCloseModal} size="lg">
        <ModalHeader>
          {editingWebhook ? 'Edit Webhook Endpoint' : 'Add Webhook Endpoint'}
        </ModalHeader>
        <ModalBody>
          <div className="space-y-5">
            {/* URL */}
            <Input
              label="Endpoint URL"
              placeholder="https://example.com/webhooks/aureon"
              value={formData.url}
              onChange={(e) => setFormData((prev) => ({ ...prev, url: e.target.value }))}
              error={formErrors.url}
              fullWidth
            />

            {/* Description */}
            <Input
              label="Description (optional)"
              placeholder="A brief description of this endpoint"
              value={formData.description}
              onChange={(e) => setFormData((prev) => ({ ...prev, description: e.target.value }))}
              fullWidth
            />

            {/* Event Types Multi-Select */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Event Types
              </label>
              {formErrors.events && (
                <p className="text-sm text-red-600 dark:text-red-400 mb-2">{formErrors.events}</p>
              )}
              <div className="grid grid-cols-2 gap-2">
                {AVAILABLE_EVENT_TYPES.map((eventType) => (
                  <label
                    key={eventType.value}
                    className={`flex items-center p-3 rounded-lg border cursor-pointer transition-colors ${
                      formData.events.includes(eventType.value)
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 dark:border-primary-500'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={formData.events.includes(eventType.value)}
                      onChange={() => handleToggleEvent(eventType.value)}
                      className="h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                    />
                    <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                      {eventType.label}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* Secret Key */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Signing Secret
                </label>
                <button
                  type="button"
                  onClick={() => setFormData((prev) => ({ ...prev, secret: generateSecret() }))}
                  className="text-xs text-primary-600 dark:text-primary-400 hover:underline"
                >
                  Regenerate
                </button>
              </div>
              <div className="relative">
                <Input
                  value={formData.secret}
                  onChange={(e) => setFormData((prev) => ({ ...prev, secret: e.target.value }))}
                  placeholder="whsec_..."
                  fullWidth
                  className="font-mono text-sm"
                />
              </div>
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Use this secret to verify webhook signatures on your server
              </p>
            </div>

            {/* Retry Settings */}
            <Select
              label="Retry Policy"
              value={formData.max_retries}
              onChange={(e) => setFormData((prev) => ({ ...prev, max_retries: e.target.value }))}
              options={RETRY_OPTIONS}
              fullWidth
            />

            {/* Active Toggle */}
            <div className="flex items-center justify-between p-3 rounded-lg border border-gray-200 dark:border-gray-700">
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">Active</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Enable or disable event delivery to this endpoint
                </p>
              </div>
              <button
                type="button"
                onClick={() => setFormData((prev) => ({ ...prev, is_active: !prev.is_active }))}
                className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
                  formData.is_active ? 'bg-primary-500' : 'bg-gray-200 dark:bg-gray-700'
                }`}
                role="switch"
                aria-checked={formData.is_active}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                    formData.is_active ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>
          </div>
        </ModalBody>
        <ModalFooter>
          <Button variant="ghost" onClick={handleCloseModal}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            isLoading={createMutation.isPending || updateMutation.isPending}
          >
            {editingWebhook ? 'Update Endpoint' : 'Create Endpoint'}
          </Button>
        </ModalFooter>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={deleteConfirmId !== null}
        onClose={() => setDeleteConfirmId(null)}
        size="sm"
      >
        <ModalHeader>Delete Webhook Endpoint</ModalHeader>
        <ModalBody>
          <p className="text-gray-600 dark:text-gray-400">
            Are you sure you want to delete this webhook endpoint? This action cannot be undone
            and all delivery history will be permanently removed.
          </p>
        </ModalBody>
        <ModalFooter>
          <Button variant="ghost" onClick={() => setDeleteConfirmId(null)}>
            Cancel
          </Button>
          <Button
            variant="danger"
            onClick={() => deleteConfirmId && deleteMutation.mutate(deleteConfirmId)}
            isLoading={deleteMutation.isPending}
          >
            Delete Endpoint
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
};

export default WebhookManagement;
