/**
 * Cash Flow Forecast Dashboard
 * Aureon by Rhematek Solutions
 *
 * Shows current balance, projected income/expenses, net cash flow,
 * area chart for 90-day projection, scenario toggling, and a detailed
 * cash flow table with running balance.
 */

import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
} from 'recharts';
import apiClient from '@/services/api';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import { LoadingSpinner } from '@/components/common';
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

type Scenario = 'optimistic' | 'realistic' | 'conservative';

interface CashFlowProjection {
  current_balance: number;
  projected_income_30d: number;
  projected_expenses_30d: number;
  net_cash_flow: number;
  daily_projections: DailyProjection[];
  pending_invoices: PendingInvoice[];
  upcoming_expenses: UpcomingExpense[];
  negative_cash_flow_alert: boolean;
  negative_cash_flow_date?: string;
}

interface DailyProjection {
  date: string;
  income: number;
  expenses: number;
  net: number;
  balance: number;
  optimistic_balance?: number;
  conservative_balance?: number;
}

interface PendingInvoice {
  id: string;
  invoice_number: string;
  client_name: string;
  amount: number;
  due_date: string;
}

interface UpcomingExpense {
  id: string;
  description: string;
  amount: number;
  due_date: string;
  category: string;
}

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
    month: 'short',
    day: 'numeric',
  });
};

const formatFullDate = (dateStr: string): string => {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

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

const CashFlowForecast: React.FC = () => {
  const [scenario, setScenario] = useState<Scenario>('realistic');

  const { data, isLoading, isError } = useQuery<CashFlowProjection>({
    queryKey: ['cash-flow-projection', scenario],
    queryFn: async () => {
      const response = await apiClient.get(
        `/analytics/cash-flow-projection/?scenario=${scenario}`
      );
      return response.data;
    },
  });

  // Prepare chart data based on scenario
  const chartData = useMemo(() => {
    if (!data?.daily_projections) return [];
    return data.daily_projections.map((dp) => ({
      name: formatDate(dp.date),
      date: dp.date,
      income: dp.income,
      expenses: dp.expenses,
      balance:
        scenario === 'optimistic'
          ? dp.optimistic_balance ?? dp.balance * 1.15
          : scenario === 'conservative'
          ? dp.conservative_balance ?? dp.balance * 0.85
          : dp.balance,
    }));
  }, [data?.daily_projections, scenario]);

  // Cash flow table combining pending invoices and expenses
  const cashFlowEntries = useMemo(() => {
    if (!data) return [];

    const entries: Array<{
      date: string;
      description: string;
      amount: number;
      type: 'income' | 'expense';
      running_balance: number;
    }> = [];

    let runningBalance = data.current_balance;

    // Merge invoices and expenses, sorted by date
    const allItems = [
      ...(data.pending_invoices || []).map((inv) => ({
        date: inv.due_date,
        description: `Invoice ${inv.invoice_number} - ${inv.client_name}`,
        amount: inv.amount,
        type: 'income' as const,
      })),
      ...(data.upcoming_expenses || []).map((exp) => ({
        date: exp.due_date,
        description: `${exp.description} (${exp.category})`,
        amount: exp.amount,
        type: 'expense' as const,
      })),
    ].sort((a, b) => a.date.localeCompare(b.date));

    allItems.forEach((item) => {
      runningBalance += item.type === 'income' ? item.amount : -item.amount;
      entries.push({ ...item, running_balance: runningBalance });
    });

    return entries;
  }, [data]);

  // Scenario button configuration
  const scenarioConfig: Record<Scenario, { label: string; description: string }> = {
    optimistic: { label: 'Optimistic', description: '+15% income adjustment' },
    realistic: { label: 'Realistic', description: 'Based on current data' },
    conservative: { label: 'Conservative', description: '-15% income adjustment' },
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <LoadingSpinner />
          <p className="mt-4 text-gray-500 dark:text-gray-400">Loading cash flow forecast...</p>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">Cash Flow Forecast</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Projected cash flow analysis</p>
        </div>
        <Card>
          <CardContent className="p-12 text-center">
            <div className="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Unable to Load Forecast</h3>
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              Could not retrieve cash flow projection data.
            </p>
            <Link
              to="/analytics"
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/20 rounded-lg hover:bg-primary-100 dark:hover:bg-primary-900/30 transition-colors"
            >
              Back to Analytics
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
              to="/analytics"
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </Link>
            <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">Cash Flow Forecast</h1>
          </div>
          <p className="text-gray-600 dark:text-gray-400 ml-8">
            90-day projected cash flow with scenario analysis
          </p>
        </div>

        {/* Scenario toggle */}
        <div className="flex items-center gap-2">
          {(Object.keys(scenarioConfig) as Scenario[]).map((key) => (
            <button
              key={key}
              onClick={() => setScenario(key)}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200 ${
                scenario === key
                  ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/25'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
              title={scenarioConfig[key].description}
            >
              {scenarioConfig[key].label}
            </button>
          ))}
        </div>
      </div>

      {/* Negative Cash Flow Alert */}
      {data?.negative_cash_flow_alert && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <svg className="w-6 h-6 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div>
              <h4 className="text-sm font-semibold text-red-800 dark:text-red-300">Negative Cash Flow Warning</h4>
              <p className="text-sm text-red-700 dark:text-red-400 mt-1">
                Projected cash flow may become negative
                {data.negative_cash_flow_date
                  ? ` around ${formatFullDate(data.negative_cash_flow_date)}`
                  : ' within the forecast period'}
                . Consider following up on outstanding invoices or adjusting expenses.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card hover className="relative overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Current Balance</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                  {formatCurrency(data?.current_balance || 0)}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Available now</p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/30">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                </svg>
              </div>
            </div>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-400 to-blue-600" />
          </CardContent>
        </Card>

        <Card hover className="relative overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Projected Income (30d)</p>
                <p className="text-2xl font-bold text-green-600 dark:text-green-400 mt-2">
                  +{formatCurrency(data?.projected_income_30d || 0)}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Pending invoices</p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-green-400 to-green-600 rounded-xl flex items-center justify-center shadow-lg shadow-green-500/30">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11l5-5m0 0l5 5m-5-5v12" />
                </svg>
              </div>
            </div>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-green-400 to-green-600" />
          </CardContent>
        </Card>

        <Card hover className="relative overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Projected Expenses (30d)</p>
                <p className="text-2xl font-bold text-red-600 dark:text-red-400 mt-2">
                  -{formatCurrency(data?.projected_expenses_30d || 0)}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Commitments & bills</p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-red-400 to-red-600 rounded-xl flex items-center justify-center shadow-lg shadow-red-500/30">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 13l-5 5m0 0l-5-5m5 5V6" />
                </svg>
              </div>
            </div>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-red-400 to-red-600" />
          </CardContent>
        </Card>

        <Card hover className="relative overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Net Cash Flow</p>
                <p className={`text-2xl font-bold mt-2 ${
                  (data?.net_cash_flow || 0) >= 0
                    ? 'text-green-600 dark:text-green-400'
                    : 'text-red-600 dark:text-red-400'
                }`}>
                  {(data?.net_cash_flow || 0) >= 0 ? '+' : ''}{formatCurrency(data?.net_cash_flow || 0)}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">30-day projection</p>
              </div>
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center shadow-lg ${
                (data?.net_cash_flow || 0) >= 0
                  ? 'bg-gradient-to-br from-emerald-400 to-emerald-600 shadow-emerald-500/30'
                  : 'bg-gradient-to-br from-orange-400 to-orange-600 shadow-orange-500/30'
              }`}>
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
            </div>
            <div className={`absolute bottom-0 left-0 right-0 h-1 ${
              (data?.net_cash_flow || 0) >= 0
                ? 'bg-gradient-to-r from-emerald-400 to-emerald-600'
                : 'bg-gradient-to-r from-orange-400 to-orange-600'
            }`} />
          </CardContent>
        </Card>
      </div>

      {/* Cash Flow Area Chart */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Projected Cash Flow - Next 90 Days</CardTitle>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Scenario: {scenarioConfig[scenario].label} ({scenarioConfig[scenario].description})
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-green-500" />
              <span className="text-xs text-gray-500 dark:text-gray-400">Income</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-blue-500" />
              <span className="text-xs text-gray-500 dark:text-gray-400">Balance</span>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={350}>
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorBalance" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorIncome" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                  </linearGradient>
                </defs>
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
                  formatter={(value: number, name: string) => [
                    formatCurrency(value),
                    name === 'balance' ? 'Balance' : name === 'income' ? 'Income' : 'Expenses',
                  ]}
                />
                <ReferenceLine y={0} stroke="#ef4444" strokeDasharray="3 3" />
                <Area
                  type="monotone"
                  dataKey="income"
                  stroke="#22c55e"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorIncome)"
                />
                <Area
                  type="monotone"
                  dataKey="balance"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorBalance)"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[350px] text-gray-400 dark:text-gray-500">
              <p>No projection data available</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Cash Flow Table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Cash Flow Details</CardTitle>
          <Badge variant="default" size="sm">
            {cashFlowEntries.length} entries
          </Badge>
        </CardHeader>
        <CardContent>
          {cashFlowEntries.length > 0 ? (
            <Table>
              <TableHead>
                <TableRow hoverable={false}>
                  <TableHeaderCell>Date</TableHeaderCell>
                  <TableHeaderCell>Description</TableHeaderCell>
                  <TableHeaderCell align="right">Amount</TableHeaderCell>
                  <TableHeaderCell align="right">Running Balance</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {cashFlowEntries.map((entry, idx) => (
                  <TableRow key={idx}>
                    <TableCell>
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {formatFullDate(entry.date)}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {entry.description}
                      </span>
                    </TableCell>
                    <TableCell align="right">
                      <span className={`font-mono font-semibold ${
                        entry.type === 'income'
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-red-600 dark:text-red-400'
                      }`}>
                        {entry.type === 'income' ? '+' : '-'}{formatCurrency(entry.amount)}
                      </span>
                    </TableCell>
                    <TableCell align="right">
                      <span className={`font-mono font-semibold ${
                        entry.running_balance >= 0
                          ? 'text-gray-900 dark:text-white'
                          : 'text-red-600 dark:text-red-400'
                      }`}>
                        {formatCurrency(entry.running_balance)}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="py-12 text-center">
              <p className="text-gray-500 dark:text-gray-400">No upcoming cash flow entries</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Methodology Note */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center shrink-0">
              <svg className="w-5 h-5 text-primary-600 dark:text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-gray-900 dark:text-white">About this forecast</h4>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Cash flow projections are calculated using pending invoice due dates, recurring billing schedules,
                and estimated expenses. Optimistic scenarios add a 15% buffer to expected income, while conservative
                scenarios reduce income projections by 15%. Actual results may vary.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CashFlowForecast;
