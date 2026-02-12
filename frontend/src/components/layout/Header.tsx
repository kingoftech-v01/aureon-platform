/**
 * Header Component
 * Aureon by Rhematek Solutions
 *
 * Top navigation bar with search, notifications, and user menu
 */

import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts';
import { ThemeToggle } from '@/contexts/ThemeContext';
import Avatar from '@/components/common/Avatar';
import Badge from '@/components/common/Badge';
import { notificationService } from '../../services/notificationService';
import { useQuery, useQueryClient } from '@tanstack/react-query';

interface HeaderProps {
  onMenuClick: () => void;
}

const Header: React.FC<HeaderProps> = ({ onMenuClick }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const notificationRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLDivElement>(null);

  const { data: notificationsData } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => notificationService.getNotifications({ page: 1, page_size: 10 }),
    staleTime: 30 * 1000,
  });

  const notifications = notificationsData?.results || [];

  const unreadCount = notifications.filter((n: any) => !n.is_read).length;

  // Quick actions for command palette
  const quickActions = [
    { name: 'Create Invoice', path: '/invoices/create', icon: 'invoice' },
    { name: 'Add Client', path: '/clients/create', icon: 'client' },
    { name: 'New Contract', path: '/contracts/create', icon: 'contract' },
    { name: 'View Analytics', path: '/analytics', icon: 'analytics' },
  ];

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        notificationRef.current &&
        !notificationRef.current.contains(event.target as Node)
      ) {
        setShowNotifications(false);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowSearch(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Keyboard shortcut for search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setShowSearch(true);
      }
      if (e.key === 'Escape') {
        setShowSearch(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleLogout = async () => {
    await logout();
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      setShowSearch(false);
      window.location.href = `/search?q=${encodeURIComponent(searchQuery.trim())}`;
    }
  };

  return (
    <header className="sticky top-0 z-30 bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl border-b border-gray-200/80 dark:border-gray-800/80">
      <div className="flex items-center justify-between h-16 px-4 lg:px-6">
        {/* Left side: Menu button and Search */}
        <div className="flex items-center flex-1">
          {/* Mobile menu button */}
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            aria-label="Open menu"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
              />
            </svg>
          </button>

          {/* Search bar */}
          <div className="hidden md:flex items-center ml-4 flex-1 max-w-lg" ref={searchRef}>
            <button
              onClick={() => setShowSearch(true)}
              className="w-full flex items-center px-4 py-2.5 text-sm text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-xl transition-colors"
            >
              <svg className="w-5 h-5 mr-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
              <span>Search anything...</span>
              <kbd className="ml-auto hidden lg:inline-flex items-center px-2 py-0.5 text-xs font-medium text-gray-400 bg-gray-200 dark:bg-gray-700 rounded">
                Ctrl K
              </kbd>
            </button>

            {/* Search Modal */}
            {showSearch && (
              <div className="fixed inset-0 z-50 overflow-y-auto">
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setShowSearch(false)} />
                <div className="relative min-h-full flex items-start justify-center p-4 pt-[15vh]">
                  <div className="relative w-full max-w-xl bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
                    <form onSubmit={handleSearch}>
                      <div className="flex items-center px-4 border-b border-gray-200 dark:border-gray-700">
                        <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                        <input
                          type="text"
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          placeholder="Search clients, invoices, contracts..."
                          className="flex-1 px-4 py-4 text-sm bg-transparent text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none"
                          autoFocus
                        />
                        <kbd className="text-xs text-gray-400 bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">ESC</kbd>
                      </div>
                    </form>
                    <div className="p-3">
                      <p className="px-3 py-2 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Quick Actions</p>
                      {quickActions.map((action) => (
                        <button
                          key={action.path}
                          onClick={() => {
                            navigate(action.path);
                            setShowSearch(false);
                          }}
                          className="w-full flex items-center px-3 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                        >
                          <span className="w-8 h-8 flex items-center justify-center bg-gray-100 dark:bg-gray-800 rounded-lg mr-3">
                            {action.icon === 'invoice' && (
                              <svg className="w-4 h-4 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2z" />
                              </svg>
                            )}
                            {action.icon === 'client' && (
                              <svg className="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                              </svg>
                            )}
                            {action.icon === 'contract' && (
                              <svg className="w-4 h-4 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                              </svg>
                            )}
                            {action.icon === 'analytics' && (
                              <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                              </svg>
                            )}
                          </span>
                          {action.name}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right side: Theme toggle, Notifications, User menu */}
        <div className="flex items-center space-x-1">
          {/* Mobile Search Button */}
          <button
            onClick={() => setShowSearch(true)}
            className="md:hidden p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            aria-label="Search"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </button>

          {/* Theme toggle */}
          <ThemeToggle />

          {/* Notifications */}
          <div className="relative" ref={notificationRef}>
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              aria-label="Notifications"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0"
                />
              </svg>
              {unreadCount > 0 && (
                <span className="absolute top-1.5 right-1.5 w-4 h-4 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center ring-2 ring-white dark:ring-gray-900">
                  {unreadCount}
                </span>
              )}
            </button>

            {/* Notifications dropdown */}
            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-900 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
                <div className="flex items-center justify-between px-4 py-3 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700">
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                    Notifications
                  </h3>
                  <button className="text-xs text-primary-600 dark:text-primary-400 hover:underline font-medium" onClick={() => {
                    notificationService.markAllAsRead().then(() => {
                      queryClient.invalidateQueries({ queryKey: ['notifications'] });
                    });
                  }}>
                    Mark all read
                  </button>
                </div>

                <div className="max-h-96 overflow-y-auto divide-y divide-gray-100 dark:divide-gray-800">
                  {notifications.map((notification: any) => (
                    <div
                      key={notification.id}
                      className={`px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 cursor-pointer transition-colors ${
                        !notification.is_read ? 'bg-primary-50/50 dark:bg-primary-900/10' : ''
                      }`}
                      onClick={() => {
                        if (notification.link) {
                          navigate(notification.link);
                          setShowNotifications(false);
                        }
                      }}
                    >
                      <div className="flex items-start space-x-3">
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                          notification.type === 'success' || notification.type === 'invoice_paid' || notification.type === 'payment_received' ? 'bg-green-100 dark:bg-green-900/30' :
                          notification.type === 'warning' || notification.type === 'payment_failed' ? 'bg-amber-100 dark:bg-amber-900/30' :
                          'bg-blue-100 dark:bg-blue-900/30'
                        }`}>
                          <svg className={`w-5 h-5 ${
                            notification.type === 'success' || notification.type === 'invoice_paid' || notification.type === 'payment_received' ? 'text-green-500' :
                            notification.type === 'warning' || notification.type === 'payment_failed' ? 'text-amber-500' :
                            'text-blue-500'
                          }`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-white">
                            {notification.title}
                          </p>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5 line-clamp-1">
                            {notification.message}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                            {new Date(notification.created_at).toRelativeString?.() || new Date(notification.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        {!notification.is_read && (
                          <div className="w-2 h-2 bg-primary-500 rounded-full flex-shrink-0 mt-2" />
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                <div className="px-4 py-3 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-200 dark:border-gray-700">
                  <Link
                    to="/notifications"
                    className="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium flex items-center justify-center"
                    onClick={() => setShowNotifications(false)}
                  >
                    View all notifications
                    <svg className="w-4 h-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* User menu */}
          <div className="relative ml-2" ref={userMenuRef}>
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center space-x-2 p-1.5 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              aria-label="User menu"
            >
              <div className="w-8 h-8 bg-gradient-to-br from-primary-400 to-primary-600 rounded-xl flex items-center justify-center text-white text-sm font-semibold shadow-lg shadow-primary-500/20">
                {user?.first_name?.[0]}{user?.last_name?.[0]}
              </div>
              <span className="hidden lg:block text-sm font-medium text-gray-700 dark:text-gray-300">
                {user?.first_name}
              </span>
              <svg
                className="hidden lg:block w-4 h-4 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>

            {/* User dropdown */}
            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-gray-900 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
                <div className="p-4 border-b border-gray-100 dark:border-gray-800">
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 bg-gradient-to-br from-primary-400 via-primary-500 to-accent-500 rounded-xl flex items-center justify-center text-white font-semibold shadow-lg shadow-primary-500/20">
                      {user?.first_name?.[0]}{user?.last_name?.[0]}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-900 dark:text-white">
                        {user?.first_name} {user?.last_name}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                        {user?.email}
                      </p>
                      <Badge variant="primary" size="sm" className="mt-1.5">
                        {user?.role}
                      </Badge>
                    </div>
                  </div>
                </div>

                <div className="py-2">
                  <Link
                    to="/settings/profile"
                    className="flex items-center px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                    onClick={() => setShowUserMenu(false)}
                  >
                    <span className="w-8 h-8 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center mr-3">
                      <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    </span>
                    Your Profile
                  </Link>

                  <Link
                    to="/settings/billing"
                    className="flex items-center px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                    onClick={() => setShowUserMenu(false)}
                  >
                    <span className="w-8 h-8 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center mr-3">
                      <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                      </svg>
                    </span>
                    Billing & Plans
                  </Link>

                  <Link
                    to="/settings"
                    className="flex items-center px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                    onClick={() => setShowUserMenu(false)}
                  >
                    <span className="w-8 h-8 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center mr-3">
                      <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                    </span>
                    Settings
                  </Link>
                </div>

                <div className="border-t border-gray-100 dark:border-gray-800 p-2">
                  <button
                    onClick={handleLogout}
                    className="flex items-center w-full px-4 py-2.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl transition-colors"
                  >
                    <span className="w-8 h-8 bg-red-100 dark:bg-red-900/30 rounded-lg flex items-center justify-center mr-3">
                      <svg className="w-4 h-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                      </svg>
                    </span>
                    Sign out
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
