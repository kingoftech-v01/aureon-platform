/**
 * Invoice Aging Report Page
 * Aureon by Rhematek Solutions
 *
 * Aging report with summary buckets, stacked bar chart,
 * detailed table with color coding and quick actions.
 */

import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import apiClient from '@/services/api';
import { analyticsService } from '@/services/analyticsService';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Button from '@/components/common/Button';
import Badge from '@/components/common/Badge';
import { LoadingSpinner, useToast } from '@/components/common';
import Table, {
  TableHead,
  TableBody,
  TableRow,
  TableHeaderCell,
  TableCell,
} from '@/components/common/Table';

// ============================================
// TYPES
// ============================================

interface AgingBucket {
  label: string;
  count: number;
  amount: number;
  color: string;
  bgClass: string;
  textClass: string;
}

interface AgingInvoice {
  id: string;
  invoice_number: string;
  client_name: string;
  client_id: string;
  amount: number;
  due_date: string;
  days_overdue: number;
  status: string;
}

interface AgingReportData {
  summary: {
    current: { count: number; amount: number };
    days_1_30: { count: number; amount: number };
    days_31_60: { count: number; amount: number };
    days_61_90: { count: number; amount: number };
    days_over_90: { count: number; amount: number };
  };
  invoices: AgingInvoice[];
  total_outstanding: number;
  chart_data?: Array<{
    name: string;
    current: number;
    days_1_30: number;
    days_31_60: number;
    days_61_90: number;
    days_over_90: number;
  }>;
}

// ============================================
// CONSTANTS
// ============================================

const AGING_BUCKETS: Omit<AgingBucket, 'count' | 'amount'>[] = [
  { label: 'Current', color: '#22c55e', bgClass: 'bg-green-100 dark:bg-green-900/30', textClass: 'text-green-600 dark:text-green-400' },
  { label: '1-30 Days', color: '#f59e0b', bgClass: 'bg-yellow-100 dark:bg-yellow-900/30', textClass: 'text-yellow-600 dark:text-yellow-400' },
  { label: '31-60 Days', color: '#f97316', bgClass: 'bg-orange-100 dark:bg-orange-900/30', textClass: 'text-orange-600 dark:text-orange-400' },
  { label: '61-90 Days', color: '#ef4444', bgClass: 'bg-red-100 dark:bg-red-900/30', textClass: 'text-red-600 dark:text-red-400' },
  { label: '90+ Days', color: '#991b1b', bgClass: 'bg-red-200 dark:bg-red-900/50', textClass: 'text-red-800 dark:text-red-300' },
];

// ============================================
// HELPERS
// ============================================

const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
};

const formatDate = (dateStr: string): string => {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

function getAgingBadge(daysOverdue: number): { variant: 'success' | 'warning' | 'danger' | 'default'; label: string } {
  if (daysOverdue <= 0) return { variant: 'success', label: 'Current' };
  if (daysOverdue <= 30) return { variant: 'warning', label: '1-30 days' };
  if (daysOverdue <= 60) return { variant: 'warning', label: '31-60 days' };
  if (daysOverdue <= 90) return { variant: 'danger', label: '61-90 days' };
  return { variant: 'danger', label: '90+ days' };
}

const tooltipStyle = {
  backgroundColor: 'rgba(17, 24, 39, 0.95)',
  border: 'none',
  borderRadius: '8px',
  padding: '12px 16px',
  boxShadow: '0 10px 25px rgba(0, 0, 0, 0.2)',
};

// ============================================
// MAIN COMPONENT
// ============================================

const InvoiceAging: React.FC = () => {
  const queryClient = useQueryClient();
  const { success: showSuccessToast, error: showErrorToast } = useToast();

  const { data, isLoading, isError } = useQuery<AgingReportData>({
    queryKey: ['aging-report'],
    queryFn: async () => {
      const response = await apiClient.get('/analytics/aging-report/');
      return response.data;
    },
  });

  // Send reminder mutation
  const sendReminderMutation = useMutation({
    mutationFn: async (invoiceId: string) => {
      await apiClient.post(`/invoices/${invoiceId}/send-reminder/`);
    },
    onSuccess: () => {
      showSuccessToast('Payment reminder sent successfully');
    },
    onError: () => {
      showErrorToast('Failed to send reminder');
    },
  });

  // Mark as paid mutation
  const markPaidMutation = useMutation({
    mutationFn: async (invoiceId: string) => {
      await apiClient.post(`/invoices/${invoiceId}/mark-paid/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['aging-report'] });
      showSuccessToast('Invoice marked as paid');
    },
    onError: () => {
      showErrorToast('Failed to mark invoice as paid');
    },
  });

  // Prepare bucket data
  const buckets: AgingBucket[] = useMemo(() => {
    if (!data?.summary) return [];
    const summaryKeys = ['current', 'days_1_30', 'days_31_60', 'days_61_90', 'days_over_90'] as const;
    return AGING_BUCKETS.map((bucket, idx) => ({
      ...bucket,
      count: data.summary[summaryKeys[idx]].count,
      amount: data.summary[summaryKeys[idx]].amount,
    }));
  }, [data?.summary]);

  // Prepare chart data
  const chartData = useMemo(() => {
    if (data?.chart_data) return data.chart_data;
    if (!data?.summary) return [];
    return [
      {
        name: 'Outstanding',
        current: data.summary.current.amount,
        days_1_30: data.summary.days_1_30.amount,
        days_31_60: data.summary.days_31_60.amount,
        days_61_90: data.summary.days_61_90.amount,
        days_over_90: data.summary.days_over_90.amount,
      },
    ];
  }, [data]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <LoadingSpinner />
          <p className="mt-4 text-gray-500 dark:text-gray-400">Loading aging report...</p>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">Invoice Aging</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Overdue invoice analysis</p>
        </div>
        <Card>
          <CardContent className="p-12 text-center">
            <div className="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Unable to Load Report</h3>
            <p className="text-gray-500 dark:text-gray-400 mb-4">Could not retrieve aging report data.</p>
            <Link
              to="/invoices"
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/20 rounded-lg hover:bg-primary-100 dark:hover:bg-primary-900/30 transition-colors"
            >
              Back to Invoices
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <Link
              to="/invoices"
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </Link>
            <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">Invoice Aging Report</h1>
          </div>
          <p className="text-gray-600 dark:text-gray-400 ml-8">
            Track overdue invoices and outstanding payments
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="danger" size="md">
            Total Outstanding: {formatCurrency(data?.total_outstanding || 0)}
          </Badge>
        </div>
      </div>

      {/* Aging Bucket Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {buckets.map((bucket) => (
          <Card key={bucket.label} hover className="relative overflow-hidden">
            <CardContent className="p-4">
              <div className={`w-8 h-8 rounded-lg ${bucket.bgClass} ${bucket.textClass} flex items-center justify-center mb-3`}>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">{bucket.label}</p>
              <p className="text-xl font-bold text-gray-900 dark:text-white mt-1">
                {formatCurrency(bucket.amount)}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {bucket.count} invoice{bucket.count !== 1 ? 's' : ''}
              </p>
              <div className="absolute bottom-0 left-0 right-0 h-1" style={{ backgroundColor: bucket.color }} />
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Stacked Bar Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Aging Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
              <XAxis
                dataKey="name"
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#9ca3af', fontSize: 12 }}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#9ca3af', fontSize: 12 }}
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
              />
              <Tooltip
                contentStyle={tooltipStyle}
                labelStyle={{ color: '#fff', fontWeight: 600 }}
                itemStyle={{ color: '#9ca3af' }}
                formatter={(value: number) => [formatCurrency(value), '']}
              />
              <Legend
                verticalAlign="bottom"
                height={36}
                formatter={(value) => (
                  <span className="text-gray-600 dark:text-gray-400">
                    {value.replace(/_/g, ' ').replace('days ', '')}
                  </span>
                )}
              />
              <Bar dataKey="current" name="Current" stackId="a" fill="#22c55e" />
              <Bar dataKey="days_1_30" name="1-30 Days" stackId="a" fill="#f59e0b" />
              <Bar dataKey="days_31_60" name="31-60 Days" stackId="a" fill="#f97316" />
              <Bar dataKey="days_61_90" name="61-90 Days" stackId="a" fill="#ef4444" />
              <Bar dataKey="days_over_90" name="90+ Days" stackId="a" fill="#991b1b" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Invoice Detail Table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Overdue Invoices</CardTitle>
          <Badge variant="default" size="sm">
            {(data?.invoices || []).length} invoices
          </Badge>
        </CardHeader>
        <CardContent>
          {(data?.invoices || []).length > 0 ? (
            <Table>
              <TableHead>
                <TableRow hoverable={false}>
                  <TableHeaderCell>Invoice #</TableHeaderCell>
                  <TableHeaderCell>Client</TableHeaderCell>
                  <TableHeaderCell align="right">Amount</TableHeaderCell>
                  <TableHeaderCell>Due Date</TableHeaderCell>
                  <TableHeaderCell align="center">Days Overdue</TableHeaderCell>
                  <TableHeaderCell>Status</TableHeaderCell>
                  <TableHeaderCell align="right">Actions</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(data?.invoices || []).map((invoice) => {
                  const aging = getAgingBadge(invoice.days_overdue);
                  return (
                    <TableRow key={invoice.id}>
                      <TableCell>
                        <Link
                          to={`/invoices/${invoice.id}`}
                          className="font-medium text-primary-600 dark:text-primary-400 hover:underline"
                        >
                          {invoice.invoice_number}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <Link
                          to={`/clients/${invoice.client_id}`}
                          className="text-gray-900 dark:text-white hover:text-primary-600 dark:hover:text-primary-400"
                        >
                          {invoice.client_name}
                        </Link>
                      </TableCell>
                      <TableCell align="right">
                        <span className="font-mono font-semibold text-gray-900 dark:text-white">
                          {formatCurrency(invoice.amount)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="text-gray-600 dark:text-gray-400">
                          {formatDate(invoice.due_date)}
                        </span>
                      </TableCell>
                      <TableCell align="center">
                        <span className={`font-mono font-semibold ${
                          invoice.days_overdue <= 0
                            ? 'text-green-600 dark:text-green-400'
                            : invoice.days_overdue <= 30
                            ? 'text-yellow-600 dark:text-yellow-400'
                            : invoice.days_overdue <= 60
                            ? 'text-orange-600 dark:text-orange-400'
                            : 'text-red-600 dark:text-red-400'
                        }`}>
                          {invoice.days_overdue <= 0 ? 'Current' : `${invoice.days_overdue}d`}
                        </span>
                      </TableCell>
                      <TableCell>
                        <Badge variant={aging.variant} size="sm">
                          {aging.label}
                        </Badge>
                      </TableCell>
                      <TableCell align="right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => sendReminderMutation.mutate(invoice.id)}
                            disabled={sendReminderMutation.isPending}
                            className="text-xs font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 disabled:opacity-50"
                            title="Send payment reminder"
                          >
                            Remind
                          </button>
                          <span className="text-gray-300 dark:text-gray-600">|</span>
                          <button
                            onClick={() => markPaidMutation.mutate(invoice.id)}
                            disabled={markPaidMutation.isPending}
                            className="text-xs font-medium text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300 disabled:opacity-50"
                            title="Mark as paid"
                          >
                            Mark Paid
                          </button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          ) : (
            <div className="py-12 text-center">
              <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">All caught up!</h3>
              <p className="text-gray-500 dark:text-gray-400">No overdue invoices at this time.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default InvoiceAging;
