/**
 * Calendar View Page
 * Aureon by Rhematek Solutions
 *
 * Monthly calendar showing deadlines, milestones, payment dates,
 * and contract expiry with day-detail panel and upcoming events sidebar.
 */

import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { invoiceService, contractService, paymentService } from '@/services';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Button from '@/components/common/Button';
import Badge from '@/components/common/Badge';

// ============================================
// TYPES
// ============================================

type EventType = 'invoice_due' | 'milestone' | 'payment' | 'contract_expiry';

interface CalendarEvent {
  id: string;
  title: string;
  date: string;
  type: EventType;
  entityId: string;
  entityType: 'invoice' | 'contract' | 'payment';
  amount?: number;
  status?: string;
}

// ============================================
// HELPERS
// ============================================

const EVENT_COLORS: Record<EventType, { bg: string; dot: string; text: string; badge: 'danger' | 'info' | 'success' | 'warning' }> = {
  invoice_due: {
    bg: 'bg-red-50 dark:bg-red-900/20',
    dot: 'bg-red-500',
    text: 'text-red-700 dark:text-red-300',
    badge: 'danger',
  },
  milestone: {
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    dot: 'bg-blue-500',
    text: 'text-blue-700 dark:text-blue-300',
    badge: 'info',
  },
  payment: {
    bg: 'bg-green-50 dark:bg-green-900/20',
    dot: 'bg-green-500',
    text: 'text-green-700 dark:text-green-300',
    badge: 'success',
  },
  contract_expiry: {
    bg: 'bg-amber-50 dark:bg-amber-900/20',
    dot: 'bg-amber-500',
    text: 'text-amber-700 dark:text-amber-300',
    badge: 'warning',
  },
};

const EVENT_LABELS: Record<EventType, string> = {
  invoice_due: 'Invoice Due',
  milestone: 'Milestone',
  payment: 'Payment',
  contract_expiry: 'Contract Expiry',
};

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
};

const getDaysInMonth = (year: number, month: number): number => {
  return new Date(year, month + 1, 0).getDate();
};

const getFirstDayOfMonth = (year: number, month: number): number => {
  return new Date(year, month, 1).getDay();
};

const isSameDay = (d1: string, d2: Date): boolean => {
  const date1 = new Date(d1);
  return (
    date1.getFullYear() === d2.getFullYear() &&
    date1.getMonth() === d2.getMonth() &&
    date1.getDate() === d2.getDate()
  );
};

const isToday = (year: number, month: number, day: number): boolean => {
  const today = new Date();
  return (
    today.getFullYear() === year &&
    today.getMonth() === month &&
    today.getDate() === day
  );
};

// ============================================
// MAIN COMPONENT
// ============================================

const CalendarView: React.FC = () => {
  const navigate = useNavigate();
  const today = new Date();
  const [currentYear, setCurrentYear] = useState(today.getFullYear());
  const [currentMonth, setCurrentMonth] = useState(today.getMonth());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);

  // Fetch data to compose calendar events
  const { data: invoicesData } = useQuery({
    queryKey: ['invoices', 'calendar'],
    queryFn: () => invoiceService.getInvoices({ page: 1, pageSize: 500 }),
  });

  const { data: contractsData } = useQuery({
    queryKey: ['contracts', 'calendar'],
    queryFn: () => contractService.getContracts({ page: 1, pageSize: 500 }),
  });

  const { data: paymentsData } = useQuery({
    queryKey: ['payments', 'calendar'],
    queryFn: () => paymentService.getPayments({ page: 1, pageSize: 500 }),
  });

  // Compose events from fetched data
  const events: CalendarEvent[] = useMemo(() => {
    const result: CalendarEvent[] = [];

    // Invoice due dates
    if (invoicesData?.results) {
      invoicesData.results.forEach((inv: any) => {
        if (inv.due_date) {
          result.push({
            id: `inv-${inv.id}`,
            title: `Invoice #${inv.invoice_number || inv.id} due`,
            date: inv.due_date,
            type: 'invoice_due',
            entityId: inv.id,
            entityType: 'invoice',
            amount: inv.total,
            status: inv.status,
          });
        }
      });
    }

    // Contract expiry dates
    if (contractsData?.results) {
      contractsData.results.forEach((contract: any) => {
        if (contract.end_date) {
          result.push({
            id: `contract-exp-${contract.id}`,
            title: `${contract.title || 'Contract'} expires`,
            date: contract.end_date,
            type: 'contract_expiry',
            entityId: contract.id,
            entityType: 'contract',
            amount: contract.total_value,
            status: contract.status,
          });
        }
        // Contract milestones
        if (contract.milestones) {
          contract.milestones.forEach((ms: any) => {
            if (ms.due_date) {
              result.push({
                id: `ms-${ms.id}`,
                title: `Milestone: ${ms.title || ms.name}`,
                date: ms.due_date,
                type: 'milestone',
                entityId: contract.id,
                entityType: 'contract',
                amount: ms.amount,
                status: ms.status,
              });
            }
          });
        }
      });
    }

    // Payment dates
    if (paymentsData?.results) {
      paymentsData.results.forEach((payment: any) => {
        if (payment.created_at || payment.payment_date) {
          result.push({
            id: `pay-${payment.id}`,
            title: `Payment received`,
            date: payment.payment_date || payment.created_at,
            type: 'payment',
            entityId: payment.id,
            entityType: 'payment',
            amount: payment.amount,
            status: payment.status,
          });
        }
      });
    }

    return result;
  }, [invoicesData, contractsData, paymentsData]);

  // Get events for a specific day
  const getEventsForDay = (year: number, month: number, day: number): CalendarEvent[] => {
    const date = new Date(year, month, day);
    return events.filter((event) => isSameDay(event.date, date));
  };

  // Get events for selected date
  const selectedDateEvents = useMemo(() => {
    if (!selectedDate) return [];
    return events.filter((event) => isSameDay(event.date, selectedDate));
  }, [events, selectedDate]);

  // Get upcoming events (next 14 days)
  const upcomingEvents = useMemo(() => {
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    const twoWeeksLater = new Date(now);
    twoWeeksLater.setDate(twoWeeksLater.getDate() + 14);

    return events
      .filter((event) => {
        const eventDate = new Date(event.date);
        return eventDate >= now && eventDate <= twoWeeksLater;
      })
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
      .slice(0, 10);
  }, [events]);

  // Navigation handlers
  const goToPreviousMonth = () => {
    if (currentMonth === 0) {
      setCurrentMonth(11);
      setCurrentYear((y) => y - 1);
    } else {
      setCurrentMonth((m) => m - 1);
    }
    setSelectedDate(null);
  };

  const goToNextMonth = () => {
    if (currentMonth === 11) {
      setCurrentMonth(0);
      setCurrentYear((y) => y + 1);
    } else {
      setCurrentMonth((m) => m + 1);
    }
    setSelectedDate(null);
  };

  const goToToday = () => {
    setCurrentYear(today.getFullYear());
    setCurrentMonth(today.getMonth());
    setSelectedDate(today);
  };

  // Navigate to entity detail
  const handleEventClick = (event: CalendarEvent) => {
    switch (event.entityType) {
      case 'invoice':
        navigate(`/invoices/${event.entityId}`);
        break;
      case 'contract':
        navigate(`/contracts/${event.entityId}`);
        break;
      case 'payment':
        navigate(`/payments/${event.entityId}`);
        break;
    }
  };

  // Build calendar grid
  const daysInMonth = getDaysInMonth(currentYear, currentMonth);
  const firstDayOfMonth = getFirstDayOfMonth(currentYear, currentMonth);
  const prevMonthDays = getDaysInMonth(
    currentMonth === 0 ? currentYear - 1 : currentYear,
    currentMonth === 0 ? 11 : currentMonth - 1
  );

  const calendarDays: Array<{ day: number; isCurrentMonth: boolean; year: number; month: number }> = [];

  // Previous month trailing days
  for (let i = firstDayOfMonth - 1; i >= 0; i--) {
    const prevMonth = currentMonth === 0 ? 11 : currentMonth - 1;
    const prevYear = currentMonth === 0 ? currentYear - 1 : currentYear;
    calendarDays.push({
      day: prevMonthDays - i,
      isCurrentMonth: false,
      year: prevYear,
      month: prevMonth,
    });
  }

  // Current month days
  for (let day = 1; day <= daysInMonth; day++) {
    calendarDays.push({
      day,
      isCurrentMonth: true,
      year: currentYear,
      month: currentMonth,
    });
  }

  // Next month leading days
  const remainingSlots = 42 - calendarDays.length;
  const nextMonth = currentMonth === 11 ? 0 : currentMonth + 1;
  const nextYear = currentMonth === 11 ? currentYear + 1 : currentYear;
  for (let day = 1; day <= remainingSlots; day++) {
    calendarDays.push({
      day,
      isCurrentMonth: false,
      year: nextYear,
      month: nextMonth,
    });
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">Calendar</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Track deadlines, milestones, and payment dates
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 flex-wrap">
          {(Object.keys(EVENT_COLORS) as EventType[]).map((type) => (
            <div key={type} className="flex items-center gap-1.5">
              <span className={`w-2.5 h-2.5 rounded-full ${EVENT_COLORS[type].dot}`} />
              <span className="text-xs text-gray-600 dark:text-gray-400">{EVENT_LABELS[type]}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Calendar Grid */}
        <div className="lg:col-span-3">
          <Card>
            {/* Month Navigation */}
            <CardHeader>
              <div className="flex items-center justify-between w-full">
                <div className="flex items-center gap-4">
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                    {MONTH_NAMES[currentMonth]} {currentYear}
                  </h2>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={goToToday}>
                    Today
                  </Button>
                  <Button variant="ghost" size="sm" onClick={goToPreviousMonth}>
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                  </Button>
                  <Button variant="ghost" size="sm" onClick={goToNextMonth}>
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </Button>
                </div>
              </div>
            </CardHeader>

            <CardContent>
              {/* Day Headers */}
              <div className="grid grid-cols-7 mb-1">
                {DAY_NAMES.map((day) => (
                  <div
                    key={day}
                    className="py-2 text-center text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase"
                  >
                    {day}
                  </div>
                ))}
              </div>

              {/* Calendar Days */}
              <div className="grid grid-cols-7 border-t border-l border-gray-200 dark:border-gray-700">
                {calendarDays.map((cell, index) => {
                  const dayEvents = cell.isCurrentMonth
                    ? getEventsForDay(cell.year, cell.month, cell.day)
                    : [];
                  const todayHighlight = cell.isCurrentMonth && isToday(cell.year, cell.month, cell.day);
                  const isSelected =
                    selectedDate &&
                    cell.isCurrentMonth &&
                    selectedDate.getFullYear() === cell.year &&
                    selectedDate.getMonth() === cell.month &&
                    selectedDate.getDate() === cell.day;

                  return (
                    <button
                      key={index}
                      onClick={() => {
                        if (cell.isCurrentMonth) {
                          setSelectedDate(new Date(cell.year, cell.month, cell.day));
                        }
                      }}
                      className={`relative min-h-[90px] p-1.5 border-r border-b border-gray-200 dark:border-gray-700 text-left transition-colors ${
                        cell.isCurrentMonth
                          ? 'bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-750'
                          : 'bg-gray-50 dark:bg-gray-900/50'
                      } ${isSelected ? 'ring-2 ring-inset ring-primary-500' : ''}`}
                    >
                      <span
                        className={`inline-flex items-center justify-center w-7 h-7 text-sm rounded-full ${
                          todayHighlight
                            ? 'bg-primary-500 text-white font-bold'
                            : cell.isCurrentMonth
                            ? 'text-gray-900 dark:text-white'
                            : 'text-gray-400 dark:text-gray-600'
                        }`}
                      >
                        {cell.day}
                      </span>

                      {/* Event Indicators */}
                      {dayEvents.length > 0 && (
                        <div className="mt-0.5 space-y-0.5">
                          {dayEvents.slice(0, 3).map((event) => (
                            <div
                              key={event.id}
                              className={`text-xs px-1.5 py-0.5 rounded truncate ${EVENT_COLORS[event.type].bg} ${EVENT_COLORS[event.type].text}`}
                            >
                              <span className={`inline-block w-1.5 h-1.5 rounded-full ${EVENT_COLORS[event.type].dot} mr-1`} />
                              <span className="truncate">{event.title}</span>
                            </div>
                          ))}
                          {dayEvents.length > 3 && (
                            <p className="text-xs text-gray-500 dark:text-gray-400 px-1.5">
                              +{dayEvents.length - 3} more
                            </p>
                          )}
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Selected Day Detail Panel */}
          {selectedDate && (
            <Card className="mt-6">
              <CardHeader>
                <CardTitle>
                  Events for{' '}
                  {selectedDate.toLocaleDateString('en-US', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {selectedDateEvents.length === 0 ? (
                  <div className="text-center py-8">
                    <svg className="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <p className="text-gray-500 dark:text-gray-400">No events scheduled for this day</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {selectedDateEvents.map((event) => (
                      <button
                        key={event.id}
                        onClick={() => handleEventClick(event)}
                        className={`w-full flex items-center justify-between p-4 rounded-lg ${EVENT_COLORS[event.type].bg} hover:opacity-90 transition-opacity group`}
                      >
                        <div className="flex items-center gap-3">
                          <span className={`w-3 h-3 rounded-full ${EVENT_COLORS[event.type].dot} flex-shrink-0`} />
                          <div className="text-left">
                            <p className={`text-sm font-medium ${EVENT_COLORS[event.type].text}`}>
                              {event.title}
                            </p>
                            <div className="flex items-center gap-2 mt-0.5">
                              <Badge variant={EVENT_COLORS[event.type].badge} size="sm">
                                {EVENT_LABELS[event.type]}
                              </Badge>
                              {event.status && (
                                <span className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                                  {event.status}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {event.amount !== undefined && (
                            <span className="text-sm font-semibold text-gray-900 dark:text-white">
                              {formatCurrency(event.amount)}
                            </span>
                          )}
                          <svg className="w-4 h-4 text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Upcoming Events Sidebar */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Upcoming Events</CardTitle>
            </CardHeader>
            <CardContent>
              {upcomingEvents.length === 0 ? (
                <div className="text-center py-6">
                  <svg className="w-10 h-10 mx-auto text-gray-300 dark:text-gray-600 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    No upcoming events in the next 14 days
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {upcomingEvents.map((event) => {
                    const eventDate = new Date(event.date);
                    const daysAway = Math.ceil(
                      (eventDate.getTime() - new Date().setHours(0, 0, 0, 0)) /
                        (1000 * 60 * 60 * 24)
                    );
                    const daysLabel =
                      daysAway === 0
                        ? 'Today'
                        : daysAway === 1
                        ? 'Tomorrow'
                        : `In ${daysAway} days`;

                    return (
                      <button
                        key={event.id}
                        onClick={() => handleEventClick(event)}
                        className="w-full text-left p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors border border-gray-100 dark:border-gray-700"
                      >
                        <div className="flex items-start gap-2">
                          <span className={`w-2 h-2 rounded-full ${EVENT_COLORS[event.type].dot} mt-1.5 flex-shrink-0`} />
                          <div className="min-w-0 flex-1">
                            <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                              {event.title}
                            </p>
                            <div className="flex items-center justify-between mt-1">
                              <span className="text-xs text-gray-500 dark:text-gray-400">
                                {eventDate.toLocaleDateString('en-US', {
                                  month: 'short',
                                  day: 'numeric',
                                })}
                              </span>
                              <span
                                className={`text-xs font-medium ${
                                  daysAway <= 1
                                    ? 'text-red-600 dark:text-red-400'
                                    : daysAway <= 3
                                    ? 'text-amber-600 dark:text-amber-400'
                                    : 'text-gray-500 dark:text-gray-400'
                                }`}
                              >
                                {daysLabel}
                              </span>
                            </div>
                            {event.amount !== undefined && (
                              <p className="text-xs font-semibold text-gray-700 dark:text-gray-300 mt-0.5">
                                {formatCurrency(event.amount)}
                              </p>
                            )}
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Stats */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>This Month</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {(Object.keys(EVENT_COLORS) as EventType[]).map((type) => {
                  const typeEvents = events.filter(
                    (e) =>
                      e.type === type &&
                      new Date(e.date).getMonth() === currentMonth &&
                      new Date(e.date).getFullYear() === currentYear
                  );
                  return (
                    <div key={type} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className={`w-2.5 h-2.5 rounded-full ${EVENT_COLORS[type].dot}`} />
                        <span className="text-sm text-gray-700 dark:text-gray-300">
                          {EVENT_LABELS[type]}
                        </span>
                      </div>
                      <span className="text-sm font-semibold text-gray-900 dark:text-white">
                        {typeEvents.length}
                      </span>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default CalendarView;
