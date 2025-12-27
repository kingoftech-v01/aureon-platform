/**
 * Payment List Page
 * Aureon by Rhematek Solutions
 *
 * Payment transaction history with Stripe integration
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { paymentService } from '@/services';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Select from '@/components/common/Select';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Table, { TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '@/components/common/Table';
import Pagination from '@/components/common/Pagination';
import Badge from '@/components/common/Badge';
import { SkeletonTable } from '@/components/common/Skeleton';
import type { Payment, PaymentStatus, PaginationConfig, SortConfig } from '@/types';

const PaymentList: React.FC = () => {
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

  // Fetch payments with React Query
  const { data, isLoading, error } = useQuery({
    queryKey: ['payments', pagination, sort, statusFilter, searchQuery],
    queryFn: () =>
      paymentService.getPayments(
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
      showErrorToast('Failed to load payments');
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

  // Payment status badge colors
  const getStatusBadge = (status: PaymentStatus) => {
    const variants: Record<PaymentStatus, 'default' | 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
      pending: 'warning',
      processing: 'info',
      succeeded: 'success',
      failed: 'danger',
      refunded: 'default',
      partially_refunded: 'warning',
      cancelled: 'default',
    };
    return <Badge variant={variants[status]}>{status.replace('_', ' ')}</Badge>;
  };

  // Payment method icon
  const getPaymentMethodIcon = (method: string) => {
    switch (method.toLowerCase()) {
      case 'card':
      case 'credit_card':
        return (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
          </svg>
        );
      case 'bank_transfer':
        return (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z" />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        );
    }
  };

  // Format currency
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Payments</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Payment transaction history and Stripe integration
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline" disabled>
            <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Export
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Received</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                  {data ? formatCurrency(data.results.filter(p => p.status === 'succeeded').reduce((sum, p) => sum + p.amount, 0)) : '$0.00'}
                </p>
              </div>
              <div className="w-12 h-12 bg-green-100 dark:bg-green-900/20 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Pending</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                  {data ? formatCurrency(data.results.filter(p => p.status === 'pending' || p.status === 'processing').reduce((sum, p) => sum + p.amount, 0)) : '$0.00'}
                </p>
              </div>
              <div className="w-12 h-12 bg-yellow-100 dark:bg-yellow-900/20 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-yellow-600 dark:text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Refunded</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                  {data ? formatCurrency(data.results.filter(p => p.status === 'refunded' || p.status === 'partially_refunded').reduce((sum, p) => sum + (p.refund_amount || p.amount), 0)) : '$0.00'}
                </p>
              </div>
              <div className="w-12 h-12 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-gray-600 dark:text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Failed</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                  {data ? data.results.filter(p => p.status === 'failed').length : 0}
                </p>
              </div>
              <div className="w-12 h-12 bg-red-100 dark:bg-red-900/20 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <Input
                type="search"
                placeholder="Search payments by transaction ID, client, or invoice..."
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
                { value: 'pending', label: 'Pending' },
                { value: 'processing', label: 'Processing' },
                { value: 'succeeded', label: 'Succeeded' },
                { value: 'failed', label: 'Failed' },
                { value: 'refunded', label: 'Refunded' },
                { value: 'partially_refunded', label: 'Partially Refunded' },
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

      {/* Payment Table */}
      <Card>
        <CardHeader>
          <CardTitle>
            {data ? `${data.count} Payment${data.count !== 1 ? 's' : ''}` : 'Payments'}
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
                    <TableHeaderCell
                      sortable
                      onSort={() => handleSort('transaction_id')}
                      sortDirection={sort.field === 'transaction_id' ? sort.direction : null}
                    >
                      Transaction ID
                    </TableHeaderCell>
                    <TableHeaderCell>Client</TableHeaderCell>
                    <TableHeaderCell>Invoice</TableHeaderCell>
                    <TableHeaderCell
                      sortable
                      onSort={() => handleSort('amount')}
                      sortDirection={sort.field === 'amount' ? sort.direction : null}
                      align="right"
                    >
                      Amount
                    </TableHeaderCell>
                    <TableHeaderCell>Payment Method</TableHeaderCell>
                    <TableHeaderCell
                      sortable
                      onSort={() => handleSort('status')}
                      sortDirection={sort.field === 'status' ? sort.direction : null}
                    >
                      Status
                    </TableHeaderCell>
                    <TableHeaderCell
                      sortable
                      onSort={() => handleSort('created_at')}
                      sortDirection={sort.field === 'created_at' ? sort.direction : null}
                    >
                      Date
                    </TableHeaderCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.results.map((payment: Payment) => (
                    <TableRow
                      key={payment.id}
                      hoverable
                      onClick={() => navigate(`/payments/${payment.id}`)}
                    >
                      <TableCell>
                        <span className="font-mono text-sm font-medium text-primary-600 dark:text-primary-400">
                          {payment.transaction_id || payment.id.substring(0, 8)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <p className="font-medium text-gray-900 dark:text-white">
                          {payment.client.type === 'individual'
                            ? `${payment.client.first_name} ${payment.client.last_name}`
                            : payment.client.company_name}
                        </p>
                      </TableCell>
                      <TableCell>
                        {payment.invoice ? (
                          <Link
                            to={`/invoices/${payment.invoice.id}`}
                            onClick={(e) => e.stopPropagation()}
                            className="text-primary-600 hover:underline dark:text-primary-400"
                          >
                            {payment.invoice.invoice_number}
                          </Link>
                        ) : (
                          <span className="text-gray-400">—</span>
                        )}
                      </TableCell>
                      <TableCell align="right">
                        <span className="font-medium text-gray-900 dark:text-white">
                          {formatCurrency(payment.amount)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <span className="text-gray-400 dark:text-gray-500">
                            {getPaymentMethodIcon(payment.payment_method)}
                          </span>
                          <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">
                            {payment.payment_method.replace('_', ' ')}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>{getStatusBadge(payment.status)}</TableCell>
                      <TableCell>
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          {formatDateTime(payment.created_at)}
                        </span>
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
                    d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No payments found
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                {searchQuery || statusFilter
                  ? 'Try adjusting your filters'
                  : 'Payment transactions will appear here once received'}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default PaymentList;
