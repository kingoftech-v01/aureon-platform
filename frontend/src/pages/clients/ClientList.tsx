/**
 * Client List Page
 * Aureon by Rhematek Solutions
 *
 * Main client management page with table, search, and filters
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { clientService } from '@/services';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Select from '@/components/common/Select';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Table, { TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '@/components/common/Table';
import Pagination from '@/components/common/Pagination';
import Badge from '@/components/common/Badge';
import Avatar from '@/components/common/Avatar';
import { SkeletonTable } from '@/components/common/Skeleton';
import type { Client, LifecycleStage, PaginationConfig, SortConfig } from '@/types';

const ClientList: React.FC = () => {
  const navigate = useNavigate();
  const { error: showErrorToast } = useToast();

  // State for filters, pagination, and sorting
  const [searchQuery, setSearchQuery] = useState('');
  const [lifecycleFilter, setLifecycleFilter] = useState<string>('');
  const [pagination, setPagination] = useState<PaginationConfig>({
    page: 1,
    pageSize: 10,
  });
  const [sort, setSort] = useState<SortConfig>({
    field: 'created_at',
    direction: 'desc',
  });

  // Fetch clients with React Query
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['clients', pagination, sort, lifecycleFilter, searchQuery],
    queryFn: () =>
      clientService.getClients(
        pagination,
        {
          lifecycle_stage: lifecycleFilter || undefined,
          search: searchQuery || undefined,
        },
        sort
      ),
  });

  // Handle errors
  React.useEffect(() => {
    if (error) {
      showErrorToast('Failed to load clients');
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

  // Lifecycle stage badge colors
  const getLifecycleBadge = (stage: LifecycleStage) => {
    const variants: Record<LifecycleStage, 'default' | 'primary' | 'success' | 'warning' | 'info'> = {
      lead: 'info',
      prospect: 'primary',
      customer: 'success',
      inactive: 'warning',
    };
    return <Badge variant={variants[stage]}>{stage}</Badge>;
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Clients</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Manage your client relationships
          </p>
        </div>
        <Link to="/clients/create">
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
            Add Client
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
                placeholder="Search clients by name, email, or company..."
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

            {/* Lifecycle Filter */}
            <Select
              value={lifecycleFilter}
              onChange={(e) => {
                setLifecycleFilter(e.target.value);
                setPagination((prev) => ({ ...prev, page: 1 }));
              }}
              options={[
                { value: '', label: 'All Stages' },
                { value: 'lead', label: 'Lead' },
                { value: 'prospect', label: 'Prospect' },
                { value: 'customer', label: 'Customer' },
                { value: 'inactive', label: 'Inactive' },
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

      {/* Client Table */}
      <Card>
        <CardHeader>
          <CardTitle>
            {data ? `${data.count} Client${data.count !== 1 ? 's' : ''}` : 'Clients'}
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
                    <TableHeaderCell>Client</TableHeaderCell>
                    <TableHeaderCell
                      sortable
                      onSort={() => handleSort('lifecycle_stage')}
                      sortDirection={sort.field === 'lifecycle_stage' ? sort.direction : null}
                    >
                      Stage
                    </TableHeaderCell>
                    <TableHeaderCell>Contact</TableHeaderCell>
                    <TableHeaderCell
                      sortable
                      onSort={() => handleSort('total_revenue')}
                      sortDirection={sort.field === 'total_revenue' ? sort.direction : null}
                      align="right"
                    >
                      Revenue
                    </TableHeaderCell>
                    <TableHeaderCell
                      sortable
                      onSort={() => handleSort('created_at')}
                      sortDirection={sort.field === 'created_at' ? sort.direction : null}
                    >
                      Added
                    </TableHeaderCell>
                    <TableHeaderCell align="right">Actions</TableHeaderCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.results.map((client: Client) => (
                    <TableRow
                      key={client.id}
                      hoverable
                      onClick={() => navigate(`/clients/${client.id}`)}
                    >
                      <TableCell>
                        <div className="flex items-center space-x-3">
                          <Avatar
                            name={
                              client.type === 'individual'
                                ? `${client.first_name} ${client.last_name}`
                                : client.company_name || 'Company'
                            }
                            size="sm"
                          />
                          <div>
                            <p className="font-medium text-gray-900 dark:text-white">
                              {client.type === 'individual'
                                ? `${client.first_name} ${client.last_name}`
                                : client.company_name}
                            </p>
                            {client.type === 'company' && client.contact_person && (
                              <p className="text-sm text-gray-500 dark:text-gray-400">
                                {client.contact_person}
                              </p>
                            )}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>{getLifecycleBadge(client.lifecycle_stage)}</TableCell>
                      <TableCell>
                        <div className="text-sm">
                          <p className="text-gray-900 dark:text-white">{client.email}</p>
                          {client.phone && (
                            <p className="text-gray-500 dark:text-gray-400">{client.phone}</p>
                          )}
                        </div>
                      </TableCell>
                      <TableCell align="right">
                        <span className="font-medium text-gray-900 dark:text-white">
                          {formatCurrency(client.total_revenue || 0)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          {formatDate(client.created_at)}
                        </span>
                      </TableCell>
                      <TableCell align="right">
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/clients/${client.id}/edit`);
                            }}
                            className="p-1 text-gray-400 hover:text-primary-500 transition-colors"
                            title="Edit client"
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
                    d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No clients found
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                {searchQuery || lifecycleFilter
                  ? 'Try adjusting your filters'
                  : 'Get started by adding your first client'}
              </p>
              <Link to="/clients/create">
                <Button variant="primary">Add Your First Client</Button>
              </Link>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ClientList;
