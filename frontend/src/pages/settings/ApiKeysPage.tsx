/**
 * API Keys Page
 * Aureon by Rhematek Solutions
 *
 * API key management with creation, reveal-once flow,
 * permissions, and revocation.
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import Table, { TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '@/components/common/Table';
import Modal, { ModalHeader, ModalBody, ModalFooter } from '@/components/common/Modal';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import { SkeletonTable } from '@/components/common/Skeleton';
import apiClient from '@/services/api';

interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  permissions: string[];
  created_at: string;
  last_used_at: string | null;
  is_active: boolean;
}

interface NewApiKeyResponse {
  id: string;
  name: string;
  key: string;
  permissions: string[];
  created_at: string;
}

const PERMISSION_OPTIONS = [
  { value: 'read', label: 'Read', description: 'View clients, contracts, invoices, and payments' },
  { value: 'write', label: 'Write', description: 'Create and update clients, contracts, and invoices' },
  { value: 'admin', label: 'Admin', description: 'Full access including team management and settings' },
];

const ApiKeysPage: React.FC = () => {
  const { success: showSuccess, error: showError } = useToast();
  const queryClient = useQueryClient();

  // Modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showRevealModal, setShowRevealModal] = useState(false);
  const [showRevokeModal, setShowRevokeModal] = useState(false);
  const [revokeTargetId, setRevokeTargetId] = useState<string | null>(null);
  const [revealedKey, setRevealedKey] = useState<string>('');
  const [copied, setCopied] = useState(false);

  // Create form state
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyPermissions, setNewKeyPermissions] = useState<string[]>(['read']);

  // Fetch API keys
  const { data: apiKeys, isLoading } = useQuery<ApiKey[]>({
    queryKey: ['api-keys'],
    queryFn: async () => {
      const response = await apiClient.get('/auth/api-keys/');
      return response.data.results || response.data;
    },
  });

  // Create API key mutation
  const createMutation = useMutation({
    mutationFn: async (data: { name: string; permissions: string[] }): Promise<NewApiKeyResponse> => {
      const response = await apiClient.post('/auth/api-keys/', data);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] });
      setRevealedKey(data.key);
      setShowCreateModal(false);
      setShowRevealModal(true);
      setNewKeyName('');
      setNewKeyPermissions(['read']);
    },
    onError: () => {
      showError('Failed to create API key');
    },
  });

  // Revoke API key mutation
  const revokeMutation = useMutation({
    mutationFn: async (keyId: string) => {
      await apiClient.delete(`/auth/api-keys/${keyId}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] });
      showSuccess('API key revoked successfully');
      setShowRevokeModal(false);
      setRevokeTargetId(null);
    },
    onError: () => {
      showError('Failed to revoke API key');
    },
  });

  // Format date
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatRelativeDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return formatDate(dateStr);
  };

  // Toggle permission
  const togglePermission = (perm: string) => {
    setNewKeyPermissions((prev) =>
      prev.includes(perm) ? prev.filter((p) => p !== perm) : [...prev, perm]
    );
  };

  // Copy to clipboard
  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(revealedKey);
      setCopied(true);
      showSuccess('API key copied to clipboard');
      setTimeout(() => setCopied(false), 3000);
    } catch {
      showError('Failed to copy to clipboard');
    }
  };

  // Handle create
  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyName.trim()) {
      showError('Please provide a name for the API key');
      return;
    }
    if (newKeyPermissions.length === 0) {
      showError('Please select at least one permission');
      return;
    }
    createMutation.mutate({ name: newKeyName, permissions: newKeyPermissions });
  };

  // Handle revoke
  const handleRevoke = (keyId: string) => {
    setRevokeTargetId(keyId);
    setShowRevokeModal(true);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-500 to-primary-600 rounded-2xl p-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">API Keys</h1>
            <p className="mt-2 text-primary-100">Manage API keys for programmatic access to your account</p>
          </div>
          <Button
            variant="secondary"
            onClick={() => setShowCreateModal(true)}
            className="bg-white/20 hover:bg-white/30 text-white border-0"
          >
            <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Create New Key
          </Button>
        </div>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <svg className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <p className="text-sm text-blue-800 dark:text-blue-300 font-medium">
              API keys provide programmatic access to your Aureon account.
            </p>
            <p className="text-sm text-blue-700 dark:text-blue-400 mt-1">
              Keep your keys secure and never share them publicly. Keys are only shown once upon creation.
            </p>
          </div>
        </div>
      </div>

      {/* API Keys Table */}
      <Card>
        <CardHeader>
          <CardTitle>
            {apiKeys ? `${apiKeys.length} API Key${apiKeys.length !== 1 ? 's' : ''}` : 'API Keys'}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6">
              <SkeletonTable rows={3} columns={6} />
            </div>
          ) : apiKeys && apiKeys.length > 0 ? (
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeaderCell>Name</TableHeaderCell>
                  <TableHeaderCell>Key</TableHeaderCell>
                  <TableHeaderCell>Permissions</TableHeaderCell>
                  <TableHeaderCell>Created</TableHeaderCell>
                  <TableHeaderCell>Last Used</TableHeaderCell>
                  <TableHeaderCell>Status</TableHeaderCell>
                  <TableHeaderCell align="right">Actions</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {apiKeys.map((apiKey) => (
                  <TableRow key={apiKey.id}>
                    <TableCell>
                      <span className="font-medium text-gray-900 dark:text-white">{apiKey.name}</span>
                    </TableCell>
                    <TableCell>
                      <code className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded text-sm font-mono text-gray-700 dark:text-gray-300">
                        {apiKey.key_prefix}...
                      </code>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {apiKey.permissions.map((perm) => (
                          <Badge
                            key={perm}
                            variant={perm === 'admin' ? 'danger' : perm === 'write' ? 'warning' : 'info'}
                            size="sm"
                          >
                            {perm}
                          </Badge>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {formatDate(apiKey.created_at)}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {formatRelativeDate(apiKey.last_used_at)}
                      </span>
                    </TableCell>
                    <TableCell>
                      <Badge variant={apiKey.is_active ? 'success' : 'default'} size="sm" dot>
                        {apiKey.is_active ? 'Active' : 'Revoked'}
                      </Badge>
                    </TableCell>
                    <TableCell align="right">
                      {apiKey.is_active && (
                        <Button
                          variant="danger"
                          size="sm"
                          onClick={() => handleRevoke(apiKey.id)}
                        >
                          Revoke
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No API keys</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Create your first API key to start integrating with the Aureon API.
              </p>
              <Button variant="primary" onClick={() => setShowCreateModal(true)}>
                Create API Key
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create API Key Modal */}
      <Modal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} size="md">
        <ModalHeader>Create API Key</ModalHeader>
        <form onSubmit={handleCreate}>
          <ModalBody>
            <div className="space-y-4">
              <Input
                label="Key Name"
                placeholder="e.g., Production Server, CI/CD Pipeline"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                fullWidth
                required
              />
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Permissions
                </label>
                <div className="space-y-3">
                  {PERMISSION_OPTIONS.map((option) => (
                    <label
                      key={option.value}
                      className={`flex items-start p-3 border rounded-lg cursor-pointer transition-colors ${
                        newKeyPermissions.includes(option.value)
                          ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/10'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={newKeyPermissions.includes(option.value)}
                        onChange={() => togglePermission(option.value)}
                        className="mt-1 h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                      />
                      <div className="ml-3">
                        <p className="text-sm font-medium text-gray-900 dark:text-white">{option.label}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">{option.description}</p>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" onClick={() => setShowCreateModal(false)} type="button">
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={createMutation.isPending}>
              Create Key
            </Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* Reveal Key Modal */}
      <Modal isOpen={showRevealModal} onClose={() => setShowRevealModal(false)} size="md" closeOnOverlayClick={false}>
        <ModalHeader>API Key Created</ModalHeader>
        <ModalBody>
          <div className="space-y-4">
            <div className="p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
              <div className="flex items-start space-x-2">
                <svg className="w-5 h-5 text-amber-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
                <p className="text-sm text-amber-800 dark:text-amber-300 font-medium">
                  This is the only time you will see this key. Copy it now and store it securely.
                </p>
              </div>
            </div>
            <div className="relative">
              <code className="block w-full p-4 bg-gray-900 dark:bg-gray-950 text-green-400 rounded-lg font-mono text-sm break-all select-all">
                {revealedKey}
              </code>
              <button
                onClick={copyToClipboard}
                className="absolute top-2 right-2 p-2 bg-gray-700 hover:bg-gray-600 rounded-md transition-colors"
                title="Copy to clipboard"
              >
                {copied ? (
                  <svg className="w-4 h-4 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </ModalBody>
        <ModalFooter>
          <Button variant="primary" onClick={() => { setShowRevealModal(false); setRevealedKey(''); setCopied(false); }}>
            I've Saved My Key
          </Button>
        </ModalFooter>
      </Modal>

      {/* Revoke Confirmation Modal */}
      <Modal isOpen={showRevokeModal} onClose={() => setShowRevokeModal(false)} size="sm">
        <ModalHeader>Revoke API Key</ModalHeader>
        <ModalBody>
          <p className="text-gray-600 dark:text-gray-400">
            Are you sure you want to revoke this API key? Any applications using this key will immediately lose access.
          </p>
        </ModalBody>
        <ModalFooter>
          <Button variant="ghost" onClick={() => setShowRevokeModal(false)}>
            Cancel
          </Button>
          <Button
            variant="danger"
            onClick={() => revokeTargetId && revokeMutation.mutate(revokeTargetId)}
            isLoading={revokeMutation.isPending}
          >
            Revoke Key
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
};

export default ApiKeysPage;
