export const STATUS_COLORS = {
  // Invoice statuses
  draft: 'bg-gray-100 text-gray-800',
  sent: 'bg-blue-100 text-blue-800',
  viewed: 'bg-purple-100 text-purple-800',
  paid: 'bg-green-100 text-green-800',
  partially_paid: 'bg-yellow-100 text-yellow-800',
  overdue: 'bg-red-100 text-red-800',
  cancelled: 'bg-gray-100 text-gray-500',
  // Contract statuses
  active: 'bg-green-100 text-green-800',
  completed: 'bg-blue-100 text-blue-800',
  expired: 'bg-orange-100 text-orange-800',
  terminated: 'bg-red-100 text-red-800',
  // Payment statuses
  pending: 'bg-yellow-100 text-yellow-800',
  processing: 'bg-blue-100 text-blue-800',
  succeeded: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  refunded: 'bg-purple-100 text-purple-800',
} as const;

export const LIFECYCLE_STAGES = {
  lead: { label: 'Lead', color: 'bg-gray-100 text-gray-800' },
  prospect: { label: 'Prospect', color: 'bg-blue-100 text-blue-800' },
  active: { label: 'Active', color: 'bg-green-100 text-green-800' },
  inactive: { label: 'Inactive', color: 'bg-yellow-100 text-yellow-800' },
  churned: { label: 'Churned', color: 'bg-red-100 text-red-800' },
} as const;

export const APP_NAME = 'Aureon';
export const ITEMS_PER_PAGE = 20;
