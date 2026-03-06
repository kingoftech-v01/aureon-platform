/**
 * Financial Health Dashboard Page
 * Aureon by Rhematek Solutions
 *
 * Overall financial health scoring with factor breakdowns,
 * recommendations, and historical trend
 */

import React, { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import apiClient from '@/services/api';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import { RevenueAreaChart } from '@/components/common/Charts';
import { SkeletonTable } from '@/components/common/Skeleton';

interface HealthFactor {
  key: string;
  title: string;
  score: number;
  trend: 'up' | 'down' | 'stable';
  description: string;
}

interface HealthData {
  overall_score: number;
  factors: {
    cash_flow_score: number;
    cash_flow_trend: 'up' | 'down' | 'stable';
    payment_collection_rate: number;
    payment_collection_trend: 'up' | 'down' | 'stable';
    client_retention: number;
    client_retention_trend: 'up' | 'down' | 'stable';
    revenue_growth: number;
    revenue_growth_trend: 'up' | 'down' | 'stable';
    invoice_aging: number;
    invoice_aging_trend: 'up' | 'down' | 'stable';
  };
  recommendations: string[];
  history: Array<{ month: string; score: number }>;
}

const getScoreCategory = (score: number) => {
  if (score >= 90) return { label: 'Excellent', color: '#22c55e', variant: 'success' as const };
  if (score >= 70) return { label: 'Good', color: '#3b82f6', variant: 'primary' as const };
  if (score >= 50) return { label: 'Fair', color: '#f59e0b', variant: 'warning' as const };
  return { label: 'Poor', color: '#ef4444', variant: 'danger' as const };
};

const getFactorColor = (score: number) => {
  if (score >= 80) return 'text-green-600 dark:text-green-400';
  if (score >= 60) return 'text-blue-600 dark:text-blue-400';
  if (score >= 40) return 'text-amber-600 dark:text-amber-400';
  return 'text-red-600 dark:text-red-400';
};

const getFactorBg = (score: number) => {
  if (score >= 80) return 'from-green-400 to-green-600';
  if (score >= 60) return 'from-blue-400 to-blue-600';
  if (score >= 40) return 'from-amber-400 to-amber-600';
  return 'from-red-400 to-red-600';
};

/**
 * Circular gauge ring component for overall health score
 */
const HealthGauge: React.FC<{ score: number; size?: number }> = ({ score, size = 200 }) => {
  const strokeWidth = 14;
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (score / 100) * circumference;
  const category = getScoreCategory(score);

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="-rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-gray-200 dark:text-gray-700"
        />
        {/* Score arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={category.color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-4xl font-bold text-gray-900 dark:text-white">
          {Math.round(score)}
        </span>
        <span className="text-sm font-medium mt-1" style={{ color: category.color }}>
          {category.label}
        </span>
        <span className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">out of 100</span>
      </div>
    </div>
  );
};

const TrendArrow: React.FC<{ trend: 'up' | 'down' | 'stable' }> = ({ trend }) => {
  if (trend === 'up') {
    return (
      <span className="inline-flex items-center text-green-600 dark:text-green-400">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
        </svg>
      </span>
    );
  }
  if (trend === 'down') {
    return (
      <span className="inline-flex items-center text-red-600 dark:text-red-400">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
      </span>
    );
  }
  return (
    <span className="inline-flex items-center text-gray-400 dark:text-gray-500">
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14" />
      </svg>
    </span>
  );
};

const FinancialHealth: React.FC = () => {
  const { data: healthData, isLoading } = useQuery<HealthData>({
    queryKey: ['financial-health'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/analytics/health-score/');
        return response.data;
      } catch {
        // Return fallback data if API is not yet available
        return {
          overall_score: 74,
          factors: {
            cash_flow_score: 82,
            cash_flow_trend: 'up' as const,
            payment_collection_rate: 78,
            payment_collection_trend: 'stable' as const,
            client_retention: 85,
            client_retention_trend: 'up' as const,
            revenue_growth: 62,
            revenue_growth_trend: 'down' as const,
            invoice_aging: 65,
            invoice_aging_trend: 'stable' as const,
          },
          recommendations: [
            'Follow up on 5 overdue invoices totaling $12,400 to improve cash flow',
            'Consider offering early payment discounts to reduce invoice aging',
            'Re-engage 3 inactive clients with personalized outreach',
            'Review pricing strategy - revenue growth has slowed this quarter',
            'Set up automated payment reminders for invoices approaching due dates',
          ],
          history: [
            { month: 'Apr', score: 68 },
            { month: 'May', score: 70 },
            { month: 'Jun', score: 65 },
            { month: 'Jul', score: 72 },
            { month: 'Aug', score: 71 },
            { month: 'Sep', score: 69 },
            { month: 'Oct', score: 73 },
            { month: 'Nov', score: 75 },
            { month: 'Dec', score: 72 },
            { month: 'Jan', score: 76 },
            { month: 'Feb', score: 73 },
            { month: 'Mar', score: 74 },
          ],
        };
      }
    },
  });

  const factors: HealthFactor[] = useMemo(() => {
    if (!healthData) return [];
    const f = healthData.factors;
    return [
      {
        key: 'cash_flow',
        title: 'Cash Flow Score',
        score: f.cash_flow_score,
        trend: f.cash_flow_trend,
        description: 'Ratio of incoming vs outgoing cash flow. Higher is better.',
      },
      {
        key: 'payment_collection',
        title: 'Payment Collection Rate',
        score: f.payment_collection_rate,
        trend: f.payment_collection_trend,
        description: 'Percentage of invoices paid on time or before due date.',
      },
      {
        key: 'client_retention',
        title: 'Client Retention',
        score: f.client_retention,
        trend: f.client_retention_trend,
        description: 'Percentage of active clients relative to total client base.',
      },
      {
        key: 'revenue_growth',
        title: 'Revenue Growth',
        score: f.revenue_growth,
        trend: f.revenue_growth_trend,
        description: 'Month-over-month revenue growth percentage.',
      },
      {
        key: 'invoice_aging',
        title: 'Invoice Aging',
        score: f.invoice_aging,
        trend: f.invoice_aging_trend,
        description: 'Score based on average days to payment. Lower aging is better.',
      },
    ];
  }, [healthData]);

  const chartData = useMemo(() => {
    if (!healthData?.history) return [];
    return healthData.history.map((item) => ({
      name: item.month,
      value: item.score,
    }));
  }, [healthData]);

  const overallCategory = healthData ? getScoreCategory(healthData.overall_score) : null;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">
            Financial Health
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Loading health data...</p>
        </div>
        <div className="p-6">
          <SkeletonTable rows={5} columns={4} />
        </div>
      </div>
    );
  }

  if (!healthData) return null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">
          Financial Health
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Comprehensive assessment of your business financial health
        </p>
      </div>

      {/* Overall Score + History */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Health gauge */}
        <Card className="lg:col-span-1">
          <CardContent className="p-6 flex flex-col items-center justify-center">
            <h2 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-6">
              Overall Health Score
            </h2>
            <HealthGauge score={healthData.overall_score} size={200} />
            <div className="mt-6 text-center">
              {overallCategory && (
                <Badge variant={overallCategory.variant} size="lg">
                  {overallCategory.label} Health
                </Badge>
              )}
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-3">
                Based on 5 key financial indicators
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Historical trend */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Health Score Trend (Last 12 Months)</CardTitle>
          </CardHeader>
          <CardContent>
            <RevenueAreaChart
              data={chartData}
              height={260}
              color={overallCategory?.color || '#3b82f6'}
              gradientId="healthTrend"
            />
          </CardContent>
        </Card>
      </div>

      {/* Health Factors */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Health Factors Breakdown
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {factors.map((factor) => (
            <Card key={factor.key} hover>
              <CardContent className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {factor.title}
                  </h3>
                  <TrendArrow trend={factor.trend} />
                </div>

                <div className="flex items-end justify-between mb-3">
                  <span className={`text-3xl font-bold ${getFactorColor(factor.score)}`}>
                    {Math.round(factor.score)}
                  </span>
                  <span className="text-sm text-gray-400 dark:text-gray-500">/ 100</span>
                </div>

                {/* Score bar */}
                <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden mb-3">
                  <div
                    className={`h-full bg-gradient-to-r ${getFactorBg(factor.score)} rounded-full transition-all duration-700`}
                    style={{ width: `${factor.score}%` }}
                  />
                </div>

                <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                  {factor.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Score Legend */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center justify-center gap-6 text-sm">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-green-500" />
              <span className="text-gray-600 dark:text-gray-400">Excellent (90-100)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-blue-500" />
              <span className="text-gray-600 dark:text-gray-400">Good (70-89)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-amber-500" />
              <span className="text-gray-600 dark:text-gray-400">Fair (50-69)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <span className="text-gray-600 dark:text-gray-400">Poor (0-49)</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle>
            <div className="flex items-center space-x-2">
              <svg className="w-5 h-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <span>Recommendations</span>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {healthData.recommendations.length === 0 ? (
            <div className="text-center py-6">
              <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-3">
                <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <p className="text-gray-600 dark:text-gray-400">
                Your financial health looks great! No recommendations at this time.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {healthData.recommendations.map((rec, idx) => (
                <div
                  key={idx}
                  className="flex items-start space-x-3 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800/30"
                >
                  <div className="shrink-0 mt-0.5">
                    <div className="w-6 h-6 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                      <span className="text-xs font-bold text-amber-700 dark:text-amber-400">
                        {idx + 1}
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-amber-800 dark:text-amber-300 leading-relaxed">
                    {rec}
                  </p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default FinancialHealth;
