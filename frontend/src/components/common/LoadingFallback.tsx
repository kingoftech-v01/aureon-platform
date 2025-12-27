/**
 * Loading Fallback Components
 * Aureon by Rhematek Solutions
 *
 * Loading states for Suspense boundaries
 */

import React from 'react';

/**
 * Page-level loading fallback
 */
export const PageLoadingFallback: React.FC = () => {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="text-center">
        {/* Spinner */}
        <div className="inline-block w-16 h-16 border-4 border-primary-200 dark:border-primary-900 border-t-primary-600 dark:border-t-primary-400 rounded-full animate-spin mb-4" />

        <p className="text-gray-600 dark:text-gray-400 font-medium">
          Loading...
        </p>
      </div>
    </div>
  );
};

/**
 * Component-level loading fallback
 */
export const ComponentLoadingFallback: React.FC = () => {
  return (
    <div className="flex items-center justify-center min-h-[200px] p-4">
      <div className="text-center">
        <div className="inline-block w-8 h-8 border-4 border-primary-200 dark:border-primary-900 border-t-primary-600 dark:border-t-primary-400 rounded-full animate-spin mb-2" />
        <p className="text-sm text-gray-600 dark:text-gray-400">Loading...</p>
      </div>
    </div>
  );
};

/**
 * Inline loading spinner
 */
export const InlineLoadingFallback: React.FC<{ text?: string }> = ({
  text = 'Loading...',
}) => {
  return (
    <div className="flex items-center gap-2 p-2">
      <div className="inline-block w-4 h-4 border-2 border-primary-200 dark:border-primary-900 border-t-primary-600 dark:border-t-primary-400 rounded-full animate-spin" />
      <span className="text-sm text-gray-600 dark:text-gray-400">{text}</span>
    </div>
  );
};

/**
 * Full-page loading overlay
 */
export const OverlayLoadingFallback: React.FC<{ text?: string }> = ({
  text = 'Loading...',
}) => {
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-xl">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-primary-200 dark:border-primary-900 border-t-primary-600 dark:border-t-primary-400 rounded-full animate-spin" />
          <p className="text-gray-900 dark:text-white font-medium">{text}</p>
        </div>
      </div>
    </div>
  );
};

/**
 * Skeleton loading for list items
 */
export const ListLoadingFallback: React.FC<{ count?: number }> = ({
  count = 5,
}) => {
  return (
    <div className="space-y-3 animate-pulse">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 p-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
          <div className="w-12 h-12 bg-gray-300 dark:bg-gray-700 rounded-full" />
          <div className="flex-1 space-y-2">
            <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-3/4" />
            <div className="h-3 bg-gray-300 dark:bg-gray-700 rounded w-1/2" />
          </div>
        </div>
      ))}
    </div>
  );
};

/**
 * Card loading skeleton
 */
export const CardLoadingFallback: React.FC = () => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 animate-pulse">
      <div className="space-y-4">
        <div className="h-6 bg-gray-300 dark:bg-gray-700 rounded w-2/3" />
        <div className="space-y-2">
          <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded" />
          <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-5/6" />
          <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-4/6" />
        </div>
      </div>
    </div>
  );
};

export default PageLoadingFallback;
