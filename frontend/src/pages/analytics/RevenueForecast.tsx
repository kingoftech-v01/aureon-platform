/**
 * Revenue Forecast Page
 * Aureon by Rhematek Solutions
 *
 * AI-powered revenue projections with historical data and confidence indicators
 */

import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { analyticsService } from '@/services/analyticsService';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import { LoadingSpinner } from '@/components/common';
import { RevenueAreaChart } from '@/components/common/Charts';

interface ForecastDataPoint {
  month: string;
  revenue: number;
  confidence?: number;
}

interface ForecastResponse {
  history: ForecastDataPoint[];
  forecast: ForecastDataPoint[];
  recurring_monthly_revenue: number;
  pending_receivables: number;
  trend: 'up' | 'down' | 'stable';
  average_monthly_revenue: number;
}

const RevenueForecast: React.FC = () => {
  const [forecastMonths, setForecastMonths] = useState<number>(6);

  const { data, isLoading, error } = useQuery<ForecastResponse>({
    queryKey: ['revenue-forecast', forecastMonths],
    queryFn: async () => {
      const response = await analyticsService.getRevenueForecast({ months: forecastMonths });
      return response;
    },
  });

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatMonth = (monthStr: string) => {
    try {
      const date = new Date(monthStr + '-01');
      return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
    } catch {
      return monthStr;
    }
  };

  // Prepare chart data for the historical revenue
  const historyChartData = useMemo(() => {
    if (!data?.history) return [];
    return data.history.map((item) => ({
      name: formatMonth(item.month),
      value: item.revenue,
    }));
  }, [data?.history]);

  // Prepare chart data for the forecast projection
  const forecastChartData = useMemo(() => {
    if (!data?.forecast) return [];
    return data.forecast.map((item) => ({
      name: formatMonth(item.month),
      value: item.revenue,
    }));
  }, [data?.forecast]);

  // Combined chart data: history + forecast bridged by last history point
  const combinedChartData = useMemo(() => {
    if (!data?.history && !data?.forecast) return [];

    const historyPoints = (data?.history || []).map((item) => ({
      name: formatMonth(item.month),
      actual: item.revenue,
      forecast: undefined as number | undefined,
    }));

    // Bridge: last history point also appears as first forecast point
    const lastHistory = data?.history?.[data.history.length - 1];
    const forecastPoints = (data?.forecast || []).map((item) => ({
      name: formatMonth(item.month),
      actual: undefined as number | undefined,
      forecast: item.revenue,
    }));

    if (lastHistory && forecastPoints.length > 0) {
      // Add the bridge point: last history value as forecast start
      forecastPoints.unshift({
        name: formatMonth(lastHistory.month),
        actual: lastHistory.revenue,
        forecast: lastHistory.revenue,
      });
    }

    return { historyPoints, forecastPoints };
  }, [data?.history, data?.forecast]);

  const trendConfig = {
    up: {
      label: 'Upward',
      color: 'text-green-600 dark:text-green-400',
      bg: 'bg-green-100 dark:bg-green-900/30',
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
      ),
    },
    down: {
      label: 'Downward',
      color: 'text-red-600 dark:text-red-400',
      bg: 'bg-red-100 dark:bg-red-900/30',
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
        </svg>
      ),
    },
    stable: {
      label: 'Stable',
      color: 'text-blue-600 dark:text-blue-400',
      bg: 'bg-blue-100 dark:bg-blue-900/30',
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14" />
        </svg>
      ),
    },
  };

  const currentTrend = data?.trend ? trendConfig[data.trend] : trendConfig.stable;

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'bg-green-500';
    if (confidence >= 60) return 'bg-blue-500';
    if (confidence >= 40) return 'bg-amber-500';
    return 'bg-red-500';
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 80) return 'High';
    if (confidence >= 60) return 'Moderate';
    if (confidence >= 40) return 'Low';
    return 'Very Low';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <LoadingSpinner />
          <p className="mt-4 text-gray-500 dark:text-gray-400">Loading revenue forecast...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">Revenue Forecast</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">AI-powered revenue projections</p>
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
              We could not retrieve your revenue forecast data. This may happen if there is not enough historical data available yet.
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
            <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">Revenue Forecast</h1>
          </div>
          <p className="text-gray-600 dark:text-gray-400 ml-8">
            AI-powered revenue projections and trend analysis
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500 dark:text-gray-400 mr-1">Forecast range:</span>
          {[3, 6, 12].map((months) => (
            <button
              key={months}
              onClick={() => setForecastMonths(months)}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200 ${
                forecastMonths === months
                  ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/25'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
            >
              {months}mo
            </button>
          ))}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Average Monthly Revenue */}
        <Card hover className="relative overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Avg Monthly Revenue</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                  {formatCurrency(data?.average_monthly_revenue || 0)}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">Based on last 12 months</p>
              </div>
              <div className="w-14 h-14 bg-gradient-to-br from-blue-400 to-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/30">
                <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
            </div>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-400 to-blue-600" />
          </CardContent>
        </Card>

        {/* Trend */}
        <Card hover className="relative overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Revenue Trend</p>
                <p className={`text-2xl font-bold mt-2 ${currentTrend.color}`}>
                  {currentTrend.label}
                </p>
                <div className="mt-2">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${currentTrend.bg} ${currentTrend.color}`}>
                    {currentTrend.icon}
                    <span className="ml-1">{data?.trend === 'up' ? 'Growing' : data?.trend === 'down' ? 'Declining' : 'Flat'}</span>
                  </span>
                </div>
              </div>
              <div className={`w-14 h-14 rounded-xl flex items-center justify-center shadow-lg ${
                data?.trend === 'up'
                  ? 'bg-gradient-to-br from-green-400 to-green-600 shadow-green-500/30'
                  : data?.trend === 'down'
                  ? 'bg-gradient-to-br from-red-400 to-red-600 shadow-red-500/30'
                  : 'bg-gradient-to-br from-blue-400 to-blue-600 shadow-blue-500/30'
              }`}>
                <span className="text-white">{currentTrend.icon}</span>
              </div>
            </div>
            <div className={`absolute bottom-0 left-0 right-0 h-1 ${
              data?.trend === 'up'
                ? 'bg-gradient-to-r from-green-400 to-green-600'
                : data?.trend === 'down'
                ? 'bg-gradient-to-r from-red-400 to-red-600'
                : 'bg-gradient-to-r from-blue-400 to-blue-600'
            }`} />
          </CardContent>
        </Card>

        {/* Recurring Monthly Revenue */}
        <Card hover className="relative overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Recurring Revenue</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                  {formatCurrency(data?.recurring_monthly_revenue || 0)}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">Monthly recurring (MRR)</p>
              </div>
              <div className="w-14 h-14 bg-gradient-to-br from-purple-400 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/30">
                <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </div>
            </div>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-400 to-purple-600" />
          </CardContent>
        </Card>

        {/* Pending Receivables */}
        <Card hover className="relative overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Pending Receivables</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                  {formatCurrency(data?.pending_receivables || 0)}
                </p>
                <p className="text-xs text-amber-600 dark:text-amber-400 mt-2">Awaiting collection</p>
              </div>
              <div className="w-14 h-14 bg-gradient-to-br from-amber-400 to-amber-600 rounded-xl flex items-center justify-center shadow-lg shadow-amber-500/30">
                <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-400 to-amber-600" />
          </CardContent>
        </Card>
      </div>

      {/* Historical Revenue Chart */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Historical Revenue</CardTitle>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Last 12 months of actual revenue</p>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-blue-500" />
              <span className="text-xs text-gray-500 dark:text-gray-400">Actual</span>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {historyChartData.length > 0 ? (
            <RevenueAreaChart
              data={historyChartData}
              height={300}
              color="#3b82f6"
              gradientId="colorHistorical"
            />
          ) : (
            <div className="flex items-center justify-center h-[300px] text-gray-400 dark:text-gray-500">
              <p>No historical data available</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Forecast Projection Chart */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Revenue Projection</CardTitle>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Next {forecastMonths} months forecast based on AI analysis
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-emerald-500" />
              <span className="text-xs text-gray-500 dark:text-gray-400">Projected</span>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {forecastChartData.length > 0 ? (
            <RevenueAreaChart
              data={forecastChartData}
              height={300}
              color="#10b981"
              gradientId="colorForecast"
            />
          ) : (
            <div className="flex items-center justify-center h-[300px] text-gray-400 dark:text-gray-500">
              <p>Insufficient data for forecast projections</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Confidence Indicators */}
      {data?.forecast && data.forecast.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Forecast Confidence</CardTitle>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Confidence level for each forecasted month
            </p>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {data.forecast.map((item, index) => {
                const confidence = item.confidence ?? Math.max(90 - index * 8, 30);
                return (
                  <div key={item.month} className="flex items-center gap-4">
                    <div className="w-24 text-sm font-medium text-gray-700 dark:text-gray-300 shrink-0">
                      {formatMonth(item.month)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${getConfidenceColor(confidence)}`}
                            style={{ width: `${confidence}%` }}
                          />
                        </div>
                        <div className="w-16 text-right">
                          <span className={`text-sm font-semibold ${
                            confidence >= 80
                              ? 'text-green-600 dark:text-green-400'
                              : confidence >= 60
                              ? 'text-blue-600 dark:text-blue-400'
                              : confidence >= 40
                              ? 'text-amber-600 dark:text-amber-400'
                              : 'text-red-600 dark:text-red-400'
                          }`}>
                            {confidence}%
                          </span>
                        </div>
                        <div className="w-20">
                          <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                            confidence >= 80
                              ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                              : confidence >= 60
                              ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                              : confidence >= 40
                              ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                              : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                          }`}>
                            {getConfidenceLabel(confidence)}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="w-28 text-right text-sm font-medium text-gray-900 dark:text-white shrink-0">
                      {formatCurrency(item.revenue)}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Legend */}
            <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
              <div className="flex flex-wrap items-center gap-4">
                <span className="text-xs text-gray-500 dark:text-gray-400">Confidence levels:</span>
                <div className="flex items-center gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-green-500" />
                  <span className="text-xs text-gray-600 dark:text-gray-400">High (80%+)</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-blue-500" />
                  <span className="text-xs text-gray-600 dark:text-gray-400">Moderate (60-79%)</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-amber-500" />
                  <span className="text-xs text-gray-600 dark:text-gray-400">Low (40-59%)</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-red-500" />
                  <span className="text-xs text-gray-600 dark:text-gray-400">Very Low (&lt;40%)</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

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
                Revenue projections are generated using AI analysis of your historical revenue patterns,
                recurring contracts, seasonal trends, and current pipeline. Confidence decreases for
                months further into the future. Forecasts are recalculated daily as new data becomes available.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default RevenueForecast;
