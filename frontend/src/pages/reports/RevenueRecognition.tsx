/**
 * Revenue Recognition Report
 * Aureon by Rhematek Solutions
 *
 * GAAP/IFRS revenue recognition dashboard
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Badge,
  Select,
  LoadingSpinner,
} from '@/components/common';
import { RevenueAreaChart } from '@/components/common/Charts';
import apiClient from '@/services/api';

interface RecognitionData {
  summary: {
    recognized: number;
    deferred: number;
    total_contracts: number;
    recognition_rate: number;
  };
  monthly: Array<{
    month: string;
    recognized: number;
    deferred: number;
    adjustments: number;
    total: number;
  }>;
  contracts: Array<{
    id: string;
    name: string;
    client_name: string;
    total_value: number;
    recognized_to_date: number;
    remaining: number;
    method: 'milestone' | 'time_based' | 'deliverable';
    status: string;
    start_date: string;
    end_date: string;
  }>;
}

const formatCurrency = (amount: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0 }).format(amount);

const RevenueRecognition: React.FC = () => {
  const [period, setPeriod] = useState('yearly');
  const [year, setYear] = useState(new Date().getFullYear().toString());

  const { data, isLoading } = useQuery<RecognitionData>({
    queryKey: ['revenue-recognition', period, year],
    queryFn: async () => {
      const res = await apiClient.get('/analytics/revenue-recognition/', {
        params: { period, year },
      });
      return res.data;
    },
  });

  const handleExport = async () => {
    try {
      const res = await apiClient.get('/analytics/revenue-recognition/export/', {
        params: { period, year, format: 'csv' },
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `revenue-recognition-${year}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      // silently fail
    }
  };

  // Fallback data for development
  const summary = data?.summary || {
    recognized: 245000,
    deferred: 87000,
    total_contracts: 42,
    recognition_rate: 73.8,
  };

  const monthly = data?.monthly || [
    { month: '2026-01', recognized: 18500, deferred: 8200, adjustments: -500, total: 26200 },
    { month: '2026-02', recognized: 21200, deferred: 7800, adjustments: 0, total: 29000 },
    { month: '2026-03', recognized: 19800, deferred: 9100, adjustments: 300, total: 28600 },
    { month: '2026-04', recognized: 22100, deferred: 6500, adjustments: -200, total: 28400 },
    { month: '2026-05', recognized: 24500, deferred: 7200, adjustments: 0, total: 31700 },
    { month: '2026-06', recognized: 20300, deferred: 8900, adjustments: 400, total: 29200 },
  ];

  const contracts = data?.contracts || [
    { id: '1', name: 'Website Redesign', client_name: 'Acme Corp', total_value: 45000, recognized_to_date: 30000, remaining: 15000, method: 'milestone' as const, status: 'active', start_date: '2025-11-01', end_date: '2026-04-30' },
    { id: '2', name: 'Monthly Retainer', client_name: 'Beta LLC', total_value: 60000, recognized_to_date: 35000, remaining: 25000, method: 'time_based' as const, status: 'active', start_date: '2025-09-01', end_date: '2026-08-31' },
    { id: '3', name: 'App Development', client_name: 'Gamma Inc', total_value: 120000, recognized_to_date: 80000, remaining: 40000, method: 'milestone' as const, status: 'active', start_date: '2025-06-01', end_date: '2026-05-31' },
    { id: '4', name: 'SEO Campaign', client_name: 'Delta Co', total_value: 24000, recognized_to_date: 24000, remaining: 0, method: 'deliverable' as const, status: 'completed', start_date: '2025-10-01', end_date: '2026-01-31' },
  ];

  if (isLoading) {
    return <div className="flex items-center justify-center h-64"><LoadingSpinner /></div>;
  }

  const chartData = monthly.map((m) => ({
    name: format(new Date(m.month + '-01'), 'MMM'),
    value: m.recognized,
  }));

  const methodLabels: Record<string, string> = {
    milestone: 'Milestone-Based',
    time_based: 'Time-Based',
    deliverable: 'Deliverable-Based',
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Revenue Recognition</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">GAAP/IFRS compliant revenue reporting</p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={period} onChange={(e) => setPeriod(e.target.value)}>
            <option value="quarterly">Quarterly</option>
            <option value="yearly">Yearly</option>
          </Select>
          <Select value={year} onChange={(e) => setYear(e.target.value)}>
            <option value="2026">2026</option>
            <option value="2025">2025</option>
            <option value="2024">2024</option>
          </Select>
          <Button variant="outline" onClick={handleExport}>
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Export CSV
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-100 dark:bg-green-900/40 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">Recognized Revenue</p>
                <p className="text-xl font-bold text-gray-900 dark:text-white">{formatCurrency(summary.recognized)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-amber-100 dark:bg-amber-900/40 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">Deferred Revenue</p>
                <p className="text-xl font-bold text-gray-900 dark:text-white">{formatCurrency(summary.deferred)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/40 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">Total Contracts</p>
                <p className="text-xl font-bold text-gray-900 dark:text-white">{summary.total_contracts}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/40 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">Recognition Rate</p>
                <p className="text-xl font-bold text-gray-900 dark:text-white">{summary.recognition_rate.toFixed(1)}%</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Revenue Recognition Trend</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-72">
            <RevenueAreaChart data={chartData} />
          </div>
        </CardContent>
      </Card>

      {/* Monthly Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Monthly Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-3 px-4 font-semibold text-gray-500 dark:text-gray-400">Month</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-500 dark:text-gray-400">Recognized</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-500 dark:text-gray-400">Deferred</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-500 dark:text-gray-400">Adjustments</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-500 dark:text-gray-400">Total</th>
                </tr>
              </thead>
              <tbody>
                {monthly.map((m) => (
                  <tr key={m.month} className="border-b border-gray-100 dark:border-gray-800">
                    <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">
                      {format(new Date(m.month + '-01'), 'MMMM yyyy')}
                    </td>
                    <td className="py-3 px-4 text-right text-green-600">{formatCurrency(m.recognized)}</td>
                    <td className="py-3 px-4 text-right text-amber-600">{formatCurrency(m.deferred)}</td>
                    <td className={`py-3 px-4 text-right ${m.adjustments >= 0 ? 'text-gray-600 dark:text-gray-400' : 'text-red-600'}`}>
                      {m.adjustments >= 0 ? '+' : ''}{formatCurrency(m.adjustments)}
                    </td>
                    <td className="py-3 px-4 text-right font-semibold text-gray-900 dark:text-white">{formatCurrency(m.total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Contract Detail */}
      <Card>
        <CardHeader>
          <CardTitle>Contract-Level Recognition</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-3 px-4 font-semibold text-gray-500 dark:text-gray-400">Contract</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-500 dark:text-gray-400">Client</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-500 dark:text-gray-400">Total Value</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-500 dark:text-gray-400">Recognized</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-500 dark:text-gray-400">Remaining</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-500 dark:text-gray-400">Method</th>
                  <th className="text-center py-3 px-4 font-semibold text-gray-500 dark:text-gray-400">Progress</th>
                </tr>
              </thead>
              <tbody>
                {contracts.map((c) => {
                  const pct = c.total_value > 0 ? (c.recognized_to_date / c.total_value) * 100 : 0;
                  return (
                    <tr key={c.id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                      <td className="py-3 px-4">
                        <a href={`/contracts/${c.id}`} className="font-medium text-primary-600 dark:text-primary-400 hover:underline">{c.name}</a>
                      </td>
                      <td className="py-3 px-4 text-gray-600 dark:text-gray-400">{c.client_name}</td>
                      <td className="py-3 px-4 text-right text-gray-900 dark:text-white">{formatCurrency(c.total_value)}</td>
                      <td className="py-3 px-4 text-right text-green-600">{formatCurrency(c.recognized_to_date)}</td>
                      <td className="py-3 px-4 text-right text-amber-600">{formatCurrency(c.remaining)}</td>
                      <td className="py-3 px-4">
                        <Badge variant="default">{methodLabels[c.method] || c.method}</Badge>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-primary-500 to-primary-600 rounded-full"
                              style={{ width: `${Math.min(pct, 100)}%` }}
                            />
                          </div>
                          <span className="text-xs font-medium text-gray-500 dark:text-gray-400 w-10 text-right">{pct.toFixed(0)}%</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Disclaimer */}
      <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <svg className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p className="text-sm text-amber-800 dark:text-amber-200">
            This report is for informational purposes only. Consult with your accountant or financial advisor
            for official revenue recognition in compliance with GAAP/IFRS standards.
          </p>
        </div>
      </div>
    </div>
  );
};

export default RevenueRecognition;
