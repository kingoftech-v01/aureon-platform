/**
 * Kanban Board Page
 * Aureon by Rhematek Solutions
 *
 * Visual kanban board for managing contracts and proposals
 * with drag indicators, card details, and column status tracking.
 */

import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { contractService } from '@/services/contractService';
import Card, { CardContent } from '@/components/common/Card';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Select from '@/components/common/Select';
import Badge from '@/components/common/Badge';
import Modal, { ModalHeader, ModalBody, ModalFooter } from '@/components/common/Modal';
import { useToast } from '@/components/common';

// ============================================
// TYPES
// ============================================

type EntityMode = 'contracts' | 'proposals';

interface KanbanCard {
  id: string;
  title: string;
  clientName: string;
  amount: number;
  date: string;
  status: string;
  assignee?: string;
  assigneeInitials?: string;
  priority?: 'low' | 'medium' | 'high';
  entityType: EntityMode;
}

interface KanbanColumn {
  id: string;
  title: string;
  status: string;
  color: string;
  dotColor: string;
}

// ============================================
// COLUMN CONFIGURATIONS
// ============================================

const CONTRACT_COLUMNS: KanbanColumn[] = [
  { id: 'draft', title: 'Draft', status: 'draft', color: 'bg-gray-100 dark:bg-gray-800', dotColor: 'bg-gray-400' },
  { id: 'pending_signature', title: 'Pending Signature', status: 'pending_signature', color: 'bg-amber-50 dark:bg-amber-900/10', dotColor: 'bg-amber-500' },
  { id: 'active', title: 'Active', status: 'active', color: 'bg-blue-50 dark:bg-blue-900/10', dotColor: 'bg-blue-500' },
  { id: 'completed', title: 'Completed', status: 'completed', color: 'bg-green-50 dark:bg-green-900/10', dotColor: 'bg-green-500' },
];

const PROPOSAL_COLUMNS: KanbanColumn[] = [
  { id: 'draft', title: 'Draft', status: 'draft', color: 'bg-gray-100 dark:bg-gray-800', dotColor: 'bg-gray-400' },
  { id: 'sent', title: 'Sent', status: 'sent', color: 'bg-blue-50 dark:bg-blue-900/10', dotColor: 'bg-blue-500' },
  { id: 'viewed', title: 'Viewed', status: 'viewed', color: 'bg-purple-50 dark:bg-purple-900/10', dotColor: 'bg-purple-500' },
  { id: 'accepted', title: 'Accepted', status: 'accepted', color: 'bg-green-50 dark:bg-green-900/10', dotColor: 'bg-green-500' },
  { id: 'declined', title: 'Declined', status: 'declined', color: 'bg-red-50 dark:bg-red-900/10', dotColor: 'bg-red-500' },
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

const getInitials = (name: string): string => {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
};

const getPriorityColor = (priority?: string): string => {
  switch (priority) {
    case 'high':
      return 'text-red-600 dark:text-red-400';
    case 'medium':
      return 'text-amber-600 dark:text-amber-400';
    case 'low':
      return 'text-green-600 dark:text-green-400';
    default:
      return 'text-gray-400';
  }
};

const getStatusBadgeVariant = (status: string): 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'info' => {
  switch (status) {
    case 'draft': return 'default';
    case 'pending_signature':
    case 'sent': return 'warning';
    case 'active':
    case 'viewed': return 'info';
    case 'completed':
    case 'accepted': return 'success';
    case 'declined': return 'danger';
    default: return 'default';
  }
};

// ============================================
// KANBAN CARD COMPONENT
// ============================================

const KanbanCardItem: React.FC<{
  card: KanbanCard;
  onClick: () => void;
}> = ({ card, onClick }) => {
  return (
    <button
      onClick={onClick}
      className="w-full text-left bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-3 shadow-sm hover:shadow-md transition-all duration-150 group"
    >
      <div className="flex items-start gap-2">
        {/* Drag handle */}
        <div className="flex-shrink-0 mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity cursor-grab">
          <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
            <circle cx="9" cy="5" r="1.5" />
            <circle cx="15" cy="5" r="1.5" />
            <circle cx="9" cy="12" r="1.5" />
            <circle cx="15" cy="12" r="1.5" />
            <circle cx="9" cy="19" r="1.5" />
            <circle cx="15" cy="19" r="1.5" />
          </svg>
        </div>

        <div className="flex-1 min-w-0">
          {/* Title */}
          <p className="text-sm font-medium text-gray-900 dark:text-white truncate group-hover:text-primary-600 dark:group-hover:text-primary-400">
            {card.title}
          </p>

          {/* Client Name */}
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">
            {card.clientName}
          </p>

          {/* Amount and Date Row */}
          <div className="flex items-center justify-between mt-2">
            <span className="text-sm font-semibold text-gray-900 dark:text-white">
              {formatCurrency(card.amount)}
            </span>
            <span className="text-xs text-gray-400 dark:text-gray-500">
              {new Date(card.date).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
              })}
            </span>
          </div>

          {/* Footer with priority and assignee */}
          <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-100 dark:border-gray-700">
            {/* Priority indicator */}
            {card.priority && (
              <div className="flex items-center gap-1">
                <svg
                  className={`w-3.5 h-3.5 ${getPriorityColor(card.priority)}`}
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M14.4 6L14 4H5v17h2v-7h5.6l.4 2h7V6z" />
                </svg>
                <span className={`text-xs capitalize ${getPriorityColor(card.priority)}`}>
                  {card.priority}
                </span>
              </div>
            )}

            {/* Assignee avatar */}
            {card.assignee && (
              <div
                className="w-6 h-6 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center"
                title={card.assignee}
              >
                <span className="text-xs font-medium text-primary-700 dark:text-primary-300">
                  {card.assigneeInitials || getInitials(card.assignee)}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </button>
  );
};

// ============================================
// MAIN COMPONENT
// ============================================

const KanbanBoard: React.FC = () => {
  const navigate = useNavigate();
  const { success: showSuccessToast } = useToast();

  // State
  const [entityMode, setEntityMode] = useState<EntityMode>('contracts');
  const [clientFilter, setClientFilter] = useState('');
  const [searchFilter, setSearchFilter] = useState('');
  const [selectedCard, setSelectedCard] = useState<KanbanCard | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);

  // Fetch contracts
  const { data: contractsData, isLoading: contractsLoading } = useQuery({
    queryKey: ['kanban-contracts'],
    queryFn: () => contractService.getContracts({ page: 1, pageSize: 200 }),
    enabled: entityMode === 'contracts',
  });

  // Fetch proposals (using contracts API with proposal status filter)
  const { data: proposalsData, isLoading: proposalsLoading } = useQuery({
    queryKey: ['kanban-proposals'],
    queryFn: () => contractService.getContracts({ page: 1, pageSize: 200 }, { type: 'proposal' }),
    enabled: entityMode === 'proposals',
  });

  const isLoading = entityMode === 'contracts' ? contractsLoading : proposalsLoading;
  const columns = entityMode === 'contracts' ? CONTRACT_COLUMNS : PROPOSAL_COLUMNS;

  // Transform data into kanban cards
  const cards: KanbanCard[] = useMemo(() => {
    const rawData = entityMode === 'contracts' ? contractsData?.results : proposalsData?.results;
    if (!rawData) return [];

    return rawData.map((item: any) => ({
      id: item.id,
      title: item.title || `${entityMode === 'contracts' ? 'Contract' : 'Proposal'} #${item.id}`,
      clientName:
        item.client?.type === 'individual'
          ? `${item.client.first_name} ${item.client.last_name}`
          : item.client?.company_name || 'Unknown Client',
      amount: item.total_value || item.amount || 0,
      date: item.created_at || item.start_date || new Date().toISOString(),
      status: item.status || 'draft',
      assignee: item.assigned_to?.name || item.created_by?.name,
      assigneeInitials: item.assigned_to?.name
        ? getInitials(item.assigned_to.name)
        : item.created_by?.name
        ? getInitials(item.created_by.name)
        : undefined,
      priority: item.priority,
      entityType: entityMode,
    }));
  }, [contractsData, proposalsData, entityMode]);

  // Apply filters
  const filteredCards = useMemo(() => {
    return cards.filter((card) => {
      if (clientFilter && !card.clientName.toLowerCase().includes(clientFilter.toLowerCase())) {
        return false;
      }
      if (searchFilter && !card.title.toLowerCase().includes(searchFilter.toLowerCase())) {
        return false;
      }
      return true;
    });
  }, [cards, clientFilter, searchFilter]);

  // Group cards by status
  const getCardsForColumn = (status: string): KanbanCard[] => {
    return filteredCards.filter((card) => card.status === status);
  };

  // Get total value for a column
  const getColumnTotal = (status: string): number => {
    return getCardsForColumn(status).reduce((sum, card) => sum + card.amount, 0);
  };

  // Handle card click
  const handleCardClick = (card: KanbanCard) => {
    setSelectedCard(card);
    setShowDetailModal(true);
  };

  // Navigate to entity detail
  const handleViewDetail = () => {
    if (!selectedCard) return;
    const basePath = selectedCard.entityType === 'contracts' ? '/contracts' : '/proposals';
    navigate(`${basePath}/${selectedCard.id}`);
  };

  // Handle add new
  const handleAddNew = (status: string) => {
    const basePath = entityMode === 'contracts' ? '/contracts/create' : '/proposals/create';
    navigate(`${basePath}?status=${status}`);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">
            Kanban Board
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Visual pipeline for {entityMode === 'contracts' ? 'contract' : 'proposal'} management
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          {/* Entity Type Toggle */}
          <div className="flex items-center bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
            <button
              onClick={() => setEntityMode('contracts')}
              className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
                entityMode === 'contracts'
                  ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              Contracts
            </button>
            <button
              onClick={() => setEntityMode('proposals')}
              className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
                entityMode === 'proposals'
                  ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              Proposals
            </button>
          </div>

          <Button
            onClick={() =>
              navigate(entityMode === 'contracts' ? '/contracts/create' : '/proposals/create')
            }
          >
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            New {entityMode === 'contracts' ? 'Contract' : 'Proposal'}
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <Input
            placeholder={`Search ${entityMode}...`}
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            className="pl-9"
          />
        </div>
        <Input
          placeholder="Filter by client..."
          value={clientFilter}
          onChange={(e) => setClientFilter(e.target.value)}
          className="max-w-xs"
        />
        <span className="text-sm text-gray-500 dark:text-gray-400">
          {filteredCards.length} total items
        </span>
      </div>

      {/* Loading State */}
      {isLoading ? (
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500" />
        </div>
      ) : (
        /* Kanban Columns */
        <div className="flex gap-4 overflow-x-auto pb-4 -mx-4 px-4 sm:mx-0 sm:px-0">
          {columns.map((column) => {
            const columnCards = getCardsForColumn(column.status);
            const columnTotal = getColumnTotal(column.status);

            return (
              <div
                key={column.id}
                className="flex-shrink-0 w-72 sm:w-80"
              >
                {/* Column Header */}
                <div className={`rounded-t-lg px-4 py-3 ${column.color}`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className={`w-2.5 h-2.5 rounded-full ${column.dotColor}`} />
                      <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                        {column.title}
                      </h3>
                      <Badge variant="default" size="sm">
                        {columnCards.length}
                      </Badge>
                    </div>
                    <button
                      onClick={() => handleAddNew(column.status)}
                      className="p-1 rounded-md hover:bg-white/50 dark:hover:bg-gray-700/50 transition-colors"
                      aria-label={`Add new ${entityMode === 'contracts' ? 'contract' : 'proposal'} to ${column.title}`}
                    >
                      <svg className="w-4 h-4 text-gray-500 dark:text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                      </svg>
                    </button>
                  </div>
                  {columnTotal > 0 && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Total: {formatCurrency(columnTotal)}
                    </p>
                  )}
                </div>

                {/* Column Body / Card List */}
                <div className="bg-gray-50 dark:bg-gray-900/50 rounded-b-lg border border-t-0 border-gray-200 dark:border-gray-700 p-2 min-h-[200px] space-y-2">
                  {columnCards.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-8 text-center">
                      <svg className="w-8 h-8 text-gray-300 dark:text-gray-600 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <p className="text-xs text-gray-400 dark:text-gray-500">
                        No {entityMode} in this stage
                      </p>
                    </div>
                  ) : (
                    columnCards.map((card) => (
                      <KanbanCardItem
                        key={card.id}
                        card={card}
                        onClick={() => handleCardClick(card)}
                      />
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Summary Bar */}
      <Card padding="sm">
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-6">
              {columns.map((column) => {
                const count = getCardsForColumn(column.status).length;
                return (
                  <div key={column.id} className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${column.dotColor}`} />
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      {column.title}:{' '}
                      <span className="font-semibold">{count}</span>
                    </span>
                  </div>
                );
              })}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Pipeline Value:{' '}
              <span className="font-bold text-gray-900 dark:text-white">
                {formatCurrency(filteredCards.reduce((sum, c) => sum + c.amount, 0))}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Card Detail Modal */}
      <Modal
        isOpen={showDetailModal}
        onClose={() => {
          setShowDetailModal(false);
          setSelectedCard(null);
        }}
        size="md"
      >
        {selectedCard && (
          <>
            <ModalHeader>
              {selectedCard.entityType === 'contracts' ? 'Contract' : 'Proposal'} Details
            </ModalHeader>
            <ModalBody>
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {selectedCard.title}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                    {selectedCard.clientName}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Status
                    </p>
                    <Badge
                      variant={getStatusBadgeVariant(selectedCard.status)}
                      size="sm"
                      className="mt-1"
                    >
                      {selectedCard.status.replace(/_/g, ' ')}
                    </Badge>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Amount
                    </p>
                    <p className="text-lg font-bold text-gray-900 dark:text-white mt-0.5">
                      {formatCurrency(selectedCard.amount)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Date
                    </p>
                    <p className="text-sm text-gray-900 dark:text-white mt-0.5">
                      {new Date(selectedCard.date).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                      })}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Assigned To
                    </p>
                    <div className="flex items-center gap-2 mt-0.5">
                      {selectedCard.assignee ? (
                        <>
                          <div className="w-6 h-6 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
                            <span className="text-xs font-medium text-primary-700 dark:text-primary-300">
                              {selectedCard.assigneeInitials}
                            </span>
                          </div>
                          <span className="text-sm text-gray-900 dark:text-white">
                            {selectedCard.assignee}
                          </span>
                        </>
                      ) : (
                        <span className="text-sm text-gray-500 dark:text-gray-400">Unassigned</span>
                      )}
                    </div>
                  </div>
                </div>

                {selectedCard.priority && (
                  <div>
                    <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Priority
                    </p>
                    <div className="flex items-center gap-1 mt-1">
                      <svg
                        className={`w-4 h-4 ${getPriorityColor(selectedCard.priority)}`}
                        fill="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path d="M14.4 6L14 4H5v17h2v-7h5.6l.4 2h7V6z" />
                      </svg>
                      <span className={`text-sm font-medium capitalize ${getPriorityColor(selectedCard.priority)}`}>
                        {selectedCard.priority} Priority
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </ModalBody>
            <ModalFooter>
              <Button
                variant="ghost"
                onClick={() => {
                  setShowDetailModal(false);
                  setSelectedCard(null);
                }}
              >
                Close
              </Button>
              <Button onClick={handleViewDetail}>
                <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                View Full Details
              </Button>
            </ModalFooter>
          </>
        )}
      </Modal>
    </div>
  );
};

export default KanbanBoard;
