/**
 * Invoice List Page
 * Aureon by Rhematek Solutions
 *
 * Main invoice management page with table, search, and filters
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { invoiceService } from '@/services';
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
  const { error: showErrorToast } = useToast();

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
              <SkeletonTable rows={5} columns={6} />
            </div>
          ) : data && data.results.length > 0 ? (
            <>
              <Table>
                <TableHead>
                  <TableRow>
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
                    >
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
