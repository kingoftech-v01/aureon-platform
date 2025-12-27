/**
 * Footer Component
 * Aureon by Rhematek Solutions
 *
 * Application footer with links and copyright
 */

import React from 'react';
import { Link } from 'react-router-dom';

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="md:flex md:items-center md:justify-between">
          {/* Left side: Branding and tagline */}
          <div className="flex flex-col space-y-2">
            <div className="flex items-center space-x-2">
              <div className="w-6 h-6 bg-gradient-to-br from-primary-500 to-accent-500 rounded flex items-center justify-center">
                <span className="text-white font-bold text-sm">A</span>
              </div>
              <span className="text-sm font-semibold text-gray-900 dark:text-white">
                Aureon
              </span>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 italic">
              From Signature to Cash, Everything Runs Automatically.
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              © {currentYear} Rhematek Solutions. All rights reserved.
            </p>
          </div>

          {/* Right side: Links */}
          <div className="mt-4 md:mt-0">
            <div className="flex flex-wrap gap-x-6 gap-y-2">
              <Link
                to="/about"
                className="text-xs text-gray-600 dark:text-gray-400 hover:text-primary-500 dark:hover:text-primary-400 transition-colors"
              >
                About
              </Link>
              <Link
                to="/privacy"
                className="text-xs text-gray-600 dark:text-gray-400 hover:text-primary-500 dark:hover:text-primary-400 transition-colors"
              >
                Privacy Policy
              </Link>
              <Link
                to="/terms"
                className="text-xs text-gray-600 dark:text-gray-400 hover:text-primary-500 dark:hover:text-primary-400 transition-colors"
              >
                Terms of Service
              </Link>
              <Link
                to="/support"
                className="text-xs text-gray-600 dark:text-gray-400 hover:text-primary-500 dark:hover:text-primary-400 transition-colors"
              >
                Support
              </Link>
              <a
                href="https://rhematek-solutions.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-gray-600 dark:text-gray-400 hover:text-primary-500 dark:hover:text-primary-400 transition-colors"
              >
                Rhematek Solutions
              </a>
            </div>

            {/* Version info */}
            <div className="mt-2 text-xs text-gray-500 dark:text-gray-500">
              Version 1.0.0
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
