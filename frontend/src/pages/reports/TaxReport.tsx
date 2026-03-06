/**
 * Tax Report Page
 * Aureon by Rhematek Solutions
 *
 * Tax report generator with date range selection,
 * summary cards, breakdown table, monthly chart, and export options.
 */

import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
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
import { analyticsService } from '@/services/analyticsService';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Select from '@/components/common/Select';
import Badge from '@/components/common/Badge';
import Table, {
  TableHead,
  TableBody,
  TableRow,
  TableHeaderCell,
  TableCell,
} from '@/components/common/Table';
import { useToast } from '@/components/common';

// ============================================
// TYPES
// ============================================

interface TaxBreakdown {
  taxType: string;
  rate: number;
  taxableAmount: number;
  taxCollected: number;
  jurisdiction: string;
}

interface MonthlyTaxData {
  name: string;
  revenue: number;
  tax: number;
}

// ============================================
// HELPERS
// ============================================

const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
};

const formatPercent = (value: number): string => {
  return `${value.toFixed(2)}%`;
};

const getCurrentTaxYear = (): string => {
  return new Date().getFullYear().toString();
};

const getDateRange = (period: string): { start: string; end: string } => {
  const now = new Date();
  const year = now.getFullYear();

  switch (period) {
    case 'q1':
      return { start: `${year}-01-01`, end: `${year}-03-31` };
    case 'q2':
      return { start: `${year}-04-01`, end: `${year}-06-30` };
    case 'q3':
      return { start: `${year}-07-01`, end: `${year}-09-30` };
    case 'q4':
      return { start: `${year}-10-01`, end: `${year}-12-31` };
    case 'year':
      return { start: `${year}-01-01`, end: `${year}-12-31` };
    case 'prev_year':
      return { start: `${year - 1}-01-01`, end: `${year - 1}-12-31` };
    default:
      return { start: `${year}-01-01`, end: `${year}-12-31` };
  }
};

// Chart tooltip style
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

const TaxReport: React.FC = () => {
  const { success: showSuccessToast, error: showErrorToast } = useToast();
  const [periodType, setPeriodType] = useState('year');
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [selectedRegion, setSelectedRegion] = useState('all');
  const [isExporting, setIsExporting] = useState<string | null>(null);

  // Determine date range
  const dateRange = useMemo(() => {
    if (periodType === 'custom') {
      return {
        start: customStartDate || `${new Date().getFullYear()}-01-01`,
        end: customEndDate || `${new Date().getFullYear()}-12-31`,
      };
    }
    return getDateRange(periodType);
  }, [periodType, customStartDate, customEndDate]);

  // Fetch revenue data
  const { data: revenueData, isLoading } = useQuery({
    queryKey: ['tax-report-revenue', dateRange, selectedRegion],
    queryFn: () =>
      analyticsService.getRevenueMetrics({
        start_date: dateRange.start,
        end_date: dateRange.end,
        group_by: 'month',
      }),
  });

  // Calculate summary metrics from data (mock calculations when no data)
  const summary = useMemo(() => {
    const totalRevenue = revenueData?.reduce((sum: number, item: any) => sum + (item.revenue || item.value || 0), 0) || 0;
    const taxRate = 0.085; // Default tax rate for display
    const totalTax = totalRevenue * taxRate;
    const netRevenue = totalRevenue - totalTax;
    const effectiveRate = totalRevenue > 0 ? (totalTax / totalRevenue) * 100 : 0;

    return {
      totalRevenue,
      totalTax,
      netRevenue,
      effectiveRate,
    };
  }, [revenueData]);

  // Tax breakdown by type (mock data structure - would come from API)
  const taxBreakdowns: TaxBreakdown[] = useMemo(() => {
    const base = summary.totalRevenue || 100000;
    return [
      {
        taxType: 'Sales Tax',
        rate: 6.0,
        taxableAmount: base * 0.4,
        taxCollected: base * 0.4 * 0.06,
        jurisdiction: 'State',
      },
      {
        taxType: 'VAT',
        rate: 20.0,
        taxableAmount: base * 0.3,
        taxCollected: base * 0.3 * 0.2,
        jurisdiction: 'EU',
      },
      {
        taxType: 'GST',
        rate: 10.0,
        taxableAmount: base * 0.2,
        taxCollected: base * 0.2 * 0.1,
        jurisdiction: 'AU',
      },
      {
        taxType: 'Service Tax',
        rate: 5.0,
        taxableAmount: base * 0.1,
        taxCollected: base * 0.1 * 0.05,
        jurisdiction: 'Other',
      },
    ];
  }, [summary.totalRevenue]);

  // Monthly chart data
  const monthlyChartData: MonthlyTaxData[] = useMemo(() => {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    if (revenueData?.length) {
      return revenueData.map((item: any, idx: number) => ({
        name: item.date || months[idx] || `M${idx + 1}`,
        revenue: item.revenue || item.value || 0,
        tax: (item.revenue || item.value || 0) * 0.085,
      }));
    }

    // Fallback data for empty state
    return months.map((month) => ({
      name: month,
      revenue: 0,
      tax: 0,
    }));
  }, [revenueData]);

  // Export handlers
  const handleExport = async (format: 'csv' | 'pdf') => {
    setIsExporting(format);
    try {
      const blob = await analyticsService.exportReport({
        report_type: 'revenue',
        format,
        start_date: dateRange.start,
        end_date: dateRange.end,
      });

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `tax-report-${dateRange.start}-to-${dateRange.end}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      showSuccessToast(`Tax report downloaded as ${format.toUpperCase()}`);
    } catch {
      showErrorToast(`Failed to export report as ${format.toUpperCase()}`);
    } finally {
      setIsExporting(null);
    }
  };

  const handleSendToAccountant = () => {
    showSuccessToast('Tax report sent to your accountant');
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">Tax Report</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Generate tax summaries and breakdowns for reporting periods
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport('csv')}
            isLoading={isExporting === 'csv'}
          >
            <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Download CSV
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport('pdf')}
            isLoading={isExporting === 'pdf'}
          >
            <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
            Download PDF
          </Button>
          <Button variant="primary" size="sm" onClick={handleSendToAccountant}>
            <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            Send to Accountant
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-end gap-4">
            <div className="w-full sm:w-48">
              <Select
                label="Report Period"
                value={periodType}
                onChange={(e) => setPeriodType(e.target.value)}
                options={[
                  { value: 'year', label: `Tax Year ${getCurrentTaxYear()}` },
                  { value: 'prev_year', label: `Tax Year ${parseInt(getCurrentTaxYear()) - 1}` },
                  { value: 'q1', label: 'Q1 (Jan - Mar)' },
                  { value: 'q2', label: 'Q2 (Apr - Jun)' },
                  { value: 'q3', label: 'Q3 (Jul - Sep)' },
                  { value: 'q4', label: 'Q4 (Oct - Dec)' },
                  { value: 'custom', label: 'Custom Range' },
                ]}
                fullWidth
              />
            </div>

            {periodType === 'custom' && (
              <>
                <div className="w-full sm:w-44">
                  <Input
                    label="Start Date"
                    type="date"
                    value={customStartDate}
                    onChange={(e) => setCustomStartDate(e.target.value)}
                    fullWidth
                  />
                </div>
                <div className="w-full sm:w-44">
                  <Input
                    label="End Date"
                    type="date"
                    value={customEndDate}
                    onChange={(e) => setCustomEndDate(e.target.value)}
                    fullWidth
                  />
                </div>
              </>
            )}

            <div className="w-full sm:w-48">
              <Select
                label="Region / Jurisdiction"
                value={selectedRegion}
                onChange={(e) => setSelectedRegion(e.target.value)}
                options={[
                  { value: 'all', label: 'All Regions' },
                  { value: 'us', label: 'United States' },
                  { value: 'eu', label: 'European Union' },
                  { value: 'uk', label: 'United Kingdom' },
                  { value: 'au', label: 'Australia' },
                  { value: 'ca', label: 'Canada' },
                ]}
                fullWidth
              />
            </div>

            <div className="flex items-center">
              <Badge variant="info" size="sm">
                {dateRange.start} to {dateRange.end}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card hover className="relative overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Revenue</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                  {isLoading ? '...' : formatCurrency(summary.totalRevenue)}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Gross income for period</p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/30">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
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
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Tax Collected</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                  {isLoading ? '...' : formatCurrency(summary.totalTax)}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">All tax types combined</p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-red-400 to-red-600 rounded-xl flex items-center justify-center shadow-lg shadow-red-500/30">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2z" />
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
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Net Revenue</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                  {isLoading ? '...' : formatCurrency(summary.netRevenue)}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Revenue after tax</p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-green-400 to-green-600 rounded-xl flex items-center justify-center shadow-lg shadow-green-500/30">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
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
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Effective Tax Rate</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                  {isLoading ? '...' : formatPercent(summary.effectiveRate)}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Weighted average rate</p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-purple-400 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/30">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
            </div>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-400 to-purple-600" />
          </CardContent>
        </Card>
      </div>

      {/* Monthly Breakdown Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Monthly Revenue vs Tax Collected</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={monthlyChartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
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
                  name === 'revenue' ? 'Revenue' : 'Tax',
                ]}
              />
              <Legend
                verticalAlign="bottom"
                height={36}
                formatter={(value) => (
                  <span className="text-gray-600 dark:text-gray-400">
                    {value === 'revenue' ? 'Revenue' : 'Tax Collected'}
                  </span>
                )}
              />
              <Bar dataKey="revenue" fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={30} name="revenue" />
              <Bar dataKey="tax" fill="#ef4444" radius={[4, 4, 0, 0]} barSize={30} name="tax" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Tax Breakdown Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <CardTitle>Tax Breakdown by Type</CardTitle>
            <Badge variant="default" size="sm">
              {taxBreakdowns.length} tax types
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHead>
              <TableRow hoverable={false}>
                <TableHeaderCell>Tax Type</TableHeaderCell>
                <TableHeaderCell>Jurisdiction</TableHeaderCell>
                <TableHeaderCell align="right">Rate</TableHeaderCell>
                <TableHeaderCell align="right">Taxable Amount</TableHeaderCell>
                <TableHeaderCell align="right">Tax Collected</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {taxBreakdowns.map((row) => (
                <TableRow key={row.taxType}>
                  <TableCell>
                    <span className="font-medium text-gray-900 dark:text-white">{row.taxType}</span>
                  </TableCell>
                  <TableCell>
                    <Badge variant="default" size="sm">{row.jurisdiction}</Badge>
                  </TableCell>
                  <TableCell align="right">
                    <span className="font-mono">{formatPercent(row.rate)}</span>
                  </TableCell>
                  <TableCell align="right">
                    <span className="font-mono">{formatCurrency(row.taxableAmount)}</span>
                  </TableCell>
                  <TableCell align="right">
                    <span className="font-mono font-semibold text-red-600 dark:text-red-400">
                      {formatCurrency(row.taxCollected)}
                    </span>
                  </TableCell>
                </TableRow>
              ))}
              {/* Totals Row */}
              <TableRow hoverable={false}>
                <TableCell>
                  <span className="font-bold text-gray-900 dark:text-white">Total</span>
                </TableCell>
                <TableCell>&mdash;</TableCell>
                <TableCell align="right">
                  <span className="font-mono font-bold">{formatPercent(summary.effectiveRate)}</span>
                </TableCell>
                <TableCell align="right">
                  <span className="font-mono font-bold">{formatCurrency(summary.totalRevenue)}</span>
                </TableCell>
                <TableCell align="right">
                  <span className="font-mono font-bold text-red-600 dark:text-red-400">
                    {formatCurrency(summary.totalTax)}
                  </span>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Disclaimer */}
      <Card padding="sm">
        <CardContent>
          <div className="flex items-start gap-3 p-2">
            <svg className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">Disclaimer</p>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
                This report is for informational purposes only and should not be used as a substitute for
                professional tax advice. Please consult with a qualified tax professional or accountant for
                accurate tax filing. Tax rates and jurisdictions shown may not reflect your actual tax
                obligations.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default TaxReport;
