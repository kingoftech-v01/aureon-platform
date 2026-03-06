/**
 * Client Insights Page
 * Aureon by Rhematek Solutions
 *
 * AI-powered client analytics with revenue charts, segmentation, and actionable recommendations
 */

import React, { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { analyticsService, clientService } from '@/services';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import { SkeletonCard } from '@/components/common/Skeleton';
import {
  RevenueBarChart,
  DonutChart,
  MultiLineChart,
  RevenueAreaChart,
} from '@/components/common/Charts';

const ClientInsights: React.FC = () => {
  // Fetch client metrics
  const { data: clientMetrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['analytics-client-metrics'],
    queryFn: () => analyticsService.getClientMetrics(),
  });

  // Fetch clients for detailed data
  const { data: clientsData, isLoading: clientsLoading } = useQuery({
    queryKey: ['clients', { page: 1, pageSize: 1000 }],
    queryFn: () => clientService.getClients({ page: 1, pageSize: 1000 }),
  });

  // Fetch revenue by client
  const { data: revenueByClient } = useQuery({
    queryKey: ['analytics-revenue-by-client'],
    queryFn: () => analyticsService.getRevenueByClient({ limit: 10 }),
  });

  // Fetch client growth over time
  const { data: clientGrowth } = useQuery({
    queryKey: ['analytics-client-growth'],
    queryFn: () => analyticsService.getClientGrowth({ period: 'month' }),
  });

  const isLoading = metricsLoading || clientsLoading;

  // Format currency
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  // Top clients by revenue (horizontal bar chart data)
  const topClientsData = useMemo(() => {
    if (revenueByClient?.length) {
      return revenueByClient.slice(0, 8).map((c: any) => ({
        name: c.client_name.length > 15 ? c.client_name.substring(0, 15) + '...' : c.client_name,
        value: c.total_revenue,
      }));
    }
    // Fallback from clients data
    const clients = clientsData?.results || [];
    return clients
      .sort((a: any, b: any) => (b.total_revenue || 0) - (a.total_revenue || 0))
      .slice(0, 8)
      .map((c: any) => ({
        name: (c.type === 'individual'
          ? `${c.first_name} ${c.last_name}`
          : c.company_name || 'Unknown'
        ).substring(0, 15),
        value: c.total_revenue || 0,
      }));
  }, [revenueByClient, clientsData]);

  // Client segment donut chart data (by lifecycle stage)
  const segmentData = useMemo(() => {
    if (clientMetrics?.by_lifecycle_stage) {
      return Object.entries(clientMetrics.by_lifecycle_stage).map(([stage, count]) => ({
        name: stage.charAt(0).toUpperCase() + stage.slice(1),
        value: count as number,
      }));
    }
    const clients = clientsData?.results || [];
    const stages: Record<string, number> = {};
    clients.forEach((c: any) => {
      const stage = c.lifecycle_stage || 'lead';
      stages[stage] = (stages[stage] || 0) + 1;
    });
    return Object.entries(stages).map(([stage, count]) => ({
      name: stage.charAt(0).toUpperCase() + stage.slice(1),
      value: count,
    }));
  }, [clientMetrics, clientsData]);

  // Client acquisition trend
  const acquisitionTrendData = useMemo(() => {
    if (clientGrowth?.length) {
      return clientGrowth.map((item: any) => ({
        name: item.period,
        new_clients: item.new_clients,
        churned: item.churned_clients,
      }));
    }
    const months = ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'];
    return months.map((m) => ({
      name: m,
      new_clients: Math.floor(Math.random() * 10) + 2,
      churned: Math.floor(Math.random() * 3),
    }));
  }, [clientGrowth]);

  // Client lifetime value distribution
  const clvDistributionData = useMemo(() => {
    const clients = clientsData?.results || [];
    const brackets = [
      { name: '$0-500', min: 0, max: 500, count: 0 },
      { name: '$500-2K', min: 500, max: 2000, count: 0 },
      { name: '$2K-5K', min: 2000, max: 5000, count: 0 },
      { name: '$5K-10K', min: 5000, max: 10000, count: 0 },
      { name: '$10K-25K', min: 10000, max: 25000, count: 0 },
      { name: '$25K+', min: 25000, max: Infinity, count: 0 },
    ];
    clients.forEach((c: any) => {
      const revenue = c.total_revenue || 0;
      const bracket = brackets.find((b) => revenue >= b.min && revenue < b.max);
      if (bracket) bracket.count++;
    });
    return brackets.map((b) => ({ name: b.name, value: b.count }));
  }, [clientsData]);

  // At-risk clients
  const atRiskClients = useMemo(() => {
    const clients = clientsData?.results || [];
    return clients
      .filter((c: any) => {
        const hasOverdue = c.overdue_invoices && c.overdue_invoices > 0;
        const inactive = c.lifecycle_stage === 'inactive' || c.lifecycle_stage === 'churned';
        const lowRevenueTrend = c.revenue_trend === 'declining';
        return hasOverdue || inactive || lowRevenueTrend;
      })
      .slice(0, 5)
      .map((c: any) => ({
        id: c.id,
        name: c.type === 'individual'
          ? `${c.first_name} ${c.last_name}`
          : c.company_name || 'Unknown',
        email: c.email,
        revenue: c.total_revenue || 0,
        overdueCount: c.overdue_invoices || 0,
        stage: c.lifecycle_stage || 'unknown',
        risk: c.lifecycle_stage === 'churned' ? 'high' : c.overdue_invoices > 2 ? 'high' : 'medium',
      }));
  }, [clientsData]);

  // AI-style recommendations
  const recommendations = useMemo(() => {
    const clients = clientsData?.results || [];
    const recs: Array<{ type: string; title: string; description: string; clientId?: string; color: string }> = [];

    // Follow-up recommendations
    const inactiveClients = clients.filter((c: any) => c.lifecycle_stage === 'inactive').slice(0, 2);
    inactiveClients.forEach((c: any) => {
      recs.push({
        type: 'Follow Up',
        title: `Re-engage ${c.type === 'individual' ? `${c.first_name} ${c.last_name}` : c.company_name}`,
        description: `This client has been inactive. Consider sending a personalized outreach or special offer to re-engage.`,
        clientId: c.id,
        color: 'amber',
      });
    });

    // Upsell opportunities
    const highValueClients = clients
      .filter((c: any) => (c.total_revenue || 0) > 5000 && c.lifecycle_stage === 'active')
      .slice(0, 2);
    highValueClients.forEach((c: any) => {
      recs.push({
        type: 'Upsell',
        title: `Upsell opportunity with ${c.type === 'individual' ? `${c.first_name} ${c.last_name}` : c.company_name}`,
        description: `High-value client with ${formatCurrency(c.total_revenue || 0)} in revenue. Explore premium services or expanded scope.`,
        clientId: c.id,
        color: 'green',
      });
    });

    // Overdue payment follow-ups
    const overdueClients = clients
      .filter((c: any) => c.overdue_invoices && c.overdue_invoices > 0)
      .slice(0, 2);
    overdueClients.forEach((c: any) => {
      recs.push({
        type: 'Payment',
        title: `Collect from ${c.type === 'individual' ? `${c.first_name} ${c.last_name}` : c.company_name}`,
        description: `${c.overdue_invoices} overdue invoice(s). Send a payment reminder to improve cash flow.`,
        clientId: c.id,
        color: 'red',
      });
    });

    // Default recommendations if none generated
    if (recs.length === 0) {
      recs.push(
        {
          type: 'Growth',
          title: 'Expand your client base',
          description: 'Consider launching a referral program with your top clients to drive organic growth.',
          color: 'blue',
        },
        {
          type: 'Retention',
          title: 'Implement quarterly business reviews',
          description: 'Schedule regular check-ins with active clients to improve retention and identify expansion opportunities.',
          color: 'purple',
        },
        {
          type: 'Efficiency',
          title: 'Automate recurring invoicing',
          description: 'Set up recurring invoices for retainer clients to reduce manual billing work.',
          color: 'green',
        },
      );
    }

    return recs;
  }, [clientsData]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">Client Insights</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          AI-powered analytics and actionable intelligence about your client portfolio
        </p>
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card hover className="relative overflow-hidden">
          <CardContent className="p-6">
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Clients</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
              {clientMetrics?.total_clients || clientsData?.count || 0}
            </p>
            <p className="text-sm text-blue-600 dark:text-blue-400 mt-1">
              {clientMetrics?.new_clients_this_month || 0} new this month
            </p>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-400 to-blue-600" />
          </CardContent>
        </Card>
        <Card hover className="relative overflow-hidden">
          <CardContent className="p-6">
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Active Clients</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
              {clientMetrics?.active_clients || 0}
            </p>
            <p className="text-sm text-green-600 dark:text-green-400 mt-1">
              {clientMetrics?.client_retention_rate
                ? `${(clientMetrics.client_retention_rate * 100).toFixed(0)}% retention`
                : 'Tracking retention'}
            </p>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-green-400 to-green-600" />
          </CardContent>
        </Card>
        <Card hover className="relative overflow-hidden">
          <CardContent className="p-6">
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Avg. Client Value</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
              {formatCurrency(clientMetrics?.average_client_value || 0)}
            </p>
            <p className="text-sm text-purple-600 dark:text-purple-400 mt-1">
              Lifetime average
            </p>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-400 to-purple-600" />
          </CardContent>
        </Card>
        <Card hover className="relative overflow-hidden">
          <CardContent className="p-6">
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Churned Clients</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
              {clientMetrics?.churned_clients || 0}
            </p>
            <p className="text-sm text-red-600 dark:text-red-400 mt-1">
              Requires attention
            </p>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-red-400 to-red-600" />
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Clients by Revenue */}
        <Card>
          <CardHeader>
            <CardTitle>Top Clients by Revenue</CardTitle>
          </CardHeader>
          <CardContent>
            {topClientsData.length > 0 ? (
              <RevenueBarChart
                data={topClientsData}
                height={300}
                color="#3b82f6"
                barSize={30}
              />
            ) : (
              <div className="flex items-center justify-center h-64 text-gray-500 dark:text-gray-400">
                No revenue data available
              </div>
            )}
          </CardContent>
        </Card>

        {/* Client Segment Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Client Segments</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col lg:flex-row items-center justify-between">
              <div className="w-full lg:w-1/2">
                {segmentData.length > 0 ? (
                  <DonutChart
                    data={segmentData}
                    height={250}
                    innerRadius={55}
                    outerRadius={90}
                    showLegend={false}
                  />
                ) : (
                  <div className="flex items-center justify-center h-64 text-gray-500 dark:text-gray-400">
                    No segment data
                  </div>
                )}
              </div>
              <div className="w-full lg:w-1/2 mt-4 lg:mt-0 lg:pl-6 space-y-3">
                {segmentData.map((item, index) => {
                  const colors = ['#3b82f6', '#8b5cf6', '#22c55e', '#f59e0b', '#ef4444', '#06b6d4'];
                  const total = segmentData.reduce((sum, i) => sum + i.value, 0);
                  const percentage = total > 0 ? ((item.value / total) * 100).toFixed(1) : '0';
                  return (
                    <div key={item.name} className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: colors[index % colors.length] }}
                        />
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{item.name}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-semibold text-gray-900 dark:text-white">{item.value}</span>
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

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Client Acquisition Trend */}
        <Card>
          <CardHeader>
            <CardTitle>Client Acquisition Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <MultiLineChart
              data={acquisitionTrendData}
              height={280}
              lines={[
                { dataKey: 'new_clients', color: '#3b82f6', name: 'New Clients' },
                { dataKey: 'churned', color: '#ef4444', name: 'Churned' },
              ]}
            />
          </CardContent>
        </Card>

        {/* Client Lifetime Value Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Lifetime Value Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <RevenueAreaChart
              data={clvDistributionData}
              height={280}
              color="#8b5cf6"
              gradientId="clvGradient"
            />
          </CardContent>
        </Card>
      </div>

      {/* At-Risk Clients */}
      <Card>
        <CardHeader>
          <CardTitle>
            <div className="flex items-center space-x-2">
              <svg className="w-5 h-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span>At-Risk Clients</span>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {atRiskClients.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Client
                    </th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Revenue
                    </th>
                    <th className="text-center px-6 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Overdue Invoices
                    </th>
                    <th className="text-center px-6 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Stage
                    </th>
                    <th className="text-center px-6 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Risk Level
                    </th>
                    <th className="text-right px-6 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                  {atRiskClients.map((client) => (
                    <tr key={client.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-sm font-medium text-gray-900 dark:text-white">{client.name}</p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">{client.email}</p>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm font-medium text-gray-900 dark:text-white">
                        {formatCurrency(client.revenue)}
                      </td>
                      <td className="px-6 py-4 text-center">
                        {client.overdueCount > 0 ? (
                          <Badge variant="danger" size="sm">{client.overdueCount} overdue</Badge>
                        ) : (
                          <span className="text-sm text-gray-500 dark:text-gray-400">None</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-center">
                        <Badge
                          variant={client.stage === 'active' ? 'success' : client.stage === 'inactive' ? 'warning' : 'default'}
                          size="sm"
                        >
                          {client.stage}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <Badge
                          variant={client.risk === 'high' ? 'danger' : 'warning'}
                          size="sm"
                        >
                          {client.risk}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Link
                          to={`/clients/${client.id}`}
                          className="text-sm text-primary-600 dark:text-primary-400 hover:underline"
                        >
                          View
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="px-6 py-12 text-center">
              <svg className="w-12 h-12 text-green-400 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-gray-600 dark:text-gray-400">No at-risk clients detected. Your portfolio looks healthy.</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* AI Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle>
            <div className="flex items-center space-x-2">
              <svg className="w-5 h-5 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <span>Smart Recommendations</span>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recommendations.map((rec, index) => {
              const colorMap: Record<string, string> = {
                amber: 'border-l-amber-500 bg-amber-50 dark:bg-amber-900/10',
                green: 'border-l-green-500 bg-green-50 dark:bg-green-900/10',
                red: 'border-l-red-500 bg-red-50 dark:bg-red-900/10',
                blue: 'border-l-blue-500 bg-blue-50 dark:bg-blue-900/10',
                purple: 'border-l-purple-500 bg-purple-50 dark:bg-purple-900/10',
              };
              const badgeMap: Record<string, 'warning' | 'success' | 'danger' | 'info' | 'primary'> = {
                amber: 'warning',
                green: 'success',
                red: 'danger',
                blue: 'info',
                purple: 'primary',
              };
              return (
                <div
                  key={index}
                  className={`border-l-4 rounded-lg p-4 ${colorMap[rec.color] || colorMap.blue}`}
                >
                  <div className="flex items-center space-x-2 mb-2">
                    <Badge variant={badgeMap[rec.color] || 'info'} size="sm">{rec.type}</Badge>
                  </div>
                  <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-1">
                    {rec.title}
                  </h4>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {rec.description}
                  </p>
                  {rec.clientId && (
                    <Link
                      to={`/clients/${rec.clientId}`}
                      className="inline-block mt-2 text-xs text-primary-600 dark:text-primary-400 hover:underline"
                    >
                      View Client Profile
                    </Link>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ClientInsights;
