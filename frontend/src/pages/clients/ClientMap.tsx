/**
 * Client Geography View Page
 * Aureon by Rhematek Solutions
 *
 * Displays clients grouped by country/region with stats,
 * sortable table, search, and expandable rows
 */

import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import apiClient from '@/services/api';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Input from '@/components/common/Input';
import Button from '@/components/common/Button';
import Badge from '@/components/common/Badge';
import { SkeletonTable } from '@/components/common/Skeleton';

interface ClientGeo {
  id: string;
  name: string;
  email: string;
  country: string;
  country_code: string;
  revenue: number;
}

interface CountryGroup {
  country: string;
  country_code: string;
  flag: string;
  clients: ClientGeo[];
  client_count: number;
  total_revenue: number;
}

// Map common country codes to flag emojis
const countryToFlag = (code: string): string => {
  if (!code || code.length !== 2) return '';
  const codePoints = code
    .toUpperCase()
    .split('')
    .map((char) => 0x1f1e6 - 65 + char.charCodeAt(0));
  return String.fromCodePoint(...codePoints);
};

const ClientMap: React.FC = () => {
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState<'count' | 'revenue'>('count');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [expandedCountry, setExpandedCountry] = useState<string | null>(null);

  // Fetch clients grouped by country
  const { data, isLoading } = useQuery({
    queryKey: ['clients-geo'],
    queryFn: async () => {
      const response = await apiClient.get('/clients/?page_size=1000');
      return response.data;
    },
  });

  // Group clients by country
  const countryGroups: CountryGroup[] = useMemo(() => {
    const clients: ClientGeo[] = (data?.results || []).map((c: any) => ({
      id: c.id,
      name:
        c.type === 'individual'
          ? `${c.first_name || ''} ${c.last_name || ''}`.trim()
          : c.company_name || 'Unknown',
      email: c.email || '',
      country: c.country || 'Unknown',
      country_code: c.country_code || '',
      revenue: c.total_revenue || 0,
    }));

    const grouped: Record<string, ClientGeo[]> = {};
    for (const client of clients) {
      const key = client.country || 'Unknown';
      if (!grouped[key]) grouped[key] = [];
      grouped[key].push(client);
    }

    return Object.entries(grouped).map(([country, groupClients]) => ({
      country,
      country_code: groupClients[0]?.country_code || '',
      flag: countryToFlag(groupClients[0]?.country_code || ''),
      clients: groupClients,
      client_count: groupClients.length,
      total_revenue: groupClients.reduce((sum, c) => sum + c.revenue, 0),
    }));
  }, [data]);

  // Stats
  const totalClients = countryGroups.reduce((sum, g) => sum + g.client_count, 0);
  const totalCountries = countryGroups.length;
  const topRegion = useMemo(() => {
    if (countryGroups.length === 0) return 'N/A';
    const sorted = [...countryGroups].sort((a, b) => b.client_count - a.client_count);
    return sorted[0].country;
  }, [countryGroups]);

  // Filter and sort
  const filteredGroups = useMemo(() => {
    let groups = countryGroups;

    if (search.trim()) {
      const q = search.toLowerCase();
      groups = groups.filter(
        (g) =>
          g.country.toLowerCase().includes(q) ||
          g.country_code.toLowerCase().includes(q)
      );
    }

    groups = [...groups].sort((a, b) => {
      const valA = sortBy === 'count' ? a.client_count : a.total_revenue;
      const valB = sortBy === 'count' ? b.client_count : b.total_revenue;
      return sortDir === 'desc' ? valB - valA : valA - valB;
    });

    return groups;
  }, [countryGroups, search, sortBy, sortDir]);

  const maxRevenue = useMemo(() => {
    return Math.max(...filteredGroups.map((g) => g.total_revenue), 1);
  }, [filteredGroups]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const handleSort = (field: 'count' | 'revenue') => {
    if (sortBy === field) {
      setSortDir((prev) => (prev === 'desc' ? 'asc' : 'desc'));
    } else {
      setSortBy(field);
      setSortDir('desc');
    }
  };

  const toggleExpand = (country: string) => {
    setExpandedCountry((prev) => (prev === country ? null : country));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">
            Client Geography
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            View your clients grouped by country and region
          </p>
        </div>
        <Link to="/clients">
          <Button variant="outline">
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Clients
          </Button>
        </Link>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card hover className="relative overflow-hidden">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Clients</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">{totalClients}</p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/30">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
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
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Countries</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">{totalCountries}</p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-green-400 to-green-600 rounded-xl flex items-center justify-center shadow-lg shadow-green-500/30">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
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
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Top Region</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2 truncate max-w-[180px]">
                  {topRegion}
                </p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-purple-400 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/30">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                </svg>
              </div>
            </div>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-400 to-purple-600" />
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4 items-center">
            <div className="flex-1">
              <Input
                type="search"
                placeholder="Search countries..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                leftIcon={
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                }
              />
            </div>
            <div className="flex items-center space-x-2 text-sm">
              <span className="text-gray-500 dark:text-gray-400">Sort by:</span>
              <button
                onClick={() => handleSort('count')}
                className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
                  sortBy === 'count'
                    ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400'
                    : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                Client Count {sortBy === 'count' && (sortDir === 'desc' ? '\u2193' : '\u2191')}
              </button>
              <button
                onClick={() => handleSort('revenue')}
                className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
                  sortBy === 'revenue'
                    ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400'
                    : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                Revenue {sortBy === 'revenue' && (sortDir === 'desc' ? '\u2193' : '\u2191')}
              </button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Country table */}
      <Card>
        <CardHeader>
          <CardTitle>
            {filteredGroups.length} {filteredGroups.length === 1 ? 'Country' : 'Countries'}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6">
              <SkeletonTable rows={5} columns={5} />
            </div>
          ) : filteredGroups.length === 0 ? (
            <div className="p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No countries found
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                {search ? 'Try adjusting your search' : 'No client geography data available'}
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-800">
              {/* Table header */}
              <div className="grid grid-cols-12 gap-4 px-6 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider bg-gray-50 dark:bg-gray-800/50">
                <div className="col-span-4">Country</div>
                <div className="col-span-2 text-right">Clients</div>
                <div className="col-span-3 text-right">Revenue</div>
                <div className="col-span-3">Distribution</div>
              </div>

              {filteredGroups.map((group) => (
                <div key={group.country}>
                  {/* Country row */}
                  <button
                    onClick={() => toggleExpand(group.country)}
                    className="w-full grid grid-cols-12 gap-4 px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors items-center text-left"
                  >
                    <div className="col-span-4 flex items-center space-x-3">
                      <svg
                        className={`w-4 h-4 text-gray-400 transition-transform ${
                          expandedCountry === group.country ? 'rotate-90' : ''
                        }`}
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                      <span className="text-xl">{group.flag || '\uD83C\uDFF3\uFE0F'}</span>
                      <span className="font-medium text-gray-900 dark:text-white">{group.country}</span>
                      {group.country_code && (
                        <Badge variant="default" size="sm">{group.country_code}</Badge>
                      )}
                    </div>
                    <div className="col-span-2 text-right">
                      <span className="font-semibold text-gray-900 dark:text-white">
                        {group.client_count}
                      </span>
                    </div>
                    <div className="col-span-3 text-right">
                      <span className="font-semibold text-gray-900 dark:text-white">
                        {formatCurrency(group.total_revenue)}
                      </span>
                    </div>
                    <div className="col-span-3">
                      <div className="flex items-center space-x-2">
                        <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-primary-400 to-primary-600 rounded-full transition-all duration-500"
                            style={{ width: `${(group.total_revenue / maxRevenue) * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500 dark:text-gray-400 w-10 text-right">
                          {totalClients > 0
                            ? `${((group.client_count / totalClients) * 100).toFixed(0)}%`
                            : '0%'}
                        </span>
                      </div>
                    </div>
                  </button>

                  {/* Expanded client rows */}
                  {expandedCountry === group.country && (
                    <div className="bg-gray-50/50 dark:bg-gray-800/30 border-t border-gray-100 dark:border-gray-800">
                      {group.clients.map((client) => (
                        <Link
                          key={client.id}
                          to={`/clients/${client.id}`}
                          className="grid grid-cols-12 gap-4 px-6 py-3 pl-16 hover:bg-gray-100/50 dark:hover:bg-gray-700/30 transition-colors items-center"
                        >
                          <div className="col-span-4 flex items-center space-x-3">
                            <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full flex items-center justify-center">
                              <span className="text-xs font-medium text-gray-600 dark:text-gray-300">
                                {client.name.charAt(0).toUpperCase()}
                              </span>
                            </div>
                            <div>
                              <p className="text-sm font-medium text-gray-900 dark:text-white">
                                {client.name}
                              </p>
                              <p className="text-xs text-gray-500 dark:text-gray-400">
                                {client.email}
                              </p>
                            </div>
                          </div>
                          <div className="col-span-2" />
                          <div className="col-span-3 text-right">
                            <span className="text-sm text-gray-700 dark:text-gray-300">
                              {formatCurrency(client.revenue)}
                            </span>
                          </div>
                          <div className="col-span-3">
                            <Badge variant="primary" size="sm">View</Badge>
                          </div>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ClientMap;
