/**
 * Contract Detail Page
 * Aureon by Rhematek Solutions
 *
 * Detailed view of a single contract with milestone timeline
 */

import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { contractService } from '@/services';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import { SkeletonCard } from '@/components/common/Skeleton';
import type { Contract, ContractStatus, ContractMilestone } from '@/types';

const ContractDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success: showSuccessToast, error: showErrorToast } = useToast();
  const [selectedTab, setSelectedTab] = useState<'overview' | 'milestones' | 'content'>('overview');

  // Fetch contract data
  const { data: contract, isLoading, error } = useQuery({
    queryKey: ['contract', id],
    queryFn: () => contractService.getContract(id!),
    enabled: !!id,
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: () => contractService.deleteContract(id!),
    onSuccess: () => {
      showSuccessToast('Contract deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['contracts'] });
      navigate('/contracts');
    },
    onError: (error: any) => {
      showErrorToast(error.response?.data?.message || 'Failed to delete contract');
    },
  });

  // Complete milestone mutation
  const completeMilestoneMutation = useMutation({
    mutationFn: (milestoneId: string) => contractService.completeMilestone(id!, milestoneId),
    onSuccess: () => {
      showSuccessToast('Milestone marked as complete');
      queryClient.invalidateQueries({ queryKey: ['contract', id] });
    },
    onError: (error: any) => {
      showErrorToast(error.response?.data?.message || 'Failed to complete milestone');
    },
  });

  // Send for signature
  const sendForSignatureMutation = useMutation({
    mutationFn: (data: { recipient_email: string; message?: string }) =>
      contractService.sendForSignature(id!, data),
    onSuccess: () => {
      showSuccessToast('Contract sent for signature');
      queryClient.invalidateQueries({ queryKey: ['contract', id] });
    },
    onError: (error: any) => {
      showErrorToast(error.response?.data?.message || 'Failed to send contract');
    },
  });

  // Handle delete with confirmation
  const handleDelete = () => {
    if (window.confirm('Are you sure you want to delete this contract? This action cannot be undone.')) {
      deleteMutation.mutate();
    }
  };

  // Handle send for signature
  const handleSendForSignature = () => {
    if (contract) {
      sendForSignatureMutation.mutate({
        recipient_email: contract.client.email,
      });
    }
  };

  // Contract status badge
  const getStatusBadge = (status: ContractStatus) => {
    const variants: Record<ContractStatus, 'default' | 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
      draft: 'default',
      sent: 'info',
      viewed: 'primary',
      signed: 'success',
      active: 'success',
      completed: 'default',
      terminated: 'danger',
      expired: 'warning',
    };
    return <Badge variant={variants[status]}>{status}</Badge>;
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
      month: 'long',
      day: 'numeric',
    });
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        <SkeletonCard />
        <SkeletonCard />
      </div>
    );
  }

  // Error state
  if (error || !contract) {
    return (
      <div className="max-w-4xl mx-auto">
        <Card>
          <CardContent className="p-12 text-center">
            <div className="w-16 h-16 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              Contract not found
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              The contract you're looking for doesn't exist or has been deleted.
            </p>
            <Link to="/contracts">
              <Button variant="primary">Back to Contracts</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  const completedMilestones = contract.milestones?.filter(m => m.is_completed).length || 0;
  const totalMilestones = contract.milestones?.length || 0;
  const milestoneProgress = totalMilestones > 0 ? (completedMilestones / totalMilestones) * 100 : 0;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center space-x-3 mb-2">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              {contract.title}
            </h1>
            {getStatusBadge(contract.status)}
          </div>
          <p className="text-gray-600 dark:text-gray-400">
            {contract.contract_number}
          </p>
          <Link to={`/clients/${contract.client.id}`} className="text-primary-600 hover:underline dark:text-primary-400 text-sm mt-1 inline-block">
            {contract.client.type === 'individual'
              ? `${contract.client.first_name} ${contract.client.last_name}`
              : contract.client.company_name}
          </Link>
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-3">
          {contract.status === 'draft' && (
            <Button
              variant="primary"
              onClick={handleSendForSignature}
              isLoading={sendForSignatureMutation.isPending}
            >
              <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              Send for Signature
            </Button>
          )}
          <Link to={`/contracts/${contract.id}/edit`}>
            <Button variant="outline">
              <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              Edit
            </Button>
          </Link>
          <Button
            variant="outline"
            onClick={handleDelete}
            isLoading={deleteMutation.isPending}
            className="text-red-600 hover:text-red-700 hover:border-red-600 dark:text-red-400"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setSelectedTab('overview')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              selectedTab === 'overview'
                ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setSelectedTab('milestones')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              selectedTab === 'milestones'
                ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
            }`}
          >
            Milestones ({completedMilestones}/{totalMilestones})
          </button>
          <button
            onClick={() => setSelectedTab('content')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              selectedTab === 'content'
                ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
            }`}
          >
            Contract Content
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {selectedTab === 'overview' && (
            <>
              {/* Contract Details */}
              <Card>
                <CardHeader>
                  <CardTitle>Contract Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {contract.description && (
                    <div>
                      <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Description</label>
                      <p className="text-gray-900 dark:text-white mt-1">{contract.description}</p>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <div>
                      <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Start Date</label>
                      <p className="text-gray-900 dark:text-white mt-1">
                        {contract.start_date ? formatDate(contract.start_date) : 'Not set'}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500 dark:text-gray-400">End Date</label>
                      <p className="text-gray-900 dark:text-white mt-1">
                        {contract.end_date ? formatDate(contract.end_date) : 'Not set'}
                      </p>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                    <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Value</label>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                      {formatCurrency(contract.total_value)}
                    </p>
                  </div>

                  {contract.signed_at && (
                    <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                      <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Signed On</label>
                      <p className="text-gray-900 dark:text-white mt-1">{formatDate(contract.signed_at)}</p>
                      {contract.signed_by_client && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          By: {contract.signed_by_client}
                        </p>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Progress */}
              {totalMilestones > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Progress</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600 dark:text-gray-400">
                          {completedMilestones} of {totalMilestones} milestones completed
                        </span>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {Math.round(milestoneProgress)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                          className="bg-primary-500 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${milestoneProgress}%` }}
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}

          {selectedTab === 'milestones' && (
            <Card>
              <CardHeader>
                <CardTitle>Milestone Timeline</CardTitle>
              </CardHeader>
              <CardContent>
                {contract.milestones && contract.milestones.length > 0 ? (
                  <div className="space-y-4">
                    {contract.milestones
                      .sort((a, b) => a.order - b.order)
                      .map((milestone, index) => (
                        <div key={milestone.id} className="relative pl-8">
                          {/* Timeline line */}
                          {index < contract.milestones.length - 1 && (
                            <div className="absolute left-3 top-8 bottom-0 w-0.5 bg-gray-200 dark:bg-gray-700" />
                          )}

                          {/* Milestone dot */}
                          <div
                            className={`absolute left-0 top-1.5 w-6 h-6 rounded-full border-2 ${
                              milestone.is_completed
                                ? 'bg-primary-500 border-primary-500'
                                : 'bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600'
                            } flex items-center justify-center`}
                          >
                            {milestone.is_completed && (
                              <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                              </svg>
                            )}
                          </div>

                          {/* Milestone content */}
                          <div className={`pb-6 ${milestone.is_completed ? 'opacity-75' : ''}`}>
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <h4 className={`font-medium ${milestone.is_completed ? 'line-through text-gray-500 dark:text-gray-400' : 'text-gray-900 dark:text-white'}`}>
                                  {milestone.title}
                                </h4>
                                {milestone.description && (
                                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                    {milestone.description}
                                  </p>
                                )}
                                <div className="flex items-center space-x-4 mt-2 text-sm">
                                  <span className="font-medium text-gray-900 dark:text-white">
                                    {formatCurrency(milestone.amount)}
                                  </span>
                                  {milestone.due_date && (
                                    <span className="text-gray-500 dark:text-gray-400">
                                      Due: {formatDate(milestone.due_date)}
                                    </span>
                                  )}
                                  {milestone.completed_at && (
                                    <span className="text-green-600 dark:text-green-400">
                                      Completed: {formatDate(milestone.completed_at)}
                                    </span>
                                  )}
                                </div>
                              </div>
                              {!milestone.is_completed && (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => completeMilestoneMutation.mutate(milestone.id)}
                                  isLoading={completeMilestoneMutation.isPending}
                                >
                                  Mark Complete
                                </Button>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <svg className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                    <p className="text-gray-500 dark:text-gray-400">No milestones defined</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {selectedTab === 'content' && (
            <Card>
              <CardHeader>
                <CardTitle>Contract Content</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="prose dark:prose-invert max-w-none">
                  {contract.content ? (
                    <div className="whitespace-pre-wrap text-gray-700 dark:text-gray-300">
                      {contract.content}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <p className="text-gray-500 dark:text-gray-400">No contract content</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Quick Stats */}
          <Card>
            <CardHeader>
              <CardTitle>Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Status</label>
                <div className="mt-1">{getStatusBadge(contract.status)}</div>
              </div>

              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Version</label>
                <p className="text-gray-900 dark:text-white mt-1">v{contract.version}</p>
              </div>

              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Created</label>
                <p className="text-gray-900 dark:text-white mt-1">{formatDate(contract.created_at)}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  by {contract.created_by.first_name} {contract.created_by.last_name}
                </p>
              </div>

              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Last Updated</label>
                <p className="text-gray-900 dark:text-white mt-1">{formatDate(contract.updated_at)}</p>
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" fullWidth onClick={() => {
                contractService.generatePDF(id!).then((blob) => {
                  const url = window.URL.createObjectURL(blob);
                  const link = document.createElement('a');
                  link.href = url;
                  link.download = `contract-${contract.contract_number}.pdf`;
                  document.body.appendChild(link);
                  link.click();
                  document.body.removeChild(link);
                  window.URL.revokeObjectURL(url);
                  showSuccessToast('PDF downloaded');
                }).catch(() => showErrorToast('Failed to download PDF'));
              }}>
                <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
                Download PDF
              </Button>
              <Button variant="outline" fullWidth onClick={() => navigate(`/contracts/create?duplicate=${id}`)}>
                <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Duplicate Contract
              </Button>
              <Button variant="outline" fullWidth onClick={() => navigate(`/invoices/create?contract=${id}`)}>
                <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Create Invoice
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default ContractDetail;
