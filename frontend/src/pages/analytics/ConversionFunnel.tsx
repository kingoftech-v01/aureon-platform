/**
 * Conversion Funnel Page
 * Aureon by Rhematek Solutions
 *
 * Lead-to-payment conversion funnel with stage details,
 * time period selector, and drop-off analysis.
 */

import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import apiClient from '@/services/api';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import { LoadingSpinner } from '@/components/common';

// ============================================
// TYPES
// ============================================

type TimePeriod = '7d' | '30d' | '90d' | 'year';

interface FunnelStage {
  name: string;
  count: number;
  value: number;
  conversion_rate: number;
  previous_count?: number;
  previous_value?: number;
}

interface FunnelData {
  stages: FunnelStage[];
  period: string;
  total_leads: number;
  total_paid: number;
  overall_conversion_rate: number;
}

// ============================================
// CONSTANTS
// ============================================

const STAGE_COLORS = [
  { bg: 'bg-blue-500', light: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-600 dark:text-blue-400' },
  { bg: 'bg-indigo-500', light: 'bg-indigo-100 dark:bg-indigo-900/30', text: 'text-indigo-600 dark:text-indigo-400' },
  { bg: 'bg-purple-500', light: 'bg-purple-100 dark:bg-purple-900/30', text: 'text-purple-600 dark:text-purple-400' },
  { bg: 'bg-amber-500', light: 'bg-amber-100 dark:bg-amber-900/30', text: 'text-amber-600 dark:text-amber-400' },
  { bg: 'bg-green-500', light: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-600 dark:text-green-400' },
];

const STAGE_ICONS = [
  // Leads
  <svg key="leads" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>,
  // Proposals
  <svg key="proposals" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>,
  // Contracts
  <svg key="contracts" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
  </svg>,
  // Invoiced
  <svg key="invoiced" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
  </svg>,
  // Paid
  <svg key="paid" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>,
];

const PERIOD_OPTIONS: { key: TimePeriod; label: string }[] = [
  { key: '7d', label: '7 Days' },
  { key: '30d', label: '30 Days' },
  { key: '90d', label: '90 Days' },
  { key: 'year', label: 'Year' },
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

const formatPercent = (value: number): string => `${value.toFixed(1)}%`;

// ============================================
// MAIN COMPONENT
// ============================================

const ConversionFunnel: React.FC = () => {
  const [period, setPeriod] = useState<TimePeriod>('30d');
  const [selectedStage, setSelectedStage] = useState<number | null>(null);

  const { data, isLoading, isError } = useQuery<FunnelData>({
    queryKey: ['conversion-funnel', period],
    queryFn: async () => {
      const response = await apiClient.get(
        `/analytics/conversion-funnel/?period=${period}`
      );
      return response.data;
    },
  });

  // Calculate drop-off between stages
  const dropOffAnalysis = useMemo(() => {
    if (!data?.stages || data.stages.length < 2) return [];
    return data.stages.slice(1).map((stage, idx) => {
      const prevStage = data.stages[idx];
      const dropOff = prevStage.count - stage.count;
      const dropOffRate = prevStage.count > 0 ? (dropOff / prevStage.count) * 100 : 0;
      return {
        from: prevStage.name,
        to: stage.name,
        dropOff,
        dropOffRate,
        valueLost: prevStage.value - stage.value,
      };
    });
  }, [data?.stages]);

  // Max count for scaling the funnel bars
  const maxCount = useMemo(() => {
    if (!data?.stages) return 1;
    return Math.max(...data.stages.map((s) => s.count), 1);
  }, [data?.stages]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <LoadingSpinner />
          <p className="mt-4 text-gray-500 dark:text-gray-400">Loading conversion funnel...</p>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">Conversion Funnel</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Lead-to-payment conversion analysis</p>
        </div>
        <Card>
          <CardContent className="p-12 text-center">
            <div className="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Unable to Load Funnel Data</h3>
            <p className="text-gray-500 dark:text-gray-400 mb-4">Could not retrieve conversion funnel data.</p>
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
            <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">Conversion Funnel</h1>
          </div>
          <p className="text-gray-600 dark:text-gray-400 ml-8">
            Track lead-to-payment conversion across your pipeline
          </p>
        </div>

        {/* Period selector */}
        <div className="flex items-center gap-2">
          {PERIOD_OPTIONS.map((opt) => (
            <button
              key={opt.key}
              onClick={() => setPeriod(opt.key)}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200 ${
                period === opt.key
                  ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/25'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Overall Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card hover className="relative overflow-hidden">
          <CardContent className="p-6">
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Leads</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
              {data?.total_leads || 0}
            </p>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-400 to-blue-600" />
          </CardContent>
        </Card>
        <Card hover className="relative overflow-hidden">
          <CardContent className="p-6">
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Paid</p>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400 mt-2">
              {data?.total_paid || 0}
            </p>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-green-400 to-green-600" />
          </CardContent>
        </Card>
        <Card hover className="relative overflow-hidden">
          <CardContent className="p-6">
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Overall Conversion</p>
            <p className="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-2">
              {formatPercent(data?.overall_conversion_rate || 0)}
            </p>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-400 to-purple-600" />
          </CardContent>
        </Card>
      </div>

      {/* Funnel Visualization */}
      <Card>
        <CardHeader>
          <CardTitle>Pipeline Funnel</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {(data?.stages || []).map((stage, idx) => {
              const color = STAGE_COLORS[idx % STAGE_COLORS.length];
              const widthPercent = Math.max((stage.count / maxCount) * 100, 8);
              const isSelected = selectedStage === idx;

              // Calculate change from previous period
              const countChange = stage.previous_count !== undefined
                ? stage.count - stage.previous_count
                : null;

              return (
                <div key={stage.name}>
                  {/* Funnel bar */}
                  <button
                    onClick={() => setSelectedStage(isSelected ? null : idx)}
                    className="w-full text-left group"
                  >
                    <div className="flex items-center gap-4 mb-2">
                      <div className={`w-10 h-10 rounded-lg ${color.light} ${color.text} flex items-center justify-center flex-shrink-0`}>
                        {STAGE_ICONS[idx]}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-gray-900 dark:text-white">
                              {stage.name}
                            </span>
                            {countChange !== null && (
                              <span className={`inline-flex items-center text-xs font-medium ${
                                countChange >= 0
                                  ? 'text-green-600 dark:text-green-400'
                                  : 'text-red-600 dark:text-red-400'
                              }`}>
                                {countChange >= 0 ? (
                                  <svg className="w-3 h-3 mr-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                                  </svg>
                                ) : (
                                  <svg className="w-3 h-3 mr-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                                  </svg>
                                )}
                                {Math.abs(countChange)}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-4">
                            <span className="text-sm font-bold text-gray-900 dark:text-white">
                              {stage.count}
                            </span>
                            <span className="text-sm text-gray-500 dark:text-gray-400">
                              {formatCurrency(stage.value)}
                            </span>
                            {idx > 0 && (
                              <Badge
                                variant={stage.conversion_rate >= 50 ? 'success' : stage.conversion_rate >= 25 ? 'warning' : 'danger'}
                                size="sm"
                              >
                                {formatPercent(stage.conversion_rate)}
                              </Badge>
                            )}
                          </div>
                        </div>
                        {/* Bar */}
                        <div className="w-full bg-gray-100 dark:bg-gray-800 rounded-full h-8 overflow-hidden">
                          <div
                            className={`h-full ${color.bg} rounded-full transition-all duration-500 flex items-center justify-end pr-3`}
                            style={{ width: `${widthPercent}%` }}
                          >
                            {widthPercent > 20 && (
                              <span className="text-xs font-medium text-white">
                                {formatPercent((stage.count / maxCount) * 100)}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </button>

                  {/* Stage details panel */}
                  {isSelected && (
                    <div className="ml-14 mt-2 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                          <p className="text-xs text-gray-500 dark:text-gray-400">Count</p>
                          <p className="text-lg font-bold text-gray-900 dark:text-white">{stage.count}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 dark:text-gray-400">Total Value</p>
                          <p className="text-lg font-bold text-gray-900 dark:text-white">{formatCurrency(stage.value)}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 dark:text-gray-400">Avg Value</p>
                          <p className="text-lg font-bold text-gray-900 dark:text-white">
                            {formatCurrency(stage.count > 0 ? stage.value / stage.count : 0)}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 dark:text-gray-400">Conversion Rate</p>
                          <p className={`text-lg font-bold ${color.text}`}>
                            {idx === 0 ? '100%' : formatPercent(stage.conversion_rate)}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Drop-off indicator between stages */}
                  {idx < (data?.stages?.length || 0) - 1 && (
                    <div className="ml-14 my-2 flex items-center gap-2">
                      <svg className="w-4 h-4 text-gray-400 dark:text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                      </svg>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {dropOffAnalysis[idx]
                          ? `${dropOffAnalysis[idx].dropOff} dropped off (${formatPercent(dropOffAnalysis[idx].dropOffRate)})`
                          : ''}
                      </span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Drop-off Analysis */}
      {dropOffAnalysis.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Drop-off Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {dropOffAnalysis.map((analysis, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700"
                >
                  <div className="flex items-center gap-3">
                    <div className="text-sm font-medium text-gray-900 dark:text-white">
                      {analysis.from}
                    </div>
                    <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                    </svg>
                    <div className="text-sm font-medium text-gray-900 dark:text-white">
                      {analysis.to}
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-sm font-semibold text-red-600 dark:text-red-400">
                        -{analysis.dropOff} ({formatPercent(analysis.dropOffRate)})
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {formatCurrency(analysis.valueLost)} lost
                      </p>
                    </div>
                    <div
                      className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden"
                    >
                      <div
                        className="h-full bg-red-500 rounded-full"
                        style={{ width: `${Math.min(analysis.dropOffRate, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ConversionFunnel;
