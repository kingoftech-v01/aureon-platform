/**
 * Template Manager Page
 * Aureon by Rhematek Solutions
 *
 * Contract and invoice template management with grid view,
 * create/edit modal, preview panel, and CRUD actions.
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Select from '@/components/common/Select';
import Card, { CardContent } from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import Modal, { ModalHeader, ModalBody, ModalFooter } from '@/components/common/Modal';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import apiClient from '@/services/api';

type TemplateType = 'contract' | 'invoice';

interface Template {
  id: string;
  name: string;
  type: TemplateType;
  description: string;
  content: string;
  last_modified: string;
  usage_count: number;
  is_default: boolean;
  created_at: string;
}

interface TemplateFormData {
  name: string;
  type: TemplateType;
  description: string;
  content: string;
}

const TemplateManager: React.FC = () => {
  const { success: showSuccess, error: showError } = useToast();
  const queryClient = useQueryClient();

  // Tab filter
  const [activeTab, setActiveTab] = useState<'all' | 'contract' | 'invoice'>('all');

  // Modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null);
  const [previewTemplate, setPreviewTemplate] = useState<Template | null>(null);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState<TemplateFormData>({
    name: '',
    type: 'contract',
    description: '',
    content: '',
  });

  // Fetch templates
  const { data: templates, isLoading } = useQuery<Template[]>({
    queryKey: ['templates'],
    queryFn: async () => {
      const response = await apiClient.get('/contracts/templates/');
      return response.data.results || response.data;
    },
  });

  // Create template mutation
  const createMutation = useMutation({
    mutationFn: async (data: TemplateFormData) => {
      const response = await apiClient.post('/contracts/templates/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      showSuccess('Template created successfully');
      resetForm();
    },
    onError: () => {
      showError('Failed to create template');
    },
  });

  // Update template mutation
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: TemplateFormData }) => {
      const response = await apiClient.put(`/contracts/templates/${id}/`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      showSuccess('Template updated successfully');
      resetForm();
    },
    onError: () => {
      showError('Failed to update template');
    },
  });

  // Delete template mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/contracts/templates/${id}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      showSuccess('Template deleted successfully');
      setShowDeleteModal(false);
      setDeleteTargetId(null);
    },
    onError: () => {
      showError('Failed to delete template');
    },
  });

  // Duplicate template mutation
  const duplicateMutation = useMutation({
    mutationFn: async (template: Template) => {
      const response = await apiClient.post('/contracts/templates/', {
        name: `${template.name} (Copy)`,
        type: template.type,
        description: template.description,
        content: template.content,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      showSuccess('Template duplicated successfully');
    },
    onError: () => {
      showError('Failed to duplicate template');
    },
  });

  // Reset form
  const resetForm = () => {
    setFormData({ name: '', type: 'contract', description: '', content: '' });
    setEditingTemplate(null);
    setShowCreateModal(false);
  };

  // Open create modal
  const openCreateModal = () => {
    setFormData({ name: '', type: 'contract', description: '', content: '' });
    setEditingTemplate(null);
    setShowCreateModal(true);
  };

  // Open edit modal
  const openEditModal = (template: Template) => {
    setFormData({
      name: template.name,
      type: template.type,
      description: template.description,
      content: template.content,
    });
    setEditingTemplate(template);
    setShowCreateModal(true);
  };

  // Open preview
  const openPreview = (template: Template) => {
    setPreviewTemplate(template);
    setShowPreviewModal(true);
  };

  // Handle form submit
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      showError('Template name is required');
      return;
    }
    if (editingTemplate) {
      updateMutation.mutate({ id: editingTemplate.id, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  // Handle delete
  const handleDelete = (id: string) => {
    setDeleteTargetId(id);
    setShowDeleteModal(true);
  };

  // Format date
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // Filter templates
  const filteredTemplates = templates?.filter((t) => {
    if (activeTab === 'all') return true;
    return t.type === activeTab;
  }) || [];

  // Tab classes
  const tabClass = (tab: typeof activeTab) =>
    `px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
      activeTab === tab
        ? 'bg-primary-500 text-white shadow-sm'
        : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800'
    }`;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-500 to-primary-600 rounded-2xl p-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Templates</h1>
            <p className="mt-2 text-primary-100">Manage your contract and invoice templates</p>
          </div>
          <Button
            variant="secondary"
            onClick={openCreateModal}
            className="bg-white/20 hover:bg-white/30 text-white border-0"
          >
            <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Create Template
          </Button>
        </div>
      </div>

      {/* Tab Filter */}
      <div className="flex items-center space-x-2 bg-gray-100 dark:bg-gray-800 rounded-lg p-1 w-fit">
        <button onClick={() => setActiveTab('all')} className={tabClass('all')}>
          All Templates
        </button>
        <button onClick={() => setActiveTab('contract')} className={tabClass('contract')}>
          Contract Templates
        </button>
        <button onClick={() => setActiveTab('invoice')} className={tabClass('invoice')}>
          Invoice Templates
        </button>
      </div>

      {/* Templates Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      ) : filteredTemplates.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTemplates.map((template) => (
            <Card key={template.id}>
              <CardContent className="p-5">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
                      {template.name}
                    </h3>
                    <div className="flex items-center space-x-2 mt-1">
                      <Badge
                        variant={template.type === 'contract' ? 'primary' : 'info'}
                        size="sm"
                      >
                        {template.type}
                      </Badge>
                      {template.is_default && (
                        <Badge variant="success" size="sm">Default</Badge>
                      )}
                    </div>
                  </div>
                </div>

                <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mb-4">
                  {template.description || 'No description provided'}
                </p>

                <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-4">
                  <span>Modified {formatDate(template.last_modified || template.created_at)}</span>
                  <span>{template.usage_count} uses</span>
                </div>

                {/* Actions */}
                <div className="flex items-center space-x-2 pt-3 border-t border-gray-100 dark:border-gray-700">
                  <button
                    onClick={() => openPreview(template)}
                    className="flex-1 px-3 py-2 text-sm font-medium text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/10 rounded-lg transition-colors text-center"
                  >
                    Use
                  </button>
                  <button
                    onClick={() => openEditModal(template)}
                    className="flex-1 px-3 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors text-center"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => duplicateMutation.mutate(template)}
                    className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                    title="Duplicate"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => handleDelete(template.id)}
                    className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/10 rounded-lg transition-colors"
                    title="Delete"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="text-center py-16">
          <div className="w-20 h-20 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-10 h-10 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            {activeTab === 'all' ? 'No templates yet' : `No ${activeTab} templates`}
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Create your first template to speed up contract and invoice creation.
          </p>
          <Button variant="primary" onClick={openCreateModal}>
            Create Your First Template
          </Button>
        </div>
      )}

      {/* Create/Edit Template Modal */}
      <Modal isOpen={showCreateModal} onClose={resetForm} size="lg">
        <ModalHeader>{editingTemplate ? 'Edit Template' : 'Create Template'}</ModalHeader>
        <form onSubmit={handleSubmit}>
          <ModalBody>
            <div className="space-y-4">
              <Input
                label="Template Name"
                placeholder="e.g., Standard Service Agreement"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                fullWidth
                required
              />
              <Select
                label="Template Type"
                value={formData.type}
                onChange={(e) => setFormData({ ...formData, type: e.target.value as TemplateType })}
                options={[
                  { value: 'contract', label: 'Contract Template' },
                  { value: 'invoice', label: 'Invoice Template' },
                ]}
                fullWidth
              />
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={2}
                  placeholder="Brief description of this template..."
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-3 text-gray-900 dark:text-white placeholder-gray-400 focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:outline-none transition-colors resize-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Template Content
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                  Use placeholders like {'{{client_name}}'}, {'{{date}}'}, {'{{amount}}'} for dynamic fields.
                </p>
                <textarea
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  rows={12}
                  placeholder={
                    formData.type === 'contract'
                      ? 'SERVICE AGREEMENT\n\nThis agreement is entered into between {{company_name}} and {{client_name}} on {{date}}.\n\n1. SCOPE OF SERVICES\n...'
                      : 'INVOICE\n\nInvoice #: {{invoice_number}}\nDate: {{date}}\nDue Date: {{due_date}}\n\nBill To:\n{{client_name}}\n{{client_address}}\n...'
                  }
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-3 text-gray-900 dark:text-white placeholder-gray-400 focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:outline-none transition-colors resize-none font-mono text-sm"
                />
              </div>
            </div>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" onClick={resetForm} type="button">
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              isLoading={createMutation.isPending || updateMutation.isPending}
            >
              {editingTemplate ? 'Update Template' : 'Create Template'}
            </Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* Preview Modal */}
      <Modal isOpen={showPreviewModal} onClose={() => setShowPreviewModal(false)} size="lg">
        <ModalHeader>
          {previewTemplate?.name || 'Template Preview'}
        </ModalHeader>
        <ModalBody>
          {previewTemplate && (
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <Badge variant={previewTemplate.type === 'contract' ? 'primary' : 'info'}>
                  {previewTemplate.type}
                </Badge>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  Last modified: {formatDate(previewTemplate.last_modified || previewTemplate.created_at)}
                </span>
              </div>
              {previewTemplate.description && (
                <p className="text-sm text-gray-600 dark:text-gray-400">{previewTemplate.description}</p>
              )}
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                <pre className="whitespace-pre-wrap text-sm text-gray-800 dark:text-gray-200 font-mono">
                  {previewTemplate.content || 'No content defined.'}
                </pre>
              </div>
            </div>
          )}
        </ModalBody>
        <ModalFooter>
          <Button variant="ghost" onClick={() => setShowPreviewModal(false)}>
            Close
          </Button>
          {previewTemplate && (
            <Button
              variant="primary"
              onClick={() => {
                setShowPreviewModal(false);
                openEditModal(previewTemplate);
              }}
            >
              Edit Template
            </Button>
          )}
        </ModalFooter>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal isOpen={showDeleteModal} onClose={() => setShowDeleteModal(false)} size="sm">
        <ModalHeader>Delete Template</ModalHeader>
        <ModalBody>
          <p className="text-gray-600 dark:text-gray-400">
            Are you sure you want to delete this template? This action cannot be undone. Existing contracts and invoices created from this template will not be affected.
          </p>
        </ModalBody>
        <ModalFooter>
          <Button variant="ghost" onClick={() => setShowDeleteModal(false)}>
            Cancel
          </Button>
          <Button
            variant="danger"
            onClick={() => deleteTargetId && deleteMutation.mutate(deleteTargetId)}
            isLoading={deleteMutation.isPending}
          >
            Delete Template
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
};

export default TemplateManager;
