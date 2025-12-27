/**
 * Table Component
 * Aureon by Rhematek Solutions
 *
 * Responsive data table with sorting and selection
 */

import React, { ReactNode } from 'react';

interface TableProps {
  children: ReactNode;
  className?: string;
  striped?: boolean;
  hoverable?: boolean;
}

const Table: React.FC<TableProps> = ({
  children,
  className = '',
  striped = false,
  hoverable = true,
}) => {
  return (
    <div className="overflow-x-auto">
      <table className={`min-w-full divide-y divide-gray-200 dark:divide-gray-700 ${className}`}>
        {children}
      </table>
    </div>
  );
};

interface TableHeadProps {
  children: ReactNode;
  className?: string;
}

export const TableHead: React.FC<TableHeadProps> = ({ children, className = '' }) => {
  return (
    <thead className={`bg-gray-50 dark:bg-gray-800 ${className}`}>
      {children}
    </thead>
  );
};

interface TableBodyProps {
  children: ReactNode;
  className?: string;
}

export const TableBody: React.FC<TableBodyProps> = ({ children, className = '' }) => {
  return (
    <tbody className={`bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700 ${className}`}>
      {children}
    </tbody>
  );
};

interface TableRowProps {
  children: ReactNode;
  className?: string;
  hoverable?: boolean;
  onClick?: () => void;
}

export const TableRow: React.FC<TableRowProps> = ({
  children,
  className = '',
  hoverable = true,
  onClick,
}) => {
  const hoverStyle = hoverable ? 'hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors' : '';
  const clickableStyle = onClick ? 'cursor-pointer' : '';

  return (
    <tr className={`${hoverStyle} ${clickableStyle} ${className}`} onClick={onClick}>
      {children}
    </tr>
  );
};

interface TableHeaderCellProps {
  children: ReactNode;
  className?: string;
  sortable?: boolean;
  onSort?: () => void;
  sortDirection?: 'asc' | 'desc' | null;
  align?: 'left' | 'center' | 'right';
}

export const TableHeaderCell: React.FC<TableHeaderCellProps> = ({
  children,
  className = '',
  sortable = false,
  onSort,
  sortDirection = null,
  align = 'left',
}) => {
  const alignStyles = {
    left: 'text-left',
    center: 'text-center',
    right: 'text-right',
  };

  return (
    <th
      className={`px-6 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider ${alignStyles[align]} ${
        sortable ? 'cursor-pointer select-none hover:text-gray-700 dark:hover:text-gray-200' : ''
      } ${className}`}
      onClick={sortable ? onSort : undefined}
    >
      <div className="flex items-center justify-between">
        <span>{children}</span>

        {sortable && (
          <span className="ml-2">
            {sortDirection === 'asc' ? (
              <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z"
                  clipRule="evenodd"
                />
              </svg>
            ) : sortDirection === 'desc' ? (
              <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z"
                  clipRule="evenodd"
                />
              </svg>
            ) : (
              <svg className="h-4 w-4 text-gray-300" fill="currentColor" viewBox="0 0 20 20">
                <path d="M5 12a1 1 0 102 0V6.414l1.293 1.293a1 1 0 001.414-1.414l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L5 6.414V12zM15 8a1 1 0 10-2 0v5.586l-1.293-1.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L15 13.586V8z" />
              </svg>
            )}
          </span>
        )}
      </div>
    </th>
  );
};

interface TableCellProps {
  children: ReactNode;
  className?: string;
  align?: 'left' | 'center' | 'right';
}

export const TableCell: React.FC<TableCellProps> = ({
  children,
  className = '',
  align = 'left',
}) => {
  const alignStyles = {
    left: 'text-left',
    center: 'text-center',
    right: 'text-right',
  };

  return (
    <td className={`px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100 ${alignStyles[align]} ${className}`}>
      {children}
    </td>
  );
};

export default Table;
