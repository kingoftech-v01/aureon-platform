/**
 * Client Activity Timeline Page
 * Aureon by Rhematek Solutions
 *
 * Displays a vertical timeline of all client interactions and events,
 * with filtering by event type and load-more pagination.
 */

import React, { useState, useMemo, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useInfiniteQuery } from '@tanstack/react-query';
import { clientService } from '@/services/clientService';
import apiClient from '@/services/api';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Button from '@/components/common/Button';
import Badge from '@/components/common/Badge';
import { LoadingSpinner } from '@/components/common';

// ============================================
// TYPES
// ============================================

type EventType =
  | 'contract_created'
  | 'invoice_sent'
  | 'payment_received'
  | 'note_added'
  | 'email_sent'
  | 'meeting_scheduled';

interface TimelineEvent {
  id: string;
  event_type: EventType;
  title: string;
  description: string;
  timestamp: string;
  link?: string;
  metadata?: Record<string, any>;
}

interface TimelineResponse {
  results: TimelineEvent[];
  next: string | null;
  count: number;
}

// ============================================
// CONSTANTS
// ============================================

const EVENT_FILTERS: { key: EventType | 'all'; label: string }[] = [
  { key: 'all', label: 'All Events' },
  { key: 'contract_created', label: 'Contracts' },
  { key: 'invoice_sent', label: 'Invoices' },
  { key: 'payment_received', label: 'Payments' },
  { key: 'note_added', label: 'Notes' },
  { key: 'email_sent', label: 'Emails' },
  { key: 'meeting_scheduled', label: 'Meetings' },
];

// ============================================
// HELPERS
// ============================================

function getEventStyle(type: EventType): {
  bgColor: string;
  borderColor: string;
  iconColor: string;
  icon: React.ReactNode;
} {
  switch (type) {
    case 'contract_created':
      return {
        bgColor: 'bg-purple-100 dark:bg-purple-900/30',
        borderColor: 'border-purple-400',
        iconColor: 'text-purple-600 dark:text-purple-400',
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        ),
      };
    case 'invoice_sent':
      return {
        bgColor: 'bg-blue-100 dark:bg-blue-900/30',
        borderColor: 'border-blue-400',
        iconColor: 'text-blue-600 dark:text-blue-400',
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
        ),
      };
    case 'payment_received':
      return {
        bgColor: 'bg-green-100 dark:bg-green-900/30',
        borderColor: 'border-green-400',
        iconColor: 'text-green-600 dark:text-green-400',
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        ),
      };
    case 'note_added':
      return {
        bgColor: 'bg-amber-100 dark:bg-amber-900/30',
        borderColor: 'border-amber-400',
        iconColor: 'text-amber-600 dark:text-amber-400',
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
        ),
      };
    case 'email_sent':
      return {
        bgColor: 'bg-cyan-100 dark:bg-cyan-900/30',
        borderColor: 'border-cyan-400',
        iconColor: 'text-cyan-600 dark:text-cyan-400',
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        ),
      };
    case 'meeting_scheduled':
      return {
        bgColor: 'bg-indigo-100 dark:bg-indigo-900/30',
        borderColor: 'border-indigo-400',
        iconColor: 'text-indigo-600 dark:text-indigo-400',
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        ),
      };
    default:
      return {
        bgColor: 'bg-gray-100 dark:bg-gray-800',
        borderColor: 'border-gray-400',
        iconColor: 'text-gray-600 dark:text-gray-400',
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        ),
      };
  }
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

function formatTime(dateStr: string): string {
  return new Date(dateStr).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

function groupEventsByDate(events: TimelineEvent[]): Record<string, TimelineEvent[]> {
  const groups: Record<string, TimelineEvent[]> = {};
  events.forEach((event) => {
    const dateKey = new Date(event.timestamp).toISOString().split('T')[0];
    if (!groups[dateKey]) {
      groups[dateKey] = [];
    }
    groups[dateKey].push(event);
  });
  return groups;
}

// ============================================
// MAIN COMPONENT
// ============================================

const ClientTimeline: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [activeFilter, setActiveFilter] = useState<EventType | 'all'>('all');

  // Fetch client info
  const { data: client } = useQuery({
    queryKey: ['client', id],
    queryFn: () => clientService.getClient(id!),
    enabled: !!id,
  });

  // Fetch timeline events with pagination
  const {
    data: timelineData,
    isLoading,
    isError,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ['client-timeline', id, activeFilter],
    queryFn: async ({ pageParam = 1 }) => {
      const params = new URLSearchParams();
      params.set('page', pageParam.toString());
      params.set('page_size', '20');
      if (activeFilter !== 'all') {
        params.set('event_type', activeFilter);
      }
      const response = await apiClient.get<TimelineResponse>(
        `/clients/${id}/activity/?${params.toString()}`
      );
      return response.data;
    },
    initialPageParam: 1,
    getNextPageParam: (lastPage, _allPages, lastPageParam) => {
      return lastPage.next ? (lastPageParam as number) + 1 : undefined;
    },
    enabled: !!id,
  });

  // Flatten pages into a single list
  const allEvents = useMemo(() => {
    return timelineData?.pages.flatMap((page) => page.results) || [];
  }, [timelineData]);

  // Group events by date
  const groupedEvents = useMemo(() => groupEventsByDate(allEvents), [allEvents]);
  const sortedDates = useMemo(
    () => Object.keys(groupedEvents).sort((a, b) => b.localeCompare(a)),
    [groupedEvents]
  );

  const clientName = client
    ? client.type === 'individual'
      ? `${client.first_name} ${client.last_name}`
      : client.company_name || 'Client'
    : 'Client';

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <LoadingSpinner />
          <p className="mt-4 text-gray-500 dark:text-gray-400">Loading timeline...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <Link
              to={`/clients/${id}`}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </Link>
            <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">
              Activity Timeline
            </h1>
          </div>
          <p className="text-gray-600 dark:text-gray-400 ml-8">
            All interactions with {clientName}
          </p>
        </div>
        <Badge variant="info" size="md">
          {allEvents.length} event{allEvents.length !== 1 ? 's' : ''}
        </Badge>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap gap-2">
        {EVENT_FILTERS.map((filter) => (
          <button
            key={filter.key}
            onClick={() => setActiveFilter(filter.key)}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200 ${
              activeFilter === filter.key
                ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/25'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {/* Error state */}
      {isError && (
        <Card>
          <CardContent className="p-12 text-center">
            <div className="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Failed to load timeline
            </h3>
            <p className="text-gray-500 dark:text-gray-400">
              Please try refreshing the page.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Empty state */}
      {!isError && allEvents.length === 0 && (
        <Card>
          <CardContent className="p-12 text-center">
            <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              No activity yet
            </h3>
            <p className="text-gray-500 dark:text-gray-400">
              {activeFilter === 'all'
                ? 'There is no recorded activity for this client yet.'
                : `No ${activeFilter.replace('_', ' ')} events found.`}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Timeline */}
      {sortedDates.length > 0 && (
        <div className="relative">
          {/* Vertical line */}
          <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200 dark:bg-gray-700" />

          {sortedDates.map((dateKey) => (
            <div key={dateKey} className="mb-8">
              {/* Date header */}
              <div className="relative flex items-center mb-4">
                <div className="w-12 h-12 bg-gray-900 dark:bg-gray-100 rounded-full flex items-center justify-center z-10">
                  <svg className="w-5 h-5 text-white dark:text-gray-900" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <h3 className="ml-4 text-lg font-semibold text-gray-900 dark:text-white">
                  {formatDate(dateKey)}
                </h3>
              </div>

              {/* Events for this date */}
              <div className="space-y-4 ml-1">
                {groupedEvents[dateKey].map((event) => {
                  const style = getEventStyle(event.event_type);
                  return (
                    <div key={event.id} className="relative flex items-start group">
                      {/* Event icon */}
                      <div
                        className={`w-10 h-10 rounded-full ${style.bgColor} ${style.iconColor} flex items-center justify-center z-10 flex-shrink-0 ml-1 ring-4 ring-white dark:ring-gray-900`}
                      >
                        {style.icon}
                      </div>

                      {/* Event content */}
                      <div className="ml-4 flex-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className="text-sm font-semibold text-gray-900 dark:text-white">
                                {event.title}
                              </h4>
                              <Badge variant="default" size="sm">
                                {event.event_type.replace(/_/g, ' ')}
                              </Badge>
                            </div>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              {event.description}
                            </p>
                          </div>
                          <span className="text-xs text-gray-400 dark:text-gray-500 whitespace-nowrap flex-shrink-0">
                            {formatTime(event.timestamp)}
                          </span>
                        </div>

                        {/* Action link */}
                        {event.link && (
                          <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
                            <Link
                              to={event.link}
                              className="inline-flex items-center text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium transition-colors"
                            >
                              View details
                              <svg className="w-4 h-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                              </svg>
                            </Link>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}

          {/* Load More */}
          {hasNextPage && (
            <div className="flex justify-center pt-4">
              <Button
                variant="outline"
                onClick={() => fetchNextPage()}
                isLoading={isFetchingNextPage}
              >
                {isFetchingNextPage ? 'Loading more...' : 'Load More Events'}
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ClientTimeline;
