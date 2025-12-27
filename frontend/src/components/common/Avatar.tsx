/**
 * Avatar Component
 * Aureon by Rhematek Solutions
 *
 * User avatar with fallback to initials
 */

import React from 'react';

type AvatarSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

interface AvatarProps {
  src?: string;
  alt?: string;
  name?: string;
  size?: AvatarSize;
  className?: string;
  status?: 'online' | 'offline' | 'away' | 'busy';
}

const Avatar: React.FC<AvatarProps> = ({
  src,
  alt,
  name,
  size = 'md',
  className = '',
  status,
}) => {
  const sizeStyles: Record<AvatarSize, { container: string; text: string }> = {
    xs: { container: 'h-6 w-6', text: 'text-xs' },
    sm: { container: 'h-8 w-8', text: 'text-sm' },
    md: { container: 'h-10 w-10', text: 'text-base' },
    lg: { container: 'h-12 w-12', text: 'text-lg' },
    xl: { container: 'h-16 w-16', text: 'text-2xl' },
  };

  const statusColors = {
    online: 'bg-green-500',
    offline: 'bg-gray-400',
    away: 'bg-yellow-500',
    busy: 'bg-red-500',
  };

  const getInitials = (name: string): string => {
    const parts = name.trim().split(' ');
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  const initials = name ? getInitials(name) : '?';

  return (
    <div className={`relative inline-block ${className}`}>
      <div
        className={`${sizeStyles[size].container} rounded-full overflow-hidden bg-gradient-to-br from-primary-400 to-accent-400 flex items-center justify-center text-white font-semibold ${sizeStyles[size].text}`}
      >
        {src ? (
          <img
            src={src}
            alt={alt || name || 'Avatar'}
            className="h-full w-full object-cover"
            onError={(e) => {
              // Fallback to initials if image fails to load
              const target = e.target as HTMLImageElement;
              target.style.display = 'none';
            }}
          />
        ) : (
          <span>{initials}</span>
        )}
      </div>

      {status && (
        <span
          className={`absolute bottom-0 right-0 block h-3 w-3 rounded-full ring-2 ring-white dark:ring-gray-800 ${statusColors[status]}`}
          aria-label={`Status: ${status}`}
        />
      )}
    </div>
  );
};

interface AvatarGroupProps {
  children: React.ReactElement<AvatarProps>[];
  max?: number;
  className?: string;
}

export const AvatarGroup: React.FC<AvatarGroupProps> = ({
  children,
  max = 3,
  className = '',
}) => {
  const visibleAvatars = children.slice(0, max);
  const remainingCount = Math.max(0, children.length - max);

  return (
    <div className={`flex -space-x-2 ${className}`}>
      {visibleAvatars.map((avatar, index) => (
        <div key={index} className="ring-2 ring-white dark:ring-gray-900 rounded-full">
          {avatar}
        </div>
      ))}

      {remainingCount > 0 && (
        <div className="h-10 w-10 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-sm font-medium text-gray-600 dark:text-gray-300 ring-2 ring-white dark:ring-gray-900">
          +{remainingCount}
        </div>
      )}
    </div>
  );
};

export default Avatar;
