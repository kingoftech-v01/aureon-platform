/**
 * Activity Feed Page
 * Aureon by Rhematek Solutions
 *
 * Real-time activity feed and audit log with timeline UI
 */

import React, { useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { analyticsService } from '@/services';
import { useToast } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Select from '@/components/common/Select';
import Card, { CardContent } from '@/components/common/Card';
import Badge from '@/components/common/Badge';
import LoadingSpinner from '@/components/common/LoadingSpinner';

// Event type configuration: icon colors and display settings
const EVENT_CONFIG: Record<
  string,
  {
    color: string;
    bgColor: string;
    darkBgColor: string;
    icon: React.ReactNode;
    category: string;
  }
> = {
  invoice_created: {
    color: 'text-blue-600 dark:text-blue-400',
    bgColor: 'bg-blue-100',
    darkBgColor: 'dark:bg-blue-900/30',
    category: 'invoice',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
  },
  invoice_sent: {
    color: 'text-indigo-600 dark:text-indigo-400',
    bgColor: 'bg-indigo-100',
    darkBgColor: 'dark:bg-indigo-900/30',
    category: 'invoice',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    ),
  },
  invoice_paid: {
    color: 'text-green-600 dark:text-green-400',
    bgColor: 'bg-green-100',
    darkBgColor: 'dark:bg-green-900/30',
    category: 'invoice',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  payment_received: {
    color: 'text-emerald-600 dark:text-emerald-400',
    bgColor: 'bg-emerald-100',
    darkBgColor: 'dark:bg-emerald-900/30',
    category: 'payment',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  payment_failed: {
    color: 'text-red-600 dark:text-red-400',
    bgColor: 'bg-red-100',
    darkBgColor: 'dark:bg-red-900/30',
    category: 'payment',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  contract_signed: {
    color: 'text-purple-600 dark:text-purple-400',
    bgColor: 'bg-purple-100',
    darkBgColor: 'dark:bg-purple-900/30',
    category: 'contract',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
      </svg>
    ),
  },
  contract_completed: {
    color: 'text-teal-600 dark:text-teal-400',
    bgColor: 'bg-teal-100',
    darkBgColor: 'dark:bg-teal-900/30',
    category: 'contract',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
      </svg>
    ),
  },
  client_created: {
    color: 'text-cyan-600 dark:text-cyan-400',
    bgColor: 'bg-cyan-100',
    darkBgColor: 'dark:bg-cyan-900/30',
    category: 'client',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
      </svg>
    ),
  },
  milestone_completed: {
    color: 'text-amber-600 dark:text-amber-400',
    bgColor: 'bg-amber-100',
    darkBgColor: 'dark:bg-amber-900/30',
    category: 'contract',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9" />
      </svg>
    ),
  },
  user_login: {
    color: 'text-gray-600 dark:text-gray-400',
    bgColor: 'bg-gray-100',
    darkBgColor: 'dark:bg-gray-800',
    category: 'auth',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
      </svg>
    ),
  },
  user_logout: {
    color: 'text-gray-500 dark:text-gray-500',
    bgColor: 'bg-gray-100',
    darkBgColor: 'dark:bg-gray-800',
    category: 'auth',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
      </svg>
    ),
  },
};

// Default config for unknown event types
const DEFAULT_EVENT_CONFIG = {
  color: 'text-gray-600 dark:text-gray-400',
  bgColor: 'bg-gray-100',
  darkBgColor: 'dark:bg-gray-800',
  category: 'other',
  icon: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
};

// Filter category options
const CATEGORY_OPTIONS = [
  { value: '', label: 'All Events' },
  { value: 'invoice', label: 'Invoice' },
  { value: 'payment', label: 'Payment' },
  { value: 'contract', label: 'Contract' },
  { value: 'client', label: 'Client' },
  { value: 'auth', label: 'Auth' },
];

const ITEMS_PER_PAGE = 20;

const ActivityFeed: React.FC = () => {
  const { error: showErrorToast } = useToast();

  // Filter state
  const [categoryFilter, setCategoryFilter] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [userFilter, setUserFilter] = useState('');
  const [expandedItemId, setExpandedItemId] = useState<string | null>(null);
  const [displayCount, setDisplayCount] = useState(ITEMS_PER_PAGE);

  // Build event_types filter based on category
  const getEventTypesForCategory = useCallback((category: string): string[] | undefined => {
    if (!category) return undefined;
    return Object.entries(EVENT_CONFIG)
      .filter(([, config]) => config.category === category)
      .map(([eventType]) => eventType);
  }, []);

  // Fetch activity feed
  const { data: activities, isLoading, error } = useQuery({
    queryKey: ['activity-feed', categoryFilter, dateFrom, dateTo, userFilter],
    queryFn: () =>
      analyticsService.getActivityFeed({
        limit: 100,
        offset: 0,
        event_types: getEventTypesForCategory(categoryFilter),
      }),
  });

  // Handle errors
  React.useEffect(() => {
    if (error) {
      showErrorToast('Failed to load activity feed');
    }
  }, [error, showErrorToast]);

  // Filter activities client-side for date range and user
  const filteredActivities = React.useMemo(() => {
    if (!activities) return [];

    let filtered = [...activities];

    // Filter by date range
    if (dateFrom) {
      const fromDate = new Date(dateFrom);
      filtered = filtered.filter((a) => new Date(a.timestamp) >= fromDate);
    }
    if (dateTo) {
      const toDate = new Date(dateTo);
      toDate.setHours(23, 59, 59, 999);
      filtered = filtered.filter((a) => new Date(a.timestamp) <= toDate);
    }

    // Filter by user name
    if (userFilter.trim()) {
      const search = userFilter.toLowerCase();
      filtered = filtered.filter(
        (a) => a.user?.name?.toLowerCase().includes(search)
      );
    }

    return filtered;
  }, [activities, dateFrom, dateTo, userFilter]);

  // Paginated activities for display
  const displayedActivities = filteredActivities.slice(0, displayCount);
  const hasMore = displayCount < filteredActivities.length;

  // Load more handler
  const handleLoadMore = () => {
    setDisplayCount((prev) => prev + ITEMS_PER_PAGE);
  };

  // Reset filters
  const handleResetFilters = () => {
    setCategoryFilter('');
    setDateFrom('');
    setDateTo('');
    setUserFilter('');
    setDisplayCount(ITEMS_PER_PAGE);
  };

  // Relative time formatter
  const getRelativeTime = (timestamp: string): string => {
    const now = new Date();
    const date = new Date(timestamp);
    const diffMs = now.getTime() - date.getTime();
    const diffSeconds = Math.floor(diffMs / 1000);
    const diffMinutes = Math.floor(diffSeconds / 60);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSeconds < 60) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
    });
  };

  // Get config for event type
  const getConfig = (eventType: string) => {
    return EVENT_CONFIG[eventType] || DEFAULT_EVENT_CONFIG;
  };

  // Format event type as badge label
  const formatEventType = (eventType: string) => {
    return eventType
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase());
  };

  // Get badge variant for event category
  const getCategoryBadgeVariant = (eventType: string): 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default' => {
    const config = getConfig(eventType);
    switch (config.category) {
      case 'invoice': return 'info';
      case 'payment': return 'success';
      case 'contract': return 'primary';
      case 'client': return 'warning';
      case 'auth': return 'default';
      default: return 'default';
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Activity Feed</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Real-time audit log of all system events and user actions
          </p>
        </div>
        {(categoryFilter || dateFrom || dateTo || userFilter) && (
          <Button variant="ghost" onClick={handleResetFilters}>
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Reset Filters
          </Button>
        )}
      </div>

      {/* Filter Bar */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Category Filter */}
            <Select
              value={categoryFilter}
              onChange={(e) => {
                setCategoryFilter(e.target.value);
                setDisplayCount(ITEMS_PER_PAGE);
              }}
              options={CATEGORY_OPTIONS}
              className="w-full md:w-44"
            />

            {/* Date From */}
            <Input
              type="date"
              placeholder="From date"
              value={dateFrom}
              onChange={(e) => {
                setDateFrom(e.target.value);
                setDisplayCount(ITEMS_PER_PAGE);
              }}
              className="w-full md:w-44"
            />

            {/* Date To */}
            <Input
              type="date"
              placeholder="To date"
              value={dateTo}
              onChange={(e) => {
                setDateTo(e.target.value);
                setDisplayCount(ITEMS_PER_PAGE);
              }}
              className="w-full md:w-44"
            />

            {/* User Filter */}
            <div className="flex-1">
              <Input
                type="text"
                placeholder="Filter by user name..."
                value={userFilter}
                onChange={(e) => {
                  setUserFilter(e.target.value);
                  setDisplayCount(ITEMS_PER_PAGE);
                }}
                leftIcon={
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                }
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Activity Timeline */}
      <Card padding="none">
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-16">
              <LoadingSpinner size="lg" text="Loading activity feed..." />
            </div>
          ) : displayedActivities.length > 0 ? (
            <div className="p-6">
              {/* Timeline */}
              <div className="relative">
                {/* Vertical timeline line */}
                <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-gray-200 dark:bg-gray-700" />

                {/* Activity Items */}
                <div className="space-y-6">
                  {displayedActivities.map((activity) => {
                    const config = getConfig(activity.event_type);
                    const isExpanded = expandedItemId === activity.id;

                    return (
                      <div key={activity.id} className="relative flex items-start group">
                        {/* Timeline Dot */}
                        <div
                          className={`relative z-10 flex items-center justify-center w-10 h-10 rounded-full ${config.bgColor} ${config.darkBgColor} ${config.color} ring-4 ring-white dark:ring-gray-800 flex-shrink-0`}
                        >
                          {config.icon}
                        </div>

                        {/* Content */}
                        <div className="ml-4 flex-1 min-w-0">
                          <div className="flex items-start justify-between">
                            <div className="flex-1 min-w-0">
                              {/* Description */}
                              <p className="text-sm text-gray-900 dark:text-white">
                                {activity.description}
                              </p>

                              {/* Meta line: user, event type badge, timestamp */}
                              <div className="flex flex-wrap items-center gap-2 mt-1">
                                {activity.user && (
                                  <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                                    {activity.user.name}
                                  </span>
                                )}
                                <Badge variant={getCategoryBadgeVariant(activity.event_type)} size="sm">
                                  {formatEventType(activity.event_type)}
                                </Badge>
                              </div>
                            </div>

                            {/* Timestamp */}
                            <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap ml-4 flex-shrink-0" title={new Date(activity.timestamp).toLocaleString()}>
                              {getRelativeTime(activity.timestamp)}
                            </span>
                          </div>

                          {/* Expandable Metadata */}
                          {activity.metadata && Object.keys(activity.metadata).length > 0 && (
                            <div className="mt-2">
                              <button
                                onClick={() => setExpandedItemId(isExpanded ? null : activity.id)}
                                className="text-xs text-primary-600 dark:text-primary-400 hover:underline flex items-center"
                              >
                                <svg
                                  className={`w-3 h-3 mr-1 transition-transform duration-200 ${
                                    isExpanded ? 'rotate-90' : ''
                                  }`}
                                  fill="none"
                                  viewBox="0 0 24 24"
                                  stroke="currentColor"
                                >
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                </svg>
                                {isExpanded ? 'Hide details' : 'View details'}
                              </button>

                              {isExpanded && (
                                <div className="mt-2 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-100 dark:border-gray-700">
                                  <div className="space-y-1.5">
                                    {Object.entries(activity.metadata).map(([key, value]) => (
                                      <div key={key} className="flex items-start text-xs">
                                        <span className="font-medium text-gray-500 dark:text-gray-400 min-w-[100px]">
                                          {key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}:
                                        </span>
                                        <span className="text-gray-700 dark:text-gray-300 ml-2 font-mono break-all">
                                          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                        </span>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Load More */}
              {hasMore && (
                <div className="mt-8 text-center">
                  <Button variant="outline" onClick={handleLoadMore}>
                    <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                    Load More ({filteredActivities.length - displayCount} remaining)
                  </Button>
                </div>
              )}
            </div>
          ) : (
            <div className="p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No activity found
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                {categoryFilter || dateFrom || dateTo || userFilter
                  ? 'Try adjusting your filters to see more results'
                  : 'System events and user actions will appear here'}
              </p>
              {(categoryFilter || dateFrom || dateTo || userFilter) && (
                <Button variant="ghost" onClick={handleResetFilters} className="mt-4">
                  Reset Filters
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Summary Footer */}
      {filteredActivities.length > 0 && (
        <div className="text-center text-sm text-gray-500 dark:text-gray-400">
          Showing {displayedActivities.length} of {filteredActivities.length} events
        </div>
      )}
    </div>
  );
};

export default ActivityFeed;
