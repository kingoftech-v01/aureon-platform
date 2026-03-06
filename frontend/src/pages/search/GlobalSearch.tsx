/**
 * Global Search Results Page
 * Aureon by Rhematek Solutions
 *
 * Full search results page with tabs for All, Clients, Invoices, Contracts, Payments
 */

import React, { useState, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { clientService, invoiceService, contractService, paymentService } from '@/services';
import Card, { CardContent } from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import { SkeletonTable } from '@/components/common/Skeleton';
import type { Client, Invoice, Contract, Payment, InvoiceStatus, ContractStatus, PaymentStatus } from '@/types';

type SearchTab = 'all' | 'clients' | 'invoices' | 'contracts' | 'payments';

const GlobalSearch: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const query = searchParams.get('q') || '';
  const [activeTab, setActiveTab] = useState<SearchTab>('all');

  // Search clients
  const {
    data: clientsData,
    isLoading: clientsLoading,
  } = useQuery({
    queryKey: ['search-clients', query],
    queryFn: () =>
      clientService.getClients(
        { page: 1, pageSize: 10 },
        { search: query }
      ),
    enabled: !!query,
  });

  // Search invoices
  const {
    data: invoicesData,
    isLoading: invoicesLoading,
  } = useQuery({
    queryKey: ['search-invoices', query],
    queryFn: () =>
      invoiceService.getInvoices(
        { page: 1, pageSize: 10 },
        { search: query }
      ),
    enabled: !!query,
  });

  // Search contracts
  const {
    data: contractsData,
    isLoading: contractsLoading,
  } = useQuery({
    queryKey: ['search-contracts', query],
    queryFn: () =>
      contractService.getContracts(
        { page: 1, pageSize: 10 },
        { search: query }
      ),
    enabled: !!query,
  });

  // Search payments
  const {
    data: paymentsData,
    isLoading: paymentsLoading,
  } = useQuery({
    queryKey: ['search-payments', query],
    queryFn: () =>
      paymentService.getPayments(
        { page: 1, pageSize: 10 },
        { search: query }
      ),
    enabled: !!query,
  });

  const isLoading = clientsLoading || invoicesLoading || contractsLoading || paymentsLoading;

  // Counts for tabs
  const counts = useMemo(() => ({
    clients: clientsData?.results?.length || 0,
    invoices: invoicesData?.results?.length || 0,
    contracts: contractsData?.results?.length || 0,
    payments: paymentsData?.results?.length || 0,
  }), [clientsData, invoicesData, contractsData, paymentsData]);

  const totalCount = counts.clients + counts.invoices + counts.contracts + counts.payments;

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

  // Get client name
  const getClientName = (client: Client) => {
    if (client.type === 'individual') {
      return `${client.first_name} ${client.last_name}`;
    }
    return client.company_name || '';
  };

  // Invoice status badge
  const getInvoiceStatusBadge = (status: InvoiceStatus) => {
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

  // Contract status badge
  const getContractStatusBadge = (status: ContractStatus) => {
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
    return <Badge variant={variants[status]}>{status.replace('_', ' ')}</Badge>;
  };

  // Payment status badge
  const getPaymentStatusBadge = (status: PaymentStatus) => {
    const variants: Record<PaymentStatus, 'default' | 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
      pending: 'warning',
      processing: 'info',
      succeeded: 'success',
      failed: 'danger',
      cancelled: 'default',
      refunded: 'default',
      partially_refunded: 'warning',
    };
    return <Badge variant={variants[status]}>{status.replace('_', ' ')}</Badge>;
  };

  // Tab definitions
  const tabs: { key: SearchTab; label: string; count: number }[] = [
    { key: 'all', label: 'All', count: totalCount },
    { key: 'clients', label: 'Clients', count: counts.clients },
    { key: 'invoices', label: 'Invoices', count: counts.invoices },
    { key: 'contracts', label: 'Contracts', count: counts.contracts },
    { key: 'payments', label: 'Payments', count: counts.payments },
  ];

  // Render client results
  const renderClients = () => {
    if (!clientsData?.results?.length) return null;
    return (
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
          <svg className="w-5 h-5 mr-2 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          Clients ({counts.clients})
        </h3>
        <div className="space-y-2">
          {clientsData.results.map((client: Client) => (
            <Card key={client.id}>
              <CardContent className="p-4">
                <button
                  onClick={() => navigate(`/clients/${client.id}`)}
                  className="w-full text-left flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700/50 -m-4 p-4 rounded-lg transition-colors"
                >
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {getClientName(client)}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {client.email}
                    </p>
                  </div>
                  <div className="flex items-center space-x-3">
                    <Badge variant="info">{client.lifecycle_stage}</Badge>
                    <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  };

  // Render invoice results
  const renderInvoices = () => {
    if (!invoicesData?.results?.length) return null;
    return (
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
          <svg className="w-5 h-5 mr-2 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Invoices ({counts.invoices})
        </h3>
        <div className="space-y-2">
          {invoicesData.results.map((invoice: Invoice) => (
            <Card key={invoice.id}>
              <CardContent className="p-4">
                <button
                  onClick={() => navigate(`/invoices/${invoice.id}`)}
                  className="w-full text-left flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700/50 -m-4 p-4 rounded-lg transition-colors"
                >
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      <span className="font-mono text-primary-600 dark:text-primary-400 mr-2">
                        {invoice.invoice_number}
                      </span>
                      {getClientName(invoice.client)}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Due {formatDate(invoice.due_date)} &middot; {formatCurrency(invoice.total)}
                    </p>
                  </div>
                  <div className="flex items-center space-x-3">
                    {getInvoiceStatusBadge(invoice.status)}
                    <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  };

  // Render contract results
  const renderContracts = () => {
    if (!contractsData?.results?.length) return null;
    return (
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
          <svg className="w-5 h-5 mr-2 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Contracts ({counts.contracts})
        </h3>
        <div className="space-y-2">
          {contractsData.results.map((contract: Contract) => (
            <Card key={contract.id}>
              <CardContent className="p-4">
                <button
                  onClick={() => navigate(`/contracts/${contract.id}`)}
                  className="w-full text-left flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700/50 -m-4 p-4 rounded-lg transition-colors"
                >
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      <span className="font-mono text-primary-600 dark:text-primary-400 mr-2">
                        {contract.contract_number}
                      </span>
                      {contract.title}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {getClientName(contract.client)} &middot; {formatCurrency(contract.total_value)}
                    </p>
                  </div>
                  <div className="flex items-center space-x-3">
                    {getContractStatusBadge(contract.status)}
                    <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  };

  // Render payment results
  const renderPayments = () => {
    if (!paymentsData?.results?.length) return null;
    return (
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
          <svg className="w-5 h-5 mr-2 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          Payments ({counts.payments})
        </h3>
        <div className="space-y-2">
          {paymentsData.results.map((payment: Payment) => (
            <Card key={payment.id}>
              <CardContent className="p-4">
                <button
                  onClick={() => navigate(`/payments/${payment.id}`)}
                  className="w-full text-left flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700/50 -m-4 p-4 rounded-lg transition-colors"
                >
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      <span className="font-mono text-primary-600 dark:text-primary-400 mr-2">
                        {payment.payment_number}
                      </span>
                      {formatCurrency(payment.amount)}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Invoice {payment.invoice?.invoice_number} &middot; {formatDate(payment.created_at)}
                    </p>
                  </div>
                  <div className="flex items-center space-x-3">
                    {getPaymentStatusBadge(payment.status)}
                    <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  };

  // Render empty state
  const renderEmptyState = () => (
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
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </div>
      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
        {query ? 'No results found' : 'Search for anything'}
      </h3>
      <p className="text-gray-600 dark:text-gray-400">
        {query
          ? `No results matched "${query}". Try a different search term.`
          : 'Enter a search term to find clients, invoices, contracts, and payments.'}
      </p>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Search Results</h1>
        {query && (
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            {isLoading
              ? 'Searching...'
              : `${totalCount} result${totalCount !== 1 ? 's' : ''} for "${query}"`}
          </p>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex space-x-8" aria-label="Search result tabs">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`py-3 px-1 border-b-2 font-medium text-sm whitespace-nowrap transition-colors ${
                activeTab === tab.key
                  ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              {tab.label}
              {!isLoading && (
                <span
                  className={`ml-2 px-2 py-0.5 rounded-full text-xs ${
                    activeTab === tab.key
                      ? 'bg-primary-100 text-primary-600 dark:bg-primary-900/30 dark:text-primary-400'
                      : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                  }`}
                >
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Results */}
      {isLoading ? (
        <Card>
          <CardContent className="p-6">
            <SkeletonTable rows={5} columns={4} />
          </CardContent>
        </Card>
      ) : !query || totalCount === 0 ? (
        <Card>
          <CardContent className="p-0">
            {renderEmptyState()}
          </CardContent>
        </Card>
      ) : (
        <div>
          {(activeTab === 'all' || activeTab === 'clients') && renderClients()}
          {(activeTab === 'all' || activeTab === 'invoices') && renderInvoices()}
          {(activeTab === 'all' || activeTab === 'contracts') && renderContracts()}
          {(activeTab === 'all' || activeTab === 'payments') && renderPayments()}
        </div>
      )}
    </div>
  );
};

export default GlobalSearch;
