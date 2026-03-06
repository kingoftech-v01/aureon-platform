/**
 * Command Palette Component
 * Aureon by Rhematek Solutions
 *
 * Enhanced command palette (Cmd+K / Ctrl+K) with fuzzy search,
 * keyboard navigation, and categorized actions
 */

import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { createPortal } from 'react-dom';
import { useAuth } from '@/contexts/AuthContext';

interface CommandItem {
  id: string;
  label: string;
  section: 'quick-actions' | 'navigation' | 'commands' | 'recent';
  icon: React.ReactNode;
  shortcut?: string;
  action: () => void;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

const sectionLabels: Record<string, string> = {
  'quick-actions': 'Quick Actions',
  recent: 'Recent',
  navigation: 'Navigation',
  commands: 'Commands',
};

const sectionOrder = ['quick-actions', 'recent', 'navigation', 'commands'];

/**
 * Simple fuzzy match: checks if all query characters appear in the target in order
 */
const fuzzyMatch = (query: string, target: string): boolean => {
  const lowerQuery = query.toLowerCase();
  const lowerTarget = target.toLowerCase();
  let qi = 0;
  for (let ti = 0; ti < lowerTarget.length && qi < lowerQuery.length; ti++) {
    if (lowerTarget[ti] === lowerQuery[qi]) {
      qi++;
    }
  }
  return qi === lowerQuery.length;
};

export const CommandPalette: React.FC<CommandPaletteProps> = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const toggleDarkMode = useCallback(() => {
    document.documentElement.classList.toggle('dark');
    const isDark = document.documentElement.classList.contains('dark');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
  }, []);

  const allItems: CommandItem[] = useMemo(
    () => [
      // Quick Actions
      {
        id: 'create-invoice',
        label: 'Create Invoice',
        section: 'quick-actions',
        shortcut: 'N I',
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
        ),
        action: () => navigate('/invoices/create'),
      },
      {
        id: 'create-client',
        label: 'Create Client',
        section: 'quick-actions',
        shortcut: 'N C',
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
          </svg>
        ),
        action: () => navigate('/clients/create'),
      },
      {
        id: 'create-contract',
        label: 'Create Contract',
        section: 'quick-actions',
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        ),
        action: () => navigate('/contracts/create'),
      },
      {
        id: 'create-proposal',
        label: 'Create Proposal',
        section: 'quick-actions',
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
        ),
        action: () => navigate('/proposals/create'),
      },

      // Navigation
      {
        id: 'nav-dashboard',
        label: 'Dashboard',
        section: 'navigation',
        shortcut: 'G D',
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
        ),
        action: () => navigate('/dashboard'),
      },
      {
        id: 'nav-clients',
        label: 'Clients',
        section: 'navigation',
        shortcut: 'G C',
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        ),
        action: () => navigate('/clients'),
      },
      {
        id: 'nav-contracts',
        label: 'Contracts',
        section: 'navigation',
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        ),
        action: () => navigate('/contracts'),
      },
      {
        id: 'nav-invoices',
        label: 'Invoices',
        section: 'navigation',
        shortcut: 'G I',
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2z" />
          </svg>
        ),
        action: () => navigate('/invoices'),
      },
      {
        id: 'nav-payments',
        label: 'Payments',
        section: 'navigation',
        shortcut: 'G P',
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
          </svg>
        ),
        action: () => navigate('/payments'),
      },
      {
        id: 'nav-analytics',
        label: 'Analytics',
        section: 'navigation',
        shortcut: 'G A',
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        ),
        action: () => navigate('/analytics'),
      },
      {
        id: 'nav-settings',
        label: 'Settings',
        section: 'navigation',
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        ),
        action: () => navigate('/settings'),
      },

      // Commands
      {
        id: 'cmd-dark-mode',
        label: 'Toggle Dark Mode',
        section: 'commands',
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
          </svg>
        ),
        action: () => toggleDarkMode(),
      },
      {
        id: 'cmd-export',
        label: 'Export Data',
        section: 'commands',
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        ),
        action: () => navigate('/analytics'),
      },
      {
        id: 'cmd-clear-cache',
        label: 'Clear Cache',
        section: 'commands',
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        ),
        action: () => {
          localStorage.clear();
          window.location.reload();
        },
      },
      {
        id: 'cmd-logout',
        label: 'Logout',
        section: 'commands',
        icon: (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
        ),
        action: () => logout(),
      },
    ],
    [navigate, logout, toggleDarkMode]
  );

  // Filter items by fuzzy search
  const filteredItems = useMemo(() => {
    if (!query.trim()) return allItems;
    return allItems.filter((item) => fuzzyMatch(query, item.label));
  }, [query, allItems]);

  // Group filtered items by section
  const groupedItems = useMemo(() => {
    const groups: Record<string, CommandItem[]> = {};
    for (const item of filteredItems) {
      if (!groups[item.section]) groups[item.section] = [];
      groups[item.section].push(item);
    }
    return groups;
  }, [filteredItems]);

  // Flat list for keyboard navigation
  const flatItems = useMemo(() => {
    const result: CommandItem[] = [];
    for (const section of sectionOrder) {
      if (groupedItems[section]) {
        result.push(...groupedItems[section]);
      }
    }
    return result;
  }, [groupedItems]);

  // Reset state on open/close
  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setActiveIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  // Clamp active index when list changes
  useEffect(() => {
    if (activeIndex >= flatItems.length) {
      setActiveIndex(Math.max(0, flatItems.length - 1));
    }
  }, [flatItems.length, activeIndex]);

  // Scroll active item into view
  useEffect(() => {
    if (!listRef.current) return;
    const activeEl = listRef.current.querySelector('[data-active="true"]');
    if (activeEl) {
      activeEl.scrollIntoView({ block: 'nearest' });
    }
  }, [activeIndex]);

  const handleSelect = useCallback(
    (item: CommandItem) => {
      onClose();
      // Small delay so the palette closes first
      setTimeout(() => item.action(), 100);
    },
    [onClose]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setActiveIndex((prev) => (prev + 1) % flatItems.length);
          break;
        case 'ArrowUp':
          e.preventDefault();
          setActiveIndex((prev) => (prev - 1 + flatItems.length) % flatItems.length);
          break;
        case 'Enter':
          e.preventDefault();
          if (flatItems[activeIndex]) {
            handleSelect(flatItems[activeIndex]);
          }
          break;
        case 'Escape':
          e.preventDefault();
          onClose();
          break;
      }
    },
    [flatItems, activeIndex, handleSelect, onClose]
  );

  if (!isOpen) return null;

  const palette = (
    <div className="fixed inset-0 z-[60] flex items-start justify-center pt-[15vh] animate-fade-in">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Palette */}
      <div
        className="relative w-full max-w-xl bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden animate-slide-in"
        role="dialog"
        aria-modal="true"
        aria-label="Command Palette"
        onKeyDown={handleKeyDown}
      >
        {/* Search input */}
        <div className="flex items-center px-4 border-b border-gray-200 dark:border-gray-700">
          <svg className="w-5 h-5 text-gray-400 dark:text-gray-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setActiveIndex(0);
            }}
            placeholder="Type a command or search..."
            className="w-full px-3 py-4 bg-transparent text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none text-sm"
          />
          <kbd className="hidden sm:inline-flex items-center px-2 py-1 text-xs font-medium text-gray-400 dark:text-gray-500 bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded">
            Esc
          </kbd>
        </div>

        {/* Results */}
        <div ref={listRef} className="max-h-80 overflow-y-auto py-2">
          {flatItems.length === 0 ? (
            <div className="px-4 py-8 text-center text-gray-500 dark:text-gray-400 text-sm">
              No results found for &quot;{query}&quot;
            </div>
          ) : (
            sectionOrder.map((section) => {
              const items = groupedItems[section];
              if (!items || items.length === 0) return null;

              return (
                <div key={section}>
                  <div className="px-4 py-1.5">
                    <p className="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
                      {sectionLabels[section]}
                    </p>
                  </div>
                  {items.map((item) => {
                    const globalIdx = flatItems.indexOf(item);
                    const isActive = globalIdx === activeIndex;

                    return (
                      <button
                        key={item.id}
                        data-active={isActive}
                        onClick={() => handleSelect(item)}
                        onMouseEnter={() => setActiveIndex(globalIdx)}
                        className={`w-full flex items-center justify-between px-4 py-2.5 text-left transition-colors ${
                          isActive
                            ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300'
                            : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                        }`}
                      >
                        <div className="flex items-center space-x-3">
                          <span className={isActive ? 'text-primary-500 dark:text-primary-400' : 'text-gray-400 dark:text-gray-500'}>
                            {item.icon}
                          </span>
                          <span className="text-sm font-medium">{item.label}</span>
                        </div>
                        {item.shortcut && (
                          <div className="flex items-center space-x-1">
                            {item.shortcut.split(' ').map((key, idx) => (
                              <kbd
                                key={idx}
                                className="inline-flex items-center justify-center min-w-[22px] px-1.5 py-0.5 text-[10px] font-medium text-gray-400 dark:text-gray-500 bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded"
                              >
                                {key}
                              </kbd>
                            ))}
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2.5 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between text-xs text-gray-400 dark:text-gray-500">
          <div className="flex items-center space-x-3">
            <span className="flex items-center space-x-1">
              <kbd className="px-1 py-0.5 bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-[10px]">&uarr;</kbd>
              <kbd className="px-1 py-0.5 bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-[10px]">&darr;</kbd>
              <span>Navigate</span>
            </span>
            <span className="flex items-center space-x-1">
              <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-[10px]">&crarr;</kbd>
              <span>Select</span>
            </span>
          </div>
          <span>Aureon Command Palette</span>
        </div>
      </div>
    </div>
  );

  return createPortal(palette, document.body);
};

export default CommandPalette;
