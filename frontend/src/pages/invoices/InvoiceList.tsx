/**
 * Invoice List Page
 * Aureon by Rhematek Solutions
 *
 * Main invoice management page with table, search, filters, and bulk actions
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { invoiceService } from '@/services';
import apiClient from '@/services/api';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Select from '@/components/common/Select';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Table, { TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '@/components/common/Table';
import Pagination from '@/components/common/Pagination';
import Badge from '@/components/common/Badge';
import { SkeletonTable } from '@/components/common/Skeleton';
import type { Invoice, InvoiceStatus, PaginationConfig, SortConfig } from '@/types';

const InvoiceList: React.FC = () => {
  const navigate = useNavigate();
  const queryClientInstance = useQueryClient();
  const { success: showSuccess, error: showErrorToast } = useToast();

  // State for filters, pagination, and sorting
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [pagination, setPagination] = useState<PaginationConfig>({
    page: 1,
    pageSize: 10,
  });
  const [sort, setSort] = useState<SortConfig>({
    field: 'created_at',
    direction: 'desc',
  });

  // Bulk selection state
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // Fetch invoices with React Query
  const { data, isLoading, error } = useQuery({
    queryKey: ['invoices', pagination, sort, statusFilter, searchQuery],
    queryFn: () =>
      invoiceService.getInvoices(
        pagination,
        {
          status: statusFilter || undefined,
          search: searchQuery || undefined,
        },
        sort
      ),
  });

  // Bulk action mutation
  const bulkActionMutation = useMutation({
    mutationFn: ({ action, invoice_ids }: { action: string; invoice_ids: string[] }) =>
      apiClient.post('/analytics/bulk/invoices/', { action, invoice_ids }),
    onSuccess: (_data, variables) => {
      queryClientInstance.invalidateQueries({ queryKey: ['invoices'] });
      setSelectedIds(new Set());
      const actionLabels: Record<string, string> = {
        send: 'sent',
        mark_paid: 'marked as paid',
        cancel: 'cancelled',
        delete: 'deleted',
      };
      showSuccess(`${variables.invoice_ids.length} invoice(s) ${actionLabels[variables.action] || 'updated'} successfully`);
    },
    onError: () => {
      showErrorToast('Bulk action failed. Please try again.');
    },
  });

  // Handle errors
  React.useEffect(() => {
    if (error) {
      showErrorToast('Failed to load invoices');
    }
  }, [error, showErrorToast]);

  // Handle sorting
  const handleSort = (field: string) => {
    setSort((prev) => ({
      field,
      direction: prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  // Handle search
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPagination((prev) => ({ ...prev, page: 1 }));
  };

  // Bulk selection handlers
  const allInvoiceIds = data?.results?.map((inv: Invoice) => inv.id) || [];
  const allSelected = allInvoiceIds.length > 0 && allInvoiceIds.every((id: string) => selectedIds.has(id));
  const someSelected = selectedIds.size > 0;

  const handleSelectAll = () => {
    if (allSelected) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(allInvoiceIds));
    }
  };

  const handleSelectOne = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleBulkAction = (action: string) => {
    if (selectedIds.size === 0) return;
    bulkActionMutation.mutate({
      action,
      invoice_ids: Array.from(selectedIds),
    });
  };

  // Invoice status badge colors
  const getStatusBadge = (status: InvoiceStatus) => {
    const variants: Record<InvoiceStatus, 'default' | 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
      draft: 'default',
      sent: 'info',
      viewed: 'primary',
      paid: 'success',
      partially_paid: 'warning',
      overdue: 'danger',
      cancelled: 'default',
    };
    return <Badge variant={variants[status]}>{status.replace('_', ' ')}</Badge>;
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
      month: 'short',
      day: 'numeric',
    });
  };

  // Check if invoice is overdue
  const isOverdue = (invoice: Invoice) => {
    if (invoice.status === 'paid' || invoice.status === 'cancelled') {
      return false;
    }
    return new Date(invoice.due_date) < new Date();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Invoices</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Manage client invoices and billing
          </p>
        </div>
        <Link to="/invoices/create">
          <Button variant="primary" size="lg">
            <svg
              className="w-5 h-5 mr-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 6v6m0 0v6m0-6h6m-6 0H6"
              />
            </svg>
            New Invoice
          </Button>
        </Link>
      </div>

      {/* Bulk Actions Bar */}
      {someSelected && (
        <div className="bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800 rounded-lg p-4 flex items-center justify-between animate-fade-in">
          <span className="text-sm font-medium text-primary-700 dark:text-primary-300">
            {selectedIds.size} invoice{selectedIds.size !== 1 ? 's' : ''} selected
          </span>
          <div className="flex items-center space-x-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleBulkAction('send')}
              disabled={bulkActionMutation.isPending}
            >
              <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              Send All
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleBulkAction('mark_paid')}
              disabled={bulkActionMutation.isPending}
            >
              <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Mark Paid
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleBulkAction('cancel')}
              disabled={bulkActionMutation.isPending}
            >
              <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
              </svg>
              Cancel
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleBulkAction('delete')}
              disabled={bulkActionMutation.isPending}
              className="text-red-600 hover:text-red-700 border-red-300 hover:border-red-400"
            >
              <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Delete
            </Button>
            <button
              onClick={() => setSelectedIds(new Set())}
              className="ml-2 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              title="Clear selection"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <Input
                type="search"
                placeholder="Search invoices by number, client, or amount..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                leftIcon={
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    />
                  </svg>
                }
              />
            </div>

            {/* Status Filter */}
            <Select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPagination((prev) => ({ ...prev, page: 1 }));
              }}
              options={[
                { value: '', label: 'All Statuses' },
                { value: 'draft', label: 'Draft' },
                { value: 'sent', label: 'Sent' },
                { value: 'viewed', label: 'Viewed' },
                { value: 'paid', label: 'Paid' },
                { value: 'partially_paid', label: 'Partially Paid' },
                { value: 'overdue', label: 'Overdue' },
                { value: 'cancelled', label: 'Cancelled' },
              ]}
              className="w-48"
            />

            {/* Search Button */}
            <Button type="submit" variant="outline">
              Search
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Invoice Table */}
      <Card>
        <CardHeader>
          <CardTitle>
            {data ? `${data.count} Invoice${data.count !== 1 ? 's' : ''}` : 'Invoices'}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6">
              <SkeletonTable rows={5} columns={7} />
            </div>
          ) : data && data.results.length > 0 ? (
            <>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableHeaderCell>
                      <input
                        type="checkbox"
                        checked={allSelected}
                        onChange={handleSelectAll}
                        className="h-4 w-4 rounded border-gray-300 dark:border-gray-600 text-primary-600 focus:ring-primary-500 cursor-pointer"
                        aria-label="Select all invoices"
                      />
                    </TableHeaderCell>
                    <TableHeaderCell
                      sortable
                      onSort={() => handleSort('invoice_number')}
                      sortDirection={sort.field === 'invoice_number' ? sort.direction : null}
                    >
                      Invoice #
                    </TableHeaderCell>
                    <TableHeaderCell>Client</TableHeaderCell>
                    <TableHeaderCell
                      sortable
                      onSort={() => handleSort('status')}
                      sortDirection={sort.field === 'status' ? sort.direction : null}
                    >
                      Status
                    </TableHeaderCell>
                    <TableHeaderCell
                      sortable
                      onSort={() => handleSort('issue_date')}
                      sortDirection={sort.field === 'issue_date' ? sort.direction : null}
                    >
                      Issue Date
                    </TableHeaderCell>
                    <TableHeaderCell
                      sortable
                      onSort={() => handleSort('due_date')}
                      sortDirection={sort.field === 'due_date' ? sort.direction : null}
                    >
                      Due Date
                    </TableHeaderCell>
                    <TableHeaderCell
                      sortable
                      onSort={() => handleSort('total')}
                      sortDirection={sort.field === 'total' ? sort.direction : null}
                      align="right"
                    >
                      Total
                    </TableHeaderCell>
                    <TableHeaderCell align="right">Actions</TableHeaderCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.results.map((invoice: Invoice) => (
                    <TableRow
                      key={invoice.id}
                      hoverable
                      onClick={() => navigate(`/invoices/${invoice.id}`)}
                      className={selectedIds.has(invoice.id) ? 'bg-primary-50 dark:bg-primary-900/10' : ''}
                    >
                      <TableCell>
                        <input
                          type="checkbox"
                          checked={selectedIds.has(invoice.id)}
                          onChange={(e) => {
                            e.stopPropagation();
                            handleSelectOne(invoice.id);
                          }}
                          onClick={(e) => e.stopPropagation()}
                          className="h-4 w-4 rounded border-gray-300 dark:border-gray-600 text-primary-600 focus:ring-primary-500 cursor-pointer"
                          aria-label={`Select invoice ${invoice.invoice_number}`}
                        />
                      </TableCell>
                      <TableCell>
                        <span className="font-mono text-sm font-medium text-primary-600 dark:text-primary-400">
                          {invoice.invoice_number}
                        </span>
                      </TableCell>
                      <TableCell>
                        <p className="font-medium text-gray-900 dark:text-white">
                          {invoice.client.type === 'individual'
                            ? `${invoice.client.first_name} ${invoice.client.last_name}`
                            : invoice.client.company_name}
                        </p>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          {getStatusBadge(invoice.status)}
                          {isOverdue(invoice) && invoice.status !== 'overdue' && (
                            <Badge variant="danger">Overdue</Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          {formatDate(invoice.issue_date)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className={`text-sm ${isOverdue(invoice) ? 'text-red-600 dark:text-red-400 font-medium' : 'text-gray-600 dark:text-gray-400'}`}>
                          {formatDate(invoice.due_date)}
                        </span>
                      </TableCell>
                      <TableCell align="right">
                        <span className="font-medium text-gray-900 dark:text-white">
                          {formatCurrency(invoice.total)}
                        </span>
                      </TableCell>
                      <TableCell align="right">
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/invoices/${invoice.id}/edit`);
                            }}
                            className="p-1 text-gray-400 hover:text-primary-500 transition-colors"
                            title="Edit invoice"
                          >
                            <svg
                              className="w-5 h-5"
                              fill="none"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                              />
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
                  currentPage={pagination.page}
                  totalPages={Math.ceil((data.count || 0) / pagination.pageSize)}
                  onPageChange={(page) => setPagination((prev) => ({ ...prev, page }))}
                  pageSize={pagination.pageSize}
                  totalItems={data.count}
                  onPageSizeChange={(pageSize) =>
                    setPagination({ page: 1, pageSize })
                  }
                />
              </div>
            </>
          ) : (
            <div className="p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-8 h-8 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No invoices found
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                {searchQuery || statusFilter
                  ? 'Try adjusting your filters'
                  : 'Get started by creating your first invoice'}
              </p>
              <Link to="/invoices/create">
                <Button variant="primary">Create Your First Invoice</Button>
              </Link>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default InvoiceList;
