/**
 * Layout Component
 * Aureon by Rhematek Solutions
 *
 * Main application layout with sidebar, header, and footer
 * Enhanced with accessibility features for Lighthouse 95+ compliance
 */

import React, { useState, useCallback, useEffect, ReactNode } from 'react';
import Sidebar from './Sidebar';
import Header from './Header';
import Footer from './Footer';
import { SkipLink } from '../common';

interface LayoutProps {
  children: ReactNode;
  showFooter?: boolean;
  /** Page title for screen readers - announced on navigation */
  pageTitle?: string;
  /** Custom ARIA label for the main content region */
  mainContentLabel?: string;
}

const Layout: React.FC<LayoutProps> = ({
  children,
  showFooter = true,
  pageTitle,
  mainContentLabel = 'Main content',
}) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const toggleSidebar = useCallback(() => {
    setSidebarOpen((prev) => !prev);
  }, []);

  const closeSidebar = useCallback(() => {
    setSidebarOpen(false);
  }, []);

  // Handle escape key to close sidebar
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && sidebarOpen) {
        closeSidebar();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [sidebarOpen, closeSidebar]);

  // Announce page title changes to screen readers
  useEffect(() => {
    if (pageTitle) {
      // Update document title
      document.title = `${pageTitle} | Aureon`;

      // Create live region announcement for screen readers
      const announcement = document.createElement('div');
      announcement.setAttribute('role', 'status');
      announcement.setAttribute('aria-live', 'polite');
      announcement.setAttribute('aria-atomic', 'true');
      announcement.className = 'sr-only';
      announcement.textContent = `Navigated to ${pageTitle}`;
      document.body.appendChild(announcement);

      // Remove after announcement
      const timeout = setTimeout(() => {
        announcement.remove();
      }, 1000);

      return () => {
        clearTimeout(timeout);
        announcement.remove();
      };
    }
  }, [pageTitle]);

  // Prevent body scroll when sidebar is open on mobile
  useEffect(() => {
    if (sidebarOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [sidebarOpen]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Skip Links for keyboard navigation */}
      <SkipLink targetId="main-content">Skip to main content</SkipLink>
      <SkipLink targetId="navigation" className="ml-2">
        Skip to navigation
      </SkipLink>

      {/* Sidebar Navigation */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={closeSidebar}
        aria-label="Main navigation"
      />

      {/* Backdrop for mobile sidebar */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-900/50 backdrop-blur-sm lg:hidden"
          onClick={closeSidebar}
          onKeyDown={(e) => e.key === 'Enter' && closeSidebar()}
          role="button"
          tabIndex={0}
          aria-label="Close navigation menu"
        />
      )}

      {/* Main content area */}
      <div className="lg:pl-64">
        {/* Header */}
        <Header
          onMenuClick={toggleSidebar}
        />

        {/* Page content */}
        <main
          id="main-content"
          role="main"
          aria-label={mainContentLabel}
          className="flex flex-col min-h-[calc(100vh-4rem)]"
          tabIndex={-1}
        >
          <div className="flex-1 p-4 sm:p-6 lg:p-8">
            {children}
          </div>

          {/* Footer */}
          {showFooter && <Footer />}
        </main>
      </div>

      {/* Live region for dynamic announcements */}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
        id="live-announcements"
      />
    </div>
  );
};

export default Layout;

/**
 * useAnnounce hook - Announces messages to screen readers
 *
 * @example
 * ```tsx
 * const announce = useAnnounce();
 *
 * // Announce a message
 * announce('Item added to cart');
 * ```
 */
export const useAnnounce = () => {
  return useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    const liveRegion = document.getElementById('live-announcements');
    if (liveRegion) {
      liveRegion.setAttribute('aria-live', priority);
      liveRegion.textContent = message;

      // Clear after announcement
      setTimeout(() => {
        liveRegion.textContent = '';
      }, 1000);
    }
  }, []);
};
