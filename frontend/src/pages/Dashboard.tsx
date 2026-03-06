/**
 * Dashboard Home Page
 * Aureon by Rhematek Solutions
 *
 * Main dashboard with statistics, charts, and overview
 */

import React, { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/contexts';
import { clientService, contractService, invoiceService, paymentService } from '@/services';
import { analyticsService } from '../services/analyticsService';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import Button from '@/components/common/Button';
import { RevenueAreaChart, DonutChart, Sparkline, ProgressRing } from '@/components/common/Charts';

const Dashboard: React.FC = () => {
  const { user } = useAuth();

  // Fetch real data
  const { data: clients } = useQuery({
    queryKey: ['clients', { page: 1, pageSize: 100 }],
    queryFn: () => clientService.getClients({ page: 1, pageSize: 100 }),
  });

  const { data: invoices } = useQuery({
    queryKey: ['invoices', { page: 1, pageSize: 100 }],
    queryFn: () => invoiceService.getInvoices({ page: 1, pageSize: 100 }),
  });

  const { data: payments } = useQuery({
    queryKey: ['payments', { page: 1, pageSize: 100 }],
    queryFn: () => paymentService.getPayments({ page: 1, pageSize: 100 }),
  });

  const { data: contracts } = useQuery({
    queryKey: ['contracts', { page: 1, pageSize: 100 }],
    queryFn: () => contractService.getContracts({ page: 1, pageSize: 100 }),
  });

  const { data: analyticsData } = useQuery({
    queryKey: ['dashboard-analytics'],
    queryFn: () => analyticsService.getDashboardStats(),
    staleTime: 5 * 60 * 1000,
  });

  // Calculate metrics
  const totalRevenue = payments?.results?.filter(p => p.status === 'succeeded').reduce((sum, p) => sum + p.amount, 0) || 0;
  const activeClients = clients?.results?.filter(c => c.lifecycle_stage === 'active').length || 0;
  const pendingInvoices = invoices?.results?.filter(i => i.status === 'sent' || i.status === 'overdue').length || 0;
  const activeContracts = contracts?.results?.filter(c => c.status === 'active').length || 0;
  const totalOutstanding = invoices?.results?.filter(i => i.status !== 'paid' && i.status !== 'cancelled').reduce((sum, i) => sum + i.total, 0) || 0;

  // Generate monthly revenue data for chart
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const monthlyRevenueData = useMemo(() => {
    const now = new Date();
    return Array.from({ length: 6 }, (_, i) => {
      const d = new Date(now.getFullYear(), now.getMonth() - 5 + i, 1);
      const monthRevenue = payments?.results
        ?.filter(p => p.status === 'succeeded' && new Date(p.created_at).getMonth() === d.getMonth() && new Date(p.created_at).getFullYear() === d.getFullYear())
        .reduce((sum, p) => sum + p.amount, 0) || 0;
      return { name: months[d.getMonth()], value: monthRevenue };
    });
  }, [payments]);

  // Invoice status distribution for donut chart
  const invoiceStatusData = useMemo(() => {
    if (!invoices?.results) return [];

    const statusCounts = invoices.results.reduce((acc, inv) => {
      acc[inv.status] = (acc[inv.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const statusLabels: Record<string, string> = {
      draft: 'Draft',
      sent: 'Sent',
      paid: 'Paid',
      overdue: 'Overdue',
      cancelled: 'Cancelled',
    };

    return Object.entries(statusCounts).map(([status, count]) => ({
      name: statusLabels[status] || status,
      value: count,
    }));
  }, [invoices]);

  // Sparkline data for stats cards
  const revenueSparkline: number[] = useMemo(() => {
    if (!payments?.results) return [];
    const now = new Date();
    const last6Months = Array.from({ length: 6 }, (_, i) => {
      const d = new Date(now.getFullYear(), now.getMonth() - 5 + i, 1);
      return d.getMonth();
    });
    return last6Months.map(month =>
      payments.results.filter(p => p.status === 'succeeded' && new Date(p.created_at).getMonth() === month)
        .reduce((sum, p) => sum + p.amount, 0)
    );
  }, [payments]);

  const clientsSparkline: number[] = useMemo(() => {
    if (!clients?.results) return [];
    const now = new Date();
    const last6Months = Array.from({ length: 6 }, (_, i) => {
      const d = new Date(now.getFullYear(), now.getMonth() - 5 + i, 1);
      return d.getMonth();
    });
    return last6Months.map(month =>
      clients.results.filter(c => new Date(c.created_at).getMonth() === month).length
    );
  }, [clients]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  // Get current hour for greeting
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  // Collection rate calculation
  const collectionRate = totalRevenue > 0 && invoices?.results
    ? Math.min(100, (totalRevenue / (invoices.results.reduce((sum, i) => sum + i.total, 0) || 1)) * 100)
    : 0;

  // AI Insights - dynamic insight generation from real data
  const aiInsights = useMemo(() => {
    const insights: Array<{ icon: string; title: string; description: string; color: string }> = [];

    // Revenue trend insight
    if (revenueSparkline.length >= 2) {
      const latest = revenueSparkline[revenueSparkline.length - 1];
      const previous = revenueSparkline[revenueSparkline.length - 2];
      if (previous > 0) {
        const changePercent = Math.round(((latest - previous) / previous) * 100);
        if (changePercent > 0) {
          insights.push({
            icon: 'trending-up',
            title: 'Revenue Trending Up',
            description: `Revenue is trending up ${changePercent}% compared to the previous month. Keep the momentum going.`,
            color: 'green',
          });
        } else if (changePercent < 0) {
          insights.push({
            icon: 'trending-down',
            title: 'Revenue Dip Detected',
            description: `Revenue decreased ${Math.abs(changePercent)}% from last month. Consider following up on pending proposals.`,
            color: 'amber',
          });
        }
      } else if (latest > 0) {
        insights.push({
          icon: 'trending-up',
          title: 'First Revenue Recorded',
          description: `Great start! You recorded ${formatCurrency(latest)} in revenue this month.`,
          color: 'green',
        });
      }
    }

    // Overdue invoices insight
    const overdueCount = invoices?.results?.filter(i => i.status === 'overdue').length || 0;
    if (overdueCount > 0) {
      const overdueTotal = invoices?.results?.filter(i => i.status === 'overdue').reduce((sum, i) => sum + i.total, 0) || 0;
      insights.push({
        icon: 'alert',
        title: `${overdueCount} Overdue Invoice${overdueCount > 1 ? 's' : ''}`,
        description: `${formatCurrency(overdueTotal)} is overdue and needs attention. Consider sending reminders to improve cash flow.`,
        color: 'red',
      });
    }

    // Client retention insight
    const totalClientCount = clients?.count || 0;
    if (totalClientCount > 0 && activeClients > 0) {
      const retentionRate = Math.round((activeClients / totalClientCount) * 100);
      insights.push({
        icon: 'users',
        title: 'Client Retention',
        description: retentionRate >= 80
          ? `Client retention rate is ${retentionRate}%, which is excellent. Your clients are staying engaged.`
          : `Client retention rate is ${retentionRate}%. Consider reaching out to inactive clients to re-engage them.`,
        color: retentionRate >= 80 ? 'blue' : 'amber',
      });
    }

    // Collection efficiency insight
    if (collectionRate > 0) {
      insights.push({
        icon: 'check-circle',
        title: 'Collection Efficiency',
        description: collectionRate >= 90
          ? `Your collection rate is ${Math.round(collectionRate)}%. Outstanding performance in payment collection.`
          : collectionRate >= 70
          ? `Collection rate is ${Math.round(collectionRate)}%. There is room to improve by automating payment reminders.`
          : `Collection rate is ${Math.round(collectionRate)}%. Consider enabling automatic payment retries to improve this metric.`,
        color: collectionRate >= 90 ? 'green' : collectionRate >= 70 ? 'blue' : 'amber',
      });
    }

    // Fallback insight if no data
    if (insights.length === 0) {
      insights.push({
        icon: 'info',
        title: 'Getting Started',
        description: 'Start creating clients, contracts, and invoices to see AI-powered insights about your business performance.',
        color: 'blue',
      });
    }

    return insights;
  }, [revenueSparkline, invoices, clients, activeClients, collectionRate]);

  return (
    <div className="space-y-6">
      {/* Welcome Header with Action Buttons */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">
            {getGreeting()}, {user?.first_name || 'there'}!
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Here's an overview of your business performance
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link to="/contracts/create">
            <Button variant="outline" size="md">
              <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              New Contract
            </Button>
          </Link>
          <Link to="/invoices/create">
            <Button variant="primary" size="md">
              <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Create Invoice
            </Button>
          </Link>
        </div>
      </div>

      {/* Quick Stats - Enhanced Cards with Sparklines */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
        {/* Total Revenue */}
        <Card hover className="relative overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Revenue</p>
                <p className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white mt-2">
                  {formatCurrency(totalRevenue)}
                </p>
              </div>
              <div className="w-14 h-14 bg-gradient-to-br from-green-400 to-green-600 rounded-xl flex items-center justify-center shadow-lg shadow-green-500/30">
                <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div className="h-10">
              <Sparkline data={revenueSparkline} color="#22c55e" />
            </div>
            <div className="flex items-center mt-2">
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                <svg className="w-3 h-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                </svg>
                {analyticsData?.revenue_growth ? `${analyticsData.revenue_growth}%` : '0%'}
              </span>
              <span className="text-xs text-gray-500 dark:text-gray-400 ml-2">vs last month</span>
            </div>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-green-400 to-green-600"></div>
          </CardContent>
        </Card>

        {/* Active Clients */}
        <Card hover className="relative overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Active Clients</p>
                <p className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white mt-2">
                  {activeClients}
                </p>
              </div>
              <div className="w-14 h-14 bg-gradient-to-br from-blue-400 to-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/30">
                <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
            </div>
            <div className="h-10">
              <Sparkline data={clientsSparkline} color="#3b82f6" />
            </div>
            <div className="flex items-center mt-2">
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {clients?.count || 0} total clients in your CRM
              </span>
            </div>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-400 to-blue-600"></div>
          </CardContent>
        </Card>

        {/* Pending Invoices */}
        <Card hover className="relative overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Pending Invoices</p>
                <p className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white mt-2">
                  {pendingInvoices}
                </p>
                <div className="flex items-center mt-3">
                  <span className="text-xs text-amber-600 dark:text-amber-400 font-medium">
                    {formatCurrency(totalOutstanding)} outstanding
                  </span>
                </div>
              </div>
              <div className="w-14 h-14 bg-gradient-to-br from-amber-400 to-amber-600 rounded-xl flex items-center justify-center shadow-lg shadow-amber-500/30">
                <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2z" />
                </svg>
              </div>
            </div>
            <div className="mt-4">
              <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
                <span>Collection Progress</span>
                <span>{Math.round(collectionRate)}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-amber-400 to-amber-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${collectionRate}%` }}
                />
              </div>
            </div>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-400 to-amber-600"></div>
          </CardContent>
        </Card>

        {/* Active Contracts */}
        <Card hover className="relative overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Active Contracts</p>
                <p className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white mt-2">
                  {activeContracts}
                </p>
                <div className="flex items-center mt-3">
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {contracts?.count || 0} total contracts
                  </span>
                </div>
              </div>
              <div className="w-14 h-14 bg-gradient-to-br from-purple-400 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/30">
                <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
            </div>
            <div className="mt-4 flex items-center justify-between">
              <div className="flex -space-x-2">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-400 to-purple-600 border-2 border-white dark:border-gray-900 flex items-center justify-center text-white text-xs font-medium"
                  >
                    {i}
                  </div>
                ))}
              </div>
              <Link to="/contracts" className="text-xs text-purple-600 dark:text-purple-400 hover:underline">
                View all
              </Link>
            </div>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-400 to-purple-600"></div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Revenue Chart */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Revenue Overview</CardTitle>
            <div className="flex items-center space-x-2">
              <button className="px-3 py-1 text-xs font-medium rounded-full bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400">
                Monthly
              </button>
              <button className="px-3 py-1 text-xs font-medium rounded-full text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800">
                Weekly
              </button>
              <button className="px-3 py-1 text-xs font-medium rounded-full text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800">
                Daily
              </button>
            </div>
          </CardHeader>
          <CardContent>
            {monthlyRevenueData.length > 0 ? (
              <RevenueAreaChart
                data={monthlyRevenueData}
                height={280}
                color="#3b82f6"
              />
            ) : (
              <div className="h-64 flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900 rounded-xl">
                <div className="text-center">
                  <div className="w-16 h-16 bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg className="w-8 h-8 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                    </svg>
                  </div>
                  <p className="text-gray-600 dark:text-gray-400 font-medium">No revenue data yet</p>
                  <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">
                    Create invoices to see your revenue
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Invoice Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Invoice Status</CardTitle>
          </CardHeader>
          <CardContent>
            {invoiceStatusData.length > 0 ? (
              <div className="flex flex-col items-center">
                <DonutChart
                  data={invoiceStatusData}
                  height={200}
                  innerRadius={50}
                  outerRadius={80}
                  showLegend={false}
                />
                <div className="mt-4 grid grid-cols-2 gap-3 w-full">
                  {invoiceStatusData.map((item, index) => {
                    const colors = ['#3b82f6', '#8b5cf6', '#22c55e', '#f59e0b', '#ef4444'];
                    return (
                      <div key={item.name} className="flex items-center space-x-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: colors[index % colors.length] }}
                        />
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          {item.name}: {item.value}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="h-48 flex items-center justify-center">
                <div className="text-center">
                  <p className="text-gray-500 dark:text-gray-400">No invoices yet</p>
                  <Link to="/invoices/create" className="text-primary-600 dark:text-primary-400 text-sm hover:underline mt-2 block">
                    Create your first invoice
                  </Link>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <Link
              to="/clients/create"
              className="group p-5 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-xl hover:shadow-md transition-all duration-200 border border-blue-100 dark:border-blue-800/30"
            >
              <div className="w-12 h-12 bg-blue-500 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                </svg>
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                Add Client
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Onboard new clients
              </p>
            </Link>

            <Link
              to="/contracts/create"
              className="group p-5 bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-xl hover:shadow-md transition-all duration-200 border border-purple-100 dark:border-purple-800/30"
            >
              <div className="w-12 h-12 bg-purple-500 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                New Contract
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Generate with e-sign
              </p>
            </Link>

            <Link
              to="/invoices/create"
              className="group p-5 bg-gradient-to-br from-amber-50 to-amber-100 dark:from-amber-900/20 dark:to-amber-800/20 rounded-xl hover:shadow-md transition-all duration-200 border border-amber-100 dark:border-amber-800/30"
            >
              <div className="w-12 h-12 bg-amber-500 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2z" />
                </svg>
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                Send Invoice
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Bill your clients
              </p>
            </Link>

            <Link
              to="/documents"
              className="group p-5 bg-gradient-to-br from-cyan-50 to-cyan-100 dark:from-cyan-900/20 dark:to-cyan-800/20 rounded-xl hover:shadow-md transition-all duration-200 border border-cyan-100 dark:border-cyan-800/30"
            >
              <div className="w-12 h-12 bg-cyan-500 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                Documents
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Manage files
              </p>
            </Link>

            <Link
              to="/analytics"
              className="group p-5 bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-xl hover:shadow-md transition-all duration-200 border border-green-100 dark:border-green-800/30"
            >
              <div className="w-12 h-12 bg-green-500 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                Analytics
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                View reports
              </p>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* Top Clients & Upcoming */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Clients */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Top Clients</CardTitle>
            <Link to="/clients" className="text-sm text-primary-600 dark:text-primary-400 hover:underline">
              View all
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            {clients?.results && clients.results.length > 0 ? (
              <div className="divide-y divide-gray-100 dark:divide-gray-800">
                {clients.results
                  .sort((a, b) => (b.total_revenue || 0) - (a.total_revenue || 0))
                  .slice(0, 5)
                  .map((client, index) => (
                    <Link
                      key={client.id}
                      to={`/clients/${client.id}`}
                      className="flex items-center justify-between px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                    >
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center text-white font-medium">
                          {client.type === 'individual'
                            ? `${client.first_name?.[0]}${client.last_name?.[0]}`
                            : client.company_name?.[0]}
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
                        <Badge variant={client.lifecycle_stage === 'active' ? 'success' : 'default'} size="sm">
                          {client.lifecycle_stage}
                        </Badge>
                      </div>
                    </Link>
                  ))}
              </div>
            ) : (
              <div className="px-6 py-12 text-center">
                <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </div>
                <p className="text-gray-600 dark:text-gray-400 mb-4">No clients yet</p>
                <Link to="/clients/create">
                  <Button variant="primary" size="sm">Add Your First Client</Button>
                </Link>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Pending Payments */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Pending Payments</CardTitle>
            <Link to="/invoices" className="text-sm text-primary-600 dark:text-primary-400 hover:underline">
              View all
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            {invoices?.results && invoices.results.filter(i => i.status !== 'paid').length > 0 ? (
              <div className="divide-y divide-gray-100 dark:divide-gray-800">
                {invoices.results
                  .filter(i => i.status !== 'paid' && i.status !== 'cancelled')
                  .slice(0, 5)
                  .map((invoice) => (
                    <Link
                      key={invoice.id}
                      to={`/invoices/${invoice.id}`}
                      className="flex items-center justify-between px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                    >
                      <div className="flex items-center space-x-3">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                          invoice.status === 'overdue' ? 'bg-red-100 dark:bg-red-900/30' : 'bg-amber-100 dark:bg-amber-900/30'
                        }`}>
                          <svg className={`w-5 h-5 ${invoice.status === 'overdue' ? 'text-red-600 dark:text-red-400' : 'text-amber-600 dark:text-amber-400'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2z" />
                          </svg>
                        </div>
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">
                            {invoice.invoice_number}
                          </p>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            Due {new Date(invoice.due_date).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-gray-900 dark:text-white">
                          {formatCurrency(invoice.total)}
                        </p>
                        <Badge
                          variant={invoice.status === 'overdue' ? 'danger' : 'warning'}
                          size="sm"
                        >
                          {invoice.status}
                        </Badge>
                      </div>
                    </Link>
                  ))}
              </div>
            ) : (
              <div className="px-6 py-12 text-center">
                <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <p className="text-gray-600 dark:text-gray-400 mb-2 font-medium">All caught up!</p>
                <p className="text-sm text-gray-500 dark:text-gray-500">No pending invoices</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Collection Performance */}
      <Card>
        <CardHeader>
          <CardTitle>Collection Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex items-center space-x-4">
              <ProgressRing progress={collectionRate} size={100} color="#22c55e" label="Collected" />
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{formatCurrency(totalRevenue)}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">Total collected</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <ProgressRing progress={pendingInvoices > 0 ? (pendingInvoices / (invoices?.count || 1)) * 100 : 0} size={100} color="#f59e0b" label="Pending" />
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{formatCurrency(totalOutstanding)}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">Outstanding amount</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <ProgressRing
                progress={activeClients > 0 ? (activeClients / (clients?.count || 1)) * 100 : 0}
                size={100}
                color="#3b82f6"
                label="Active"
              />
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{activeClients}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">Active customers</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* AI Insights */}
      <Card className="overflow-hidden">
        <div className="bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 px-6 py-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">AI Insights</h3>
              <p className="text-sm text-white/80">Smart recommendations based on your data</p>
            </div>
          </div>
        </div>
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {aiInsights.map((insight, index) => {
              const colorClasses: Record<string, { bg: string; icon: string; border: string }> = {
                green: {
                  bg: 'bg-green-50 dark:bg-green-900/20',
                  icon: 'text-green-600 dark:text-green-400',
                  border: 'border-green-200 dark:border-green-800/30',
                },
                amber: {
                  bg: 'bg-amber-50 dark:bg-amber-900/20',
                  icon: 'text-amber-600 dark:text-amber-400',
                  border: 'border-amber-200 dark:border-amber-800/30',
                },
                red: {
                  bg: 'bg-red-50 dark:bg-red-900/20',
                  icon: 'text-red-600 dark:text-red-400',
                  border: 'border-red-200 dark:border-red-800/30',
                },
                blue: {
                  bg: 'bg-blue-50 dark:bg-blue-900/20',
                  icon: 'text-blue-600 dark:text-blue-400',
                  border: 'border-blue-200 dark:border-blue-800/30',
                },
              };
              const colors = colorClasses[insight.color] || colorClasses.blue;

              const iconPaths: Record<string, string> = {
                'trending-up': 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6',
                'trending-down': 'M13 17h8m0 0V9m0 8l-8-8-4 4-6-6',
                'alert': 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
                'users': 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z',
                'check-circle': 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
                'info': 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
              };

              return (
                <div
                  key={index}
                  className={`flex items-start space-x-4 p-4 rounded-xl border ${colors.bg} ${colors.border} transition-all duration-200 hover:shadow-sm`}
                >
                  <div className={`mt-0.5 flex-shrink-0 ${colors.icon}`}>
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={iconPaths[insight.icon] || iconPaths.info} />
                    </svg>
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-white text-sm">{insight.title}</h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{insight.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;
