/**
 * Quick Notes Widget Component
 * Aureon by Rhematek Solutions
 *
 * Floating expandable note panel for entities (client, contract, invoice, payment)
 */

import React, { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/services/api';

interface Note {
  id: string;
  content: string;
  author: string;
  created_at: string;
}

interface QuickNotesProps {
  entityType: 'client' | 'contract' | 'invoice' | 'payment';
  entityId: string;
}

const entityEndpoints: Record<string, string> = {
  client: 'clients',
  contract: 'contracts',
  invoice: 'invoices',
  payment: 'payments',
};

export const QuickNotes: React.FC<QuickNotesProps> = ({ entityType, entityId }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [newNote, setNewNote] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const queryClient = useQueryClient();

  const endpoint = `/${entityEndpoints[entityType]}/${entityId}/notes/`;

  // Fetch notes
  const { data: notes = [], isLoading } = useQuery<Note[]>({
    queryKey: ['notes', entityType, entityId],
    queryFn: async () => {
      const response = await apiClient.get(endpoint);
      return response.data;
    },
  });

  // Add note mutation
  const addNoteMutation = useMutation({
    mutationFn: async (content: string) => {
      const response = await apiClient.post(endpoint, { content });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notes', entityType, entityId] });
      setNewNote('');
    },
  });

  // Delete note mutation
  const deleteNoteMutation = useMutation({
    mutationFn: async (noteId: string) => {
      await apiClient.delete(`${endpoint}${noteId}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notes', entityType, entityId] });
    },
  });

  // Focus textarea when expanded
  useEffect(() => {
    if (isExpanded && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isExpanded]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNote.trim()) return;
    addNoteMutation.mutate(newNote.trim());
  };

  const formatTimestamp = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div className="fixed bottom-6 right-6 z-40">
      {/* Expanded panel */}
      {isExpanded && (
        <div className="mb-3 w-80 bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden animate-slide-in">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-primary-500 to-primary-600 text-white">
            <h3 className="text-sm font-semibold flex items-center space-x-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              <span>Notes ({notes.length})</span>
            </h3>
            <button
              onClick={() => setIsExpanded(false)}
              className="text-white/80 hover:text-white transition-colors"
              aria-label="Close notes"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>

          {/* Notes list */}
          <div className="max-h-60 overflow-y-auto divide-y divide-gray-100 dark:divide-gray-700">
            {isLoading ? (
              <div className="px-4 py-6 text-center text-gray-400 dark:text-gray-500 text-sm">
                Loading notes...
              </div>
            ) : notes.length === 0 ? (
              <div className="px-4 py-6 text-center text-gray-400 dark:text-gray-500 text-sm">
                No notes yet. Add one below.
              </div>
            ) : (
              notes.map((note) => (
                <div
                  key={note.id}
                  className="px-4 py-3 group hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <p className="text-sm text-gray-700 dark:text-gray-300 flex-1 whitespace-pre-wrap break-words">
                      {note.content}
                    </p>
                    <button
                      onClick={() => deleteNoteMutation.mutate(note.id)}
                      className="ml-2 text-gray-300 dark:text-gray-600 hover:text-red-500 dark:hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all shrink-0"
                      aria-label="Delete note"
                      disabled={deleteNoteMutation.isPending}
                    >
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                  <div className="flex items-center justify-between mt-1.5">
                    <span className="text-xs text-gray-400 dark:text-gray-500">
                      {note.author}
                    </span>
                    <span className="text-xs text-gray-400 dark:text-gray-500">
                      {formatTimestamp(note.created_at)}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Add note form */}
          <form onSubmit={handleSubmit} className="p-3 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-end space-x-2">
              <textarea
                ref={textareaRef}
                value={newNote}
                onChange={(e) => setNewNote(e.target.value)}
                placeholder="Write a note..."
                rows={2}
                className="flex-1 resize-none rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
              />
              <button
                type="submit"
                disabled={!newNote.trim() || addNoteMutation.isPending}
                className="shrink-0 p-2 rounded-lg bg-primary-500 text-white hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                aria-label="Send note"
              >
                {addNoteMutation.isPending ? (
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                )}
              </button>
            </div>
            <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-1">
              Ctrl+Enter to send
            </p>
          </form>
        </div>
      )}

      {/* Toggle button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="relative w-12 h-12 rounded-full bg-gradient-to-br from-primary-500 to-primary-600 text-white shadow-lg shadow-primary-500/30 hover:shadow-xl hover:shadow-primary-500/40 hover:scale-105 transition-all flex items-center justify-center"
        aria-label={isExpanded ? 'Close notes' : 'Open notes'}
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>

        {/* Note count badge */}
        {notes.length > 0 && !isExpanded && (
          <span className="absolute -top-1 -right-1 flex items-center justify-center w-5 h-5 text-[10px] font-bold bg-red-500 text-white rounded-full ring-2 ring-white dark:ring-gray-900">
            {notes.length > 9 ? '9+' : notes.length}
          </span>
        )}
      </button>
    </div>
  );
};

export default QuickNotes;
