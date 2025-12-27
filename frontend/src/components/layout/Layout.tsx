/**
 * Layout Component
 * Aureon by Rhematek Solutions
 *
 * Main application layout with sidebar, header, and footer
 */

import React, { useState, ReactNode } from 'react';
import Sidebar from './Sidebar';
import Header from './Header';
import Footer from './Footer';

interface LayoutProps {
  children: ReactNode;
  showFooter?: boolean;
}

const Layout: React.FC<LayoutProps> = ({ children, showFooter = true }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const closeSidebar = () => {
    setSidebarOpen(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Sidebar */}
      <Sidebar isOpen={sidebarOpen} onClose={closeSidebar} />

      {/* Main content area */}
      <div className="lg:pl-64">
        {/* Header */}
        <Header onMenuClick={toggleSidebar} />

        {/* Page content */}
        <main className="flex flex-col min-h-[calc(100vh-4rem)]">
          <div className="flex-1 p-4 sm:p-6 lg:p-8">
            {children}
          </div>

          {/* Footer */}
          {showFooter && <Footer />}
        </main>
      </div>
    </div>
  );
};

export default Layout;
