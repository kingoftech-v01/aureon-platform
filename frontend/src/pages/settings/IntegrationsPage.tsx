/**
 * Integrations Page
 * Aureon by Rhematek Solutions
 *
 * Manage third-party integrations and webhooks
 */

import React, { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/services/api';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import LoadingSpinner from '@/components/common/LoadingSpinner';

// ============================================
// TYPES
// ============================================

type IntegrationStatus = 'active' | 'inactive' | 'error';
type IntegrationType = 'accounting' | 'calendar' | 'communication' | 'webhook';

interface Integration {
  id: string;
  name: string;
  slug: string;
  description: string;
  type: IntegrationType;
  status: IntegrationStatus;
  icon?: string;
  last_sync?: string | null;
  connected_at?: string | null;
  error_message?: string | null;
  config?: Record<string, unknown>;
}

interface IntegrationListResponse {
  count: number;
  results: Integration[];
}

// ============================================
// INTEGRATION DEFINITIONS
// ============================================

interface IntegrationDef {
  slug: string;
  name: string;
  description: string;
  type: IntegrationType;
  color: string;
  iconPath: string;
}

const INTEGRATION_DEFS: IntegrationDef[] = [
  {
    slug: 'quickbooks',
    name: 'QuickBooks',
    description: 'Sync invoices, payments, and financial data with QuickBooks Online.',
    type: 'accounting',
    color: 'bg-green-500',
    iconPath:
      'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4',
  },
  {
    slug: 'xero',
    name: 'Xero',
    description: 'Connect with Xero for seamless accounting and reconciliation.',
    type: 'accounting',
    color: 'bg-blue-500',
    iconPath:
      'M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z',
  },
  {
    slug: 'google-calendar',
    name: 'Google Calendar',
    description: 'Sync meetings, deadlines, and milestones with Google Calendar.',
    type: 'calendar',
    color: 'bg-red-500',
    iconPath:
      'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z',
  },
  {
    slug: 'outlook',
    name: 'Outlook',
    description: 'Integrate with Microsoft Outlook for email and calendar sync.',
    type: 'calendar',
    color: 'bg-blue-600',
    iconPath:
      'M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z',
  },
  {
    slug: 'slack',
    name: 'Slack',
    description: 'Get real-time notifications for payments, contracts, and invoices in Slack.',
    type: 'communication',
    color: 'bg-purple-500',
    iconPath:
      'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
  },
  {
    slug: 'custom-webhook',
    name: 'Custom Webhook',
    description: 'Configure custom webhooks for events like contract signing and payment completion.',
    type: 'webhook',
    color: 'bg-gray-600',
    iconPath:
      'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4',
  },
];

// ============================================
// COMPONENT
// ============================================

const IntegrationsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { success: showSuccessToast, error: showErrorToast } = useToast();
  const [syncingId, setSyncingId] = useState<string | null>(null);

  // ============================================
  // DATA FETCHING
  // ============================================

  const {
    data: integrationsData,
    isLoading,
    error,
  } = useQuery<IntegrationListResponse>({
    queryKey: ['integrations'],
    queryFn: async () => {
      const response = await apiClient.get('/integrations/');
      return response.data;
    },
  });

  React.useEffect(() => {
    if (error) {
      showErrorToast('Failed to load integrations');
    }
  }, [error, showErrorToast]);

  // ============================================
  // MUTATIONS
  // ============================================

  const connectMutation = useMutation({
    mutationFn: async (integrationId: string) => {
      const response = await apiClient.post(`/integrations/${integrationId}/connect/`);
      return response.data;
    },
    onSuccess: (_data, integrationId) => {
      const integration = getIntegrationByApiId(integrationId);
      showSuccessToast(`${integration?.name || 'Integration'} connected successfully`);
      queryClient.invalidateQueries({ queryKey: ['integrations'] });
    },
    onError: () => {
      showErrorToast('Failed to connect integration');
    },
  });

  const disconnectMutation = useMutation({
    mutationFn: async (integrationId: string) => {
      const response = await apiClient.post(`/integrations/${integrationId}/disconnect/`);
      return response.data;
    },
    onSuccess: (_data, integrationId) => {
      const integration = getIntegrationByApiId(integrationId);
      showSuccessToast(`${integration?.name || 'Integration'} disconnected`);
      queryClient.invalidateQueries({ queryKey: ['integrations'] });
    },
    onError: () => {
      showErrorToast('Failed to disconnect integration');
    },
  });

  const syncMutation = useMutation({
    mutationFn: async (integrationId: string) => {
      setSyncingId(integrationId);
      const response = await apiClient.post(`/integrations/${integrationId}/sync/`);
      return response.data;
    },
    onSuccess: (_data, integrationId) => {
      const integration = getIntegrationByApiId(integrationId);
      showSuccessToast(`${integration?.name || 'Integration'} synced successfully`);
      queryClient.invalidateQueries({ queryKey: ['integrations'] });
      setSyncingId(null);
    },
    onError: () => {
      showErrorToast('Failed to sync integration');
      setSyncingId(null);
    },
  });

  // ============================================
  // HELPERS
  // ============================================

  const getIntegrationByApiId = useCallback(
    (apiId: string): Integration | undefined => {
      return integrationsData?.results.find((i) => i.id === apiId);
    },
    [integrationsData]
  );

  const getApiIntegration = useCallback(
    (slug: string): Integration | undefined => {
      return integrationsData?.results.find((i) => i.slug === slug);
    },
    [integrationsData]
  );

  const getStatusBadge = (status: IntegrationStatus) => {
    const config: Record<IntegrationStatus, { variant: 'success' | 'default' | 'danger'; label: string }> = {
      active: { variant: 'success', label: 'Connected' },
      inactive: { variant: 'default', label: 'Not Connected' },
      error: { variant: 'danger', label: 'Error' },
    };
    const { variant, label } = config[status];
    return <Badge variant={variant} dot>{label}</Badge>;
  };

  const getTypeBadge = (type: IntegrationType) => {
    const config: Record<IntegrationType, { variant: 'info' | 'primary' | 'warning' | 'default'; label: string }> = {
      accounting: { variant: 'info', label: 'Accounting' },
      calendar: { variant: 'primary', label: 'Calendar' },
      communication: { variant: 'warning', label: 'Communication' },
      webhook: { variant: 'default', label: 'Webhook' },
    };
    const { variant, label } = config[type];
    return <Badge variant={variant} size="sm">{label}</Badge>;
  };

  const formatDateTime = (date: string | null | undefined): string => {
    if (!date) return 'Never';
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Build merged integration list (definitions + API data)
  const mergedIntegrations = INTEGRATION_DEFS.map((def) => {
    const apiData = getApiIntegration(def.slug);
    return {
      ...def,
      apiId: apiData?.id || null,
      status: apiData?.status || ('inactive' as IntegrationStatus),
      last_sync: apiData?.last_sync || null,
      connected_at: apiData?.connected_at || null,
      error_message: apiData?.error_message || null,
    };
  });

  const connectedIntegrations = mergedIntegrations.filter((i) => i.status === 'active' || i.status === 'error');

  // ============================================
  // RENDER
  // ============================================

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto flex items-center justify-center py-24">
        <LoadingSpinner size="lg" text="Loading integrations..." />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Integrations</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Connect your favorite tools and services to streamline your workflow
        </p>
      </div>

      {/* Available Integrations Grid */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Available Integrations
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {mergedIntegrations.map((integration) => (
            <Card key={integration.slug} hover className="flex flex-col">
              <CardContent className="flex flex-col flex-1">
                {/* Icon and Status Row */}
                <div className="flex items-start justify-between mb-3">
                  <div className={`w-12 h-12 ${integration.color} rounded-lg flex items-center justify-center`}>
                    <svg
                      className="w-6 h-6 text-white"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d={integration.iconPath}
                      />
                    </svg>
                  </div>
                  {getStatusBadge(integration.status)}
                </div>

                {/* Name and Type */}
                <div className="mb-2">
                  <div className="flex items-center space-x-2 mb-1">
                    <h3 className="text-base font-semibold text-gray-900 dark:text-white">
                      {integration.name}
                    </h3>
                    {getTypeBadge(integration.type)}
                  </div>
                </div>

                {/* Description */}
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 flex-1">
                  {integration.description}
                </p>

                {/* Error Message */}
                {integration.status === 'error' && integration.error_message && (
                  <div className="mb-3 p-2 bg-red-50 dark:bg-red-900/20 rounded-md">
                    <p className="text-xs text-red-600 dark:text-red-400">
                      {integration.error_message}
                    </p>
                  </div>
                )}

                {/* Action Button */}
                <div className="mt-auto">
                  {integration.status === 'active' ? (
                    <Button
                      variant="outline"
                      size="sm"
                      fullWidth
                      onClick={() => {
                        if (integration.apiId && window.confirm(`Disconnect ${integration.name}?`)) {
                          disconnectMutation.mutate(integration.apiId);
                        }
                      }}
                      isLoading={disconnectMutation.isPending}
                    >
                      Disconnect
                    </Button>
                  ) : integration.status === 'error' ? (
                    <div className="flex space-x-2">
                      <Button
                        variant="primary"
                        size="sm"
                        className="flex-1"
                        onClick={() => {
                          if (integration.apiId) {
                            connectMutation.mutate(integration.apiId);
                          }
                        }}
                        isLoading={connectMutation.isPending}
                      >
                        Reconnect
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          if (integration.apiId && window.confirm(`Disconnect ${integration.name}?`)) {
                            disconnectMutation.mutate(integration.apiId);
                          }
                        }}
                        isLoading={disconnectMutation.isPending}
                      >
                        Remove
                      </Button>
                    </div>
                  ) : (
                    <Button
                      variant="primary"
                      size="sm"
                      fullWidth
                      onClick={() => {
                        if (integration.apiId) {
                          connectMutation.mutate(integration.apiId);
                        }
                      }}
                      isLoading={connectMutation.isPending}
                    >
                      Connect
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Connected Integrations Details */}
      {connectedIntegrations.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Connected Integrations
          </h2>
          <div className="space-y-4">
            {connectedIntegrations.map((integration) => (
              <Card key={`connected-${integration.slug}`}>
                <CardContent>
                  <div className="flex items-center justify-between">
                    {/* Left: Integration Info */}
                    <div className="flex items-center space-x-4">
                      <div className={`w-10 h-10 ${integration.color} rounded-lg flex items-center justify-center`}>
                        <svg
                          className="w-5 h-5 text-white"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d={integration.iconPath}
                          />
                        </svg>
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <h3 className="font-medium text-gray-900 dark:text-white">
                            {integration.name}
                          </h3>
                          {getStatusBadge(integration.status)}
                        </div>
                        <div className="flex items-center space-x-4 mt-1">
                          <span className="text-sm text-gray-500 dark:text-gray-400">
                            Connected: {formatDateTime(integration.connected_at)}
                          </span>
                          <span className="text-sm text-gray-500 dark:text-gray-400">
                            Last sync: {formatDateTime(integration.last_sync)}
                          </span>
                        </div>
                        {integration.status === 'error' && integration.error_message && (
                          <p className="text-sm text-red-500 dark:text-red-400 mt-1">
                            {integration.error_message}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Right: Actions */}
                    <div className="flex items-center space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          if (integration.apiId) {
                            syncMutation.mutate(integration.apiId);
                          }
                        }}
                        isLoading={syncingId === integration.apiId}
                        leftIcon={
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                            />
                          </svg>
                        }
                      >
                        Sync Now
                      </Button>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => {
                          if (
                            integration.apiId &&
                            window.confirm(`Are you sure you want to disconnect ${integration.name}?`)
                          ) {
                            disconnectMutation.mutate(integration.apiId);
                          }
                        }}
                        isLoading={disconnectMutation.isPending}
                      >
                        Disconnect
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* No Connected Integrations */}
      {connectedIntegrations.length === 0 && !isLoading && (
        <Card>
          <CardContent>
            <div className="py-8 text-center">
              <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No connected integrations
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Connect an integration above to get started
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default IntegrationsPage;
