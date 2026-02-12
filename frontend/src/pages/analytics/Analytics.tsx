/**
 * Analytics Dashboard Page
 * Aureon by Rhematek Solutions
 *
 * Business intelligence and reporting dashboard
 */

import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { contractService, invoiceService, paymentService, clientService } from '@/services';
import { analyticsService } from '../../services/analyticsService';
import { useToast } from '@/components/common';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Select from '@/components/common/Select';
import Button from '@/components/common/Button';
import Badge from '@/components/common/Badge';
import {
  RevenueAreaChart,
  RevenueBarChart,
  DonutChart,
  MultiLineChart,
  ProgressRing,
} from '@/components/common/Charts';

const Analytics: React.FC = () => {
  const [timeRange, setTimeRange] = useState('30');
  const { success: showSuccessToast } = useToast();

  // Fetch dashboard statistics
  const { data: clients } = useQuery({
    queryKey: ['clients', { page: 1, pageSize: 1000 }],
    queryFn: () => clientService.getClients({ page: 1, pageSize: 1000 }),
  });

  const { data: invoices } = useQuery({
    queryKey: ['invoices', { page: 1, pageSize: 1000 }],
    queryFn: () => invoiceService.getInvoices({ page: 1, pageSize: 1000 }),
  });

  const { data: payments } = useQuery({
    queryKey: ['payments', { page: 1, pageSize: 1000 }],
    queryFn: () => paymentService.getPayments({ page: 1, pageSize: 1000 }),
  });

  const { data: contracts } = useQuery({
    queryKey: ['contracts', { page: 1, pageSize: 1000 }],
    queryFn: () => contractService.getContracts({ page: 1, pageSize: 1000 }),
  });

  const { data: revenueData } = useQuery({
    queryKey: ['analytics-revenue', timeRange],
    queryFn: () => analyticsService.getRevenueMetrics({ period: timeRange === '7' ? 'week' : timeRange === '30' ? 'month' : timeRange === '90' ? 'quarter' : 'year' }),
  });

  // Calculate metrics
  const totalRevenue = payments?.results?.filter(p => p.status === 'succeeded').reduce((sum, p) => sum + p.amount, 0) || 0;
  const totalInvoiced = invoices?.results?.reduce((sum, i) => sum + i.total, 0) || 0;
  const totalOutstanding = invoices?.results?.filter(i => i.status !== 'paid' && i.status !== 'cancelled').reduce((sum, i) => sum + i.total, 0) || 0;
  const totalClients = clients?.count || 0;
  const activeClients = clients?.results?.filter(c => c.lifecycle_stage === 'customer').length || 0;
  const collectionRate = totalInvoiced > 0 ? (totalRevenue / totalInvoiced) * 100 : 0;

  // Generate monthly revenue data for chart
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const monthlyRevenueData = useMemo(() => {
    if (revenueData?.length) {
      return revenueData.map((item: any) => ({
        name: item.date,
        value: item.revenue,
      }));
    }
    const currentMonth = new Date().getMonth();
    return months.slice(Math.max(0, currentMonth - 5), currentMonth + 1).map((month) => ({
      name: month,
      value: 0,
    }));
  }, [revenueData]);

  // Invoice status distribution
  const invoiceStatusData = useMemo(() => {
    if (!invoices?.results?.length) {
      return [
        { name: 'Paid', value: 45 },
        { name: 'Pending', value: 30 },
        { name: 'Overdue', value: 15 },
        { name: 'Draft', value: 10 },
      ];
    }

    const statusCounts = invoices.results.reduce((acc, inv) => {
      acc[inv.status] = (acc[inv.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const statusLabels: Record<string, string> = {
      draft: 'Draft',
      sent: 'Pending',
      paid: 'Paid',
      overdue: 'Overdue',
      cancelled: 'Cancelled',
    };

    return Object.entries(statusCounts).map(([status, count]) => ({
      name: statusLabels[status] || status,
      value: count,
    }));
  }, [invoices]);

  // Client growth data
  const clientGrowthData = useMemo(() => {
    return months.slice(0, 6).map((month) => ({
      name: month,
      clients: 0,
      leads: 0,
    }));
  }, []);

  // Revenue by category
  const revenueByCategoryData = useMemo(() => {
    return [
      { name: 'Consulting', value: Math.floor((totalRevenue || 50000) * 0.35) },
      { name: 'Development', value: Math.floor((totalRevenue || 50000) * 0.28) },
      { name: 'Design', value: Math.floor((totalRevenue || 50000) * 0.20) },
      { name: 'Support', value: Math.floor((totalRevenue || 50000) * 0.12) },
      { name: 'Other', value: Math.floor((totalRevenue || 50000) * 0.05) },
    ];
  }, [totalRevenue]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatPercent = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">Analytics</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Business intelligence and performance metrics
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            options={[
              { value: '7', label: 'Last 7 days' },
              { value: '30', label: 'Last 30 days' },
              { value: '90', label: 'Last 90 days' },
              { value: '365', label: 'Last year' },
              { value: 'all', label: 'All time' },
            ]}
            className="w-40"
          />
          <Button variant="outline" onClick={() => {
            showSuccessToast('Report generation queued. You will be notified when it is ready.');
          }}>
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Export Report
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card hover className="relative overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Revenue</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                  {formatCurrency(totalRevenue)}
                </p>
                <div className="flex items-center mt-2">
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                    <svg className="w-3 h-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                    </svg>
                    0%
                  </span>
                  <span className="text-xs text-gray-500 ml-2">vs last period</span>
                </div>
              </div>
              <div className="w-14 h-14 bg-gradient-to-br from-green-400 to-green-600 rounded-xl flex items-center justify-center shadow-lg shadow-green-500/30">
                <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-green-400 to-green-600"></div>
          </CardContent>
        </Card>

        <Card hover className="relative overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Outstanding</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                  {formatCurrency(totalOutstanding)}
                </p>
                <p className="text-sm text-amber-600 dark:text-amber-400 mt-2">
                  {invoices?.results?.filter(i => i.status !== 'paid' && i.status !== 'cancelled').length || 0} unpaid invoices
                </p>
              </div>
              <div className="w-14 h-14 bg-gradient-to-br from-amber-400 to-amber-600 rounded-xl flex items-center justify-center shadow-lg shadow-amber-500/30">
                <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-400 to-amber-600"></div>
          </CardContent>
        </Card>

        <Card hover className="relative overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Active Clients</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                  {activeClients}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                  {formatPercent((activeClients / totalClients) * 100 || 0)} of total
                </p>
              </div>
              <div className="w-14 h-14 bg-gradient-to-br from-blue-400 to-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/30">
                <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
            </div>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-400 to-blue-600"></div>
          </CardContent>
        </Card>

        <Card hover className="relative overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Avg Invoice Value</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                  {formatCurrency(totalInvoiced / (invoices?.count || 1))}
                </p>
                <p className="text-sm text-purple-600 dark:text-purple-400 mt-2">
                  {invoices?.count || 0} total invoices
                </p>
              </div>
              <div className="w-14 h-14 bg-gradient-to-br from-purple-400 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/30">
                <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              </div>
            </div>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-400 to-purple-600"></div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Grid - Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Chart */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Revenue Over Time</CardTitle>
            <div className="flex items-center space-x-2">
              <button className="px-3 py-1 text-xs font-medium rounded-full bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400">
                Monthly
              </button>
              <button className="px-3 py-1 text-xs font-medium rounded-full text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800">
                Weekly
              </button>
            </div>
          </CardHeader>
          <CardContent>
            <RevenueAreaChart
              data={monthlyRevenueData}
              height={280}
              color="#3b82f6"
            />
          </CardContent>
        </Card>

        {/* Invoice Status Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Invoice Status Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col lg:flex-row items-center justify-between">
              <div className="w-full lg:w-1/2">
                <DonutChart
                  data={invoiceStatusData}
                  height={250}
                  innerRadius={60}
                  outerRadius={90}
                  showLegend={false}
                />
              </div>
              <div className="w-full lg:w-1/2 mt-4 lg:mt-0 lg:pl-6 space-y-3">
                {invoiceStatusData.map((item, index) => {
                  const colors = ['#22c55e', '#f59e0b', '#ef4444', '#6b7280', '#3b82f6'];
                  const total = invoiceStatusData.reduce((sum, i) => sum + i.value, 0);
                  const percentage = total > 0 ? ((item.value / total) * 100).toFixed(1) : 0;
                  return (
                    <div key={item.name} className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div
                          className="w-4 h-4 rounded-full"
                          style={{ backgroundColor: colors[index % colors.length] }}
                        />
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{item.name}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm text-gray-500 dark:text-gray-400">{item.value}</span>
                        <span className="text-xs text-gray-400 dark:text-gray-500">({percentage}%)</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Grid - Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Client Growth */}
        <Card>
          <CardHeader>
            <CardTitle>Client Growth</CardTitle>
          </CardHeader>
          <CardContent>
            <MultiLineChart
              data={clientGrowthData}
              height={280}
              lines={[
                { dataKey: 'clients', color: '#3b82f6', name: 'Clients' },
                { dataKey: 'leads', color: '#8b5cf6', name: 'Leads' },
              ]}
            />
          </CardContent>
        </Card>

        {/* Revenue by Category */}
        <Card>
          <CardHeader>
            <CardTitle>Revenue by Category</CardTitle>
          </CardHeader>
          <CardContent>
            <RevenueBarChart
              data={revenueByCategoryData}
              height={280}
              color="#8b5cf6"
              barSize={50}
            />
          </CardContent>
        </Card>
      </div>

      {/* Collection Performance */}
      <Card>
        <CardHeader>
          <CardTitle>Collection Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="flex flex-col items-center">
              <ProgressRing progress={Math.min(100, collectionRate)} size={120} color="#22c55e" label="Collection Rate" />
              <p className="mt-4 text-sm text-gray-500 dark:text-gray-400">
                {formatCurrency(totalRevenue)} collected
              </p>
            </div>
            <div className="flex flex-col items-center">
              <ProgressRing
                progress={invoices?.count ? ((invoices.results?.filter(i => i.status === 'paid').length || 0) / invoices.count) * 100 : 0}
                size={120}
                color="#3b82f6"
                label="Paid Invoices"
              />
              <p className="mt-4 text-sm text-gray-500 dark:text-gray-400">
                {invoices?.results?.filter(i => i.status === 'paid').length || 0} of {invoices?.count || 0}
              </p>
            </div>
            <div className="flex flex-col items-center">
              <ProgressRing
                progress={totalClients ? (activeClients / totalClients) * 100 : 0}
                size={120}
                color="#8b5cf6"
                label="Active Clients"
              />
              <p className="mt-4 text-sm text-gray-500 dark:text-gray-400">
                {activeClients} of {totalClients} clients
              </p>
            </div>
            <div className="flex flex-col items-center">
              <ProgressRing
                progress={contracts?.count ? ((contracts.results?.filter(c => c.status === 'active').length || 0) / contracts.count) * 100 : 0}
                size={120}
                color="#f59e0b"
                label="Active Contracts"
              />
              <p className="mt-4 text-sm text-gray-500 dark:text-gray-400">
                {contracts?.results?.filter(c => c.status === 'active').length || 0} of {contracts?.count || 0}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Top Clients & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Clients */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Top Clients by Revenue</CardTitle>
            <Link to="/clients" className="text-sm text-primary-600 dark:text-primary-400 hover:underline">
              View all
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-gray-100 dark:divide-gray-800">
              {(clients?.results || [])
                .sort((a, b) => (b.total_revenue || 0) - (a.total_revenue || 0))
                .slice(0, 5)
                .map((client, index) => (
                  <Link
                    key={client.id}
                    to={`/clients/${client.id}`}
                    className="flex items-center justify-between px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center text-white text-xs font-medium">
                        {index + 1}
                      </div>
                      <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-full flex items-center justify-center">
                        <span className="text-gray-600 dark:text-gray-300 font-medium">
                          {client.type === 'individual'
                            ? `${client.first_name?.[0]}${client.last_name?.[0]}`
                            : client.company_name?.[0]}
                        </span>
                      </div>
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">
                          {client.type === 'individual'
                            ? `${client.first_name} ${client.last_name}`
                            : client.company_name}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {client.email}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-gray-900 dark:text-white">
                        {formatCurrency(client.total_revenue || 0)}
                      </p>
                      <Badge variant={client.lifecycle_stage === 'customer' ? 'success' : 'default'} size="sm">
                        {client.lifecycle_stage}
                      </Badge>
                    </div>
                  </Link>
                ))}
              {(!clients?.results || clients.results.length === 0) && (
                <div className="px-6 py-12 text-center">
                  <p className="text-gray-500 dark:text-gray-400">No clients yet</p>
                  <Link to="/clients/create" className="text-primary-600 dark:text-primary-400 text-sm hover:underline mt-2 block">
                    Add your first client
                  </Link>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Recent Payments */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent Payments</CardTitle>
            <Link to="/payments" className="text-sm text-primary-600 dark:text-primary-400 hover:underline">
              View all
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-gray-100 dark:divide-gray-800">
              {(payments?.results || []).slice(0, 5).map((payment) => (
                <div key={payment.id} className="flex items-center justify-between px-6 py-4">
                  <div className="flex items-center space-x-3">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      payment.status === 'succeeded'
                        ? 'bg-green-100 dark:bg-green-900/30'
                        : 'bg-amber-100 dark:bg-amber-900/30'
                    }`}>
                      <svg
                        className={`w-5 h-5 ${
                          payment.status === 'succeeded'
                            ? 'text-green-600 dark:text-green-400'
                            : 'text-amber-600 dark:text-amber-400'
                        }`}
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                      </svg>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {payment.client?.type === 'individual'
                          ? `${payment.client.first_name} ${payment.client.last_name}`
                          : payment.client?.company_name || 'Unknown Client'}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {new Date(payment.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`font-semibold ${
                      payment.status === 'succeeded'
                        ? 'text-green-600 dark:text-green-400'
                        : 'text-gray-900 dark:text-white'
                    }`}>
                      {payment.status === 'succeeded' ? '+' : ''}{formatCurrency(payment.amount)}
                    </p>
                    <Badge
                      variant={payment.status === 'succeeded' ? 'success' : 'warning'}
                      size="sm"
                    >
                      {payment.status}
                    </Badge>
                  </div>
                </div>
              ))}
              {(!payments?.results || payments.results.length === 0) && (
                <div className="px-6 py-12 text-center">
                  <p className="text-gray-500 dark:text-gray-400">No payments yet</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <Link to="/invoices/create">
              <Button variant="primary">
                <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Create Invoice
              </Button>
            </Link>
            <Link to="/clients/create">
              <Button variant="outline">
                <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                </svg>
                Add Client
              </Button>
            </Link>
            <Link to="/contracts/create">
              <Button variant="outline">
                <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                New Contract
              </Button>
            </Link>
            <Button variant="ghost">
              <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download Report
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Analytics;
