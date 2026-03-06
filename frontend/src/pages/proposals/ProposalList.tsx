/**
 * Proposal List Page
 * Aureon by Rhematek Solutions
 *
 * Proposal management with stats, filters, table, and actions.
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Select from '@/components/common/Select';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Table, { TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '@/components/common/Table';
import Pagination from '@/components/common/Pagination';
import Badge from '@/components/common/Badge';
import Modal, { ModalHeader, ModalBody, ModalFooter } from '@/components/common/Modal';
import { SkeletonTable } from '@/components/common/Skeleton';
import apiClient from '@/services/api';
import { buildQueryParams } from '@/services/api';

type ProposalStatus = 'draft' | 'sent' | 'viewed' | 'accepted' | 'declined' | 'expired';

interface Proposal {
  id: string;
  proposal_number: string;
  title: string;
  client: {
    id: string;
    type: string;
    first_name?: string;
    last_name?: string;
    company_name?: string;
  };
  amount: number;
  status: ProposalStatus;
  sent_date: string | null;
  expiry_date: string | null;
  created_at: string;
}

interface ProposalStats {
  total: number;
  pending: number;
  accepted: number;
  declined: number;
}

const ProposalList: React.FC = () => {
  const navigate = useNavigate();
  const { success: showSuccess, error: showError } = useToast();
  const queryClient = useQueryClient();

  // Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Delete modal state
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);

  // Fetch proposals
  const { data, isLoading, error } = useQuery({
    queryKey: ['proposals', page, pageSize, statusFilter, searchQuery],
    queryFn: async () => {
      const params = buildQueryParams({
        page,
        page_size: pageSize,
        status: statusFilter || undefined,
        search: searchQuery || undefined,
        ordering: '-created_at',
      });
      const response = await apiClient.get(`/contracts/proposals/${params}`);
      return response.data;
    },
  });

  // Fetch proposal stats
  const { data: stats } = useQuery<ProposalStats>({
    queryKey: ['proposal-stats'],
    queryFn: async () => {
      const response = await apiClient.get('/contracts/proposals/stats/');
      return response.data;
    },
  });

  // Delete proposal mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/contracts/proposals/${id}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposals'] });
      queryClient.invalidateQueries({ queryKey: ['proposal-stats'] });
      showSuccess('Proposal deleted successfully');
      setShowDeleteModal(false);
      setDeleteTargetId(null);
    },
    onError: () => {
      showError('Failed to delete proposal');
    },
  });

  // Send proposal mutation
  const sendMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.post(`/contracts/proposals/${id}/send/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposals'] });
      queryClient.invalidateQueries({ queryKey: ['proposal-stats'] });
      showSuccess('Proposal sent successfully');
    },
    onError: () => {
      showError('Failed to send proposal');
    },
  });

  // Convert to contract mutation
  const convertMutation = useMutation({
    mutationFn: async (id: string) => {
      const response = await apiClient.post(`/contracts/proposals/${id}/convert/`);
      return response.data;
    },
    onSuccess: (data) => {
      showSuccess('Proposal converted to contract');
      navigate(`/contracts/${data.id}`);
    },
    onError: () => {
      showError('Failed to convert proposal to contract');
    },
  });

  // Errors
  React.useEffect(() => {
    if (error) showError('Failed to load proposals');
  }, [error, showError]);

  // Format currency
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
  };

  // Format date
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '--';
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // Status badge
  const getStatusBadge = (status: ProposalStatus) => {
    const variants: Record<ProposalStatus, 'default' | 'info' | 'warning' | 'success' | 'danger'> = {
      draft: 'default',
      sent: 'info',
      viewed: 'warning',
      accepted: 'success',
      declined: 'danger',
      expired: 'default',
    };
    return <Badge variant={variants[status]} dot>{status}</Badge>;
  };

  // Client name
  const getClientName = (client: Proposal['client']) => {
    if (client.type === 'individual') {
      return `${client.first_name || ''} ${client.last_name || ''}`.trim();
    }
    return client.company_name || 'Unknown';
  };

  // Stats card component
  const StatCard = ({ label, value, color }: { label: string; value: number; color: string }) => (
    <div className={`rounded-xl p-5 ${color}`}>
      <p className="text-sm font-medium opacity-80">{label}</p>
      <p className="text-3xl font-bold mt-1">{value}</p>
    </div>
  );

  // Handle search
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
  };

  // Handle delete
  const handleDelete = (id: string) => {
    setDeleteTargetId(id);
    setShowDeleteModal(true);
  };

  const proposals: Proposal[] = data?.results || [];
  const totalCount = data?.count || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Proposals</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Create and manage client proposals
          </p>
        </div>
        <Link to="/proposals/create">
          <Button variant="primary" size="lg">
            <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Create Proposal
          </Button>
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Proposals"
          value={stats?.total || 0}
          color="bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300"
        />
        <StatCard
          label="Pending"
          value={stats?.pending || 0}
          color="bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-300"
        />
        <StatCard
          label="Accepted"
          value={stats?.accepted || 0}
          color="bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300"
        />
        <StatCard
          label="Declined"
          value={stats?.declined || 0}
          color="bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300"
        />
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <Input
                type="search"
                placeholder="Search proposals by title, number, or client..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                leftIcon={
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                }
              />
            </div>
            <Select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              options={[
                { value: '', label: 'All Statuses' },
                { value: 'draft', label: 'Draft' },
                { value: 'sent', label: 'Sent' },
                { value: 'viewed', label: 'Viewed' },
                { value: 'accepted', label: 'Accepted' },
                { value: 'declined', label: 'Declined' },
                { value: 'expired', label: 'Expired' },
              ]}
              className="w-48"
            />
            <Button type="submit" variant="outline">
              Search
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Proposals Table */}
      <Card>
        <CardHeader>
          <CardTitle>
            {totalCount > 0 ? `${totalCount} Proposal${totalCount !== 1 ? 's' : ''}` : 'Proposals'}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6">
              <SkeletonTable rows={5} columns={7} />
            </div>
          ) : proposals.length > 0 ? (
            <>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableHeaderCell>#</TableHeaderCell>
                    <TableHeaderCell>Title</TableHeaderCell>
                    <TableHeaderCell>Client</TableHeaderCell>
                    <TableHeaderCell align="right">Amount</TableHeaderCell>
                    <TableHeaderCell>Status</TableHeaderCell>
                    <TableHeaderCell>Sent Date</TableHeaderCell>
                    <TableHeaderCell>Expiry</TableHeaderCell>
                    <TableHeaderCell align="right">Actions</TableHeaderCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {proposals.map((proposal) => (
                    <TableRow key={proposal.id} hoverable>
                      <TableCell>
                        <span className="font-mono text-sm font-medium text-primary-600 dark:text-primary-400">
                          {proposal.proposal_number}
                        </span>
                      </TableCell>
                      <TableCell>
                        <p className="font-medium text-gray-900 dark:text-white">{proposal.title}</p>
                      </TableCell>
                      <TableCell>
                        <span className="text-gray-700 dark:text-gray-300">
                          {getClientName(proposal.client)}
                        </span>
                      </TableCell>
                      <TableCell align="right">
                        <span className="font-medium text-gray-900 dark:text-white">
                          {formatCurrency(proposal.amount)}
                        </span>
                      </TableCell>
                      <TableCell>{getStatusBadge(proposal.status)}</TableCell>
                      <TableCell>
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          {formatDate(proposal.sent_date)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          {formatDate(proposal.expiry_date)}
                        </span>
                      </TableCell>
                      <TableCell align="right">
                        <div className="flex items-center justify-end space-x-1">
                          {/* View */}
                          <button
                            onClick={() => navigate(`/proposals/${proposal.id}`)}
                            className="p-1.5 text-gray-400 hover:text-primary-500 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                            title="View"
                          >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                          </button>
                          {/* Edit */}
                          {proposal.status === 'draft' && (
                            <button
                              onClick={() => navigate(`/proposals/${proposal.id}/edit`)}
                              className="p-1.5 text-gray-400 hover:text-primary-500 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                              title="Edit"
                            >
                              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                              </svg>
                            </button>
                          )}
                          {/* Send */}
                          {proposal.status === 'draft' && (
                            <button
                              onClick={() => sendMutation.mutate(proposal.id)}
                              className="p-1.5 text-gray-400 hover:text-blue-500 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                              title="Send"
                            >
                              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                              </svg>
                            </button>
                          )}
                          {/* Convert to Contract */}
                          {proposal.status === 'accepted' && (
                            <button
                              onClick={() => convertMutation.mutate(proposal.id)}
                              className="p-1.5 text-gray-400 hover:text-green-500 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                              title="Convert to Contract"
                            >
                              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                              </svg>
                            </button>
                          )}
                          {/* Delete */}
                          <button
                            onClick={() => handleDelete(proposal.id)}
                            className="p-1.5 text-gray-400 hover:text-red-500 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                            title="Delete"
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

              {/* Pagination */}
              <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                <Pagination
                  currentPage={page}
                  totalPages={Math.ceil(totalCount / pageSize)}
                  onPageChange={setPage}
                  pageSize={pageSize}
                  totalItems={totalCount}
                  onPageSizeChange={(size) => { setPageSize(size); setPage(1); }}
                />
              </div>
            </>
          ) : (
            <div className="p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No proposals found
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                {searchQuery || statusFilter
                  ? 'Try adjusting your filters'
                  : 'Create your first proposal to get started'}
              </p>
              <Link to="/proposals/create">
                <Button variant="primary">Create Your First Proposal</Button>
              </Link>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Modal */}
      <Modal isOpen={showDeleteModal} onClose={() => setShowDeleteModal(false)} size="sm">
        <ModalHeader>Delete Proposal</ModalHeader>
        <ModalBody>
          <p className="text-gray-600 dark:text-gray-400">
            Are you sure you want to delete this proposal? This action cannot be undone.
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
            Delete
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
};

export default ProposalList;
