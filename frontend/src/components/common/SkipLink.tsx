/**
 * SkipLink Component
 * Aureon by Rhematek Solutions
 *
 * Accessibility component that allows keyboard users to skip
 * to the main content of the page, bypassing navigation.
 * Essential for WCAG 2.1 Level A compliance (Success Criterion 2.4.1)
 */

import React, { useCallback, useRef } from 'react';

interface SkipLinkProps {
  /** The ID of the main content element to skip to */
  targetId?: string;
  /** Custom text for the skip link */
  children?: React.ReactNode;
  /** Additional CSS classes */
  className?: string;
}

/**
 * SkipLink - Skip to main content accessibility component
 *
 * This component provides a way for keyboard users to bypass
 * repetitive navigation elements and jump directly to the main content.
 *
 * @example
 * ```tsx
 * // Basic usage
 * <SkipLink />
 *
 * // Custom target
 * <SkipLink targetId="main-content">Skip to content</SkipLink>
 *
 * // Multiple skip links
 * <SkipLink targetId="main-content">Skip to main content</SkipLink>
 * <SkipLink targetId="navigation">Skip to navigation</SkipLink>
 * ```
 */
const SkipLink: React.FC<SkipLinkProps> = ({
  targetId = 'main-content',
  children = 'Skip to main content',
  className = '',
}) => {
  const linkRef = useRef<HTMLAnchorElement>(null);

  const handleClick = useCallback(
    (event: React.MouseEvent<HTMLAnchorElement>) => {
      event.preventDefault();

      const target = document.getElementById(targetId);

      if (target) {
        // Make the target focusable if it isn't already
        if (!target.hasAttribute('tabindex')) {
          target.setAttribute('tabindex', '-1');
        }

        // Scroll to the target
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });

        // Focus the target element
        target.focus({ preventScroll: true });

        // Remove the tabindex after blur to maintain natural tab order
        const handleBlur = () => {
          if (target.getAttribute('tabindex') === '-1') {
            target.removeAttribute('tabindex');
          }
          target.removeEventListener('blur', handleBlur);
        };

        target.addEventListener('blur', handleBlur);
      }
    },
    [targetId]
  );

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLAnchorElement>) => {
      // Allow Enter key to activate the link (default behavior)
      if (event.key === 'Enter') {
        handleClick(event as unknown as React.MouseEvent<HTMLAnchorElement>);
      }
    },
    [handleClick]
  );

  return (
    <a
      ref={linkRef}
      href={`#${targetId}`}
      className={`
        skip-link
        fixed
        top-0
        left-1/2
        -translate-x-1/2
        -translate-y-full
        z-[9999]
        bg-primary
        text-white
        px-6
        py-3
        rounded-b-lg
        font-semibold
        text-sm
        shadow-lg
        transition-transform
        duration-200
        ease-in-out
        focus:translate-y-0
        focus:outline-none
        focus:ring-2
        focus:ring-white
        focus:ring-offset-2
        focus:ring-offset-primary
        hover:bg-primary-dark
        ${className}
      `}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
    >
      {children}
    </a>
  );
};

/**
 * SkipLinks - Multiple skip links container
 *
 * Provides multiple skip link options for complex page layouts.
 * Useful when you have distinct sections users might want to skip to.
 */
interface SkipLinksProps {
  links: Array<{
    targetId: string;
    label: string;
  }>;
  className?: string;
}

export const SkipLinks: React.FC<SkipLinksProps> = ({ links, className = '' }) => {
  return (
    <div className={`skip-links ${className}`} role="navigation" aria-label="Skip links">
      {links.map((link, index) => (
        <SkipLink
          key={link.targetId}
          targetId={link.targetId}
          className={index > 0 ? 'ml-2' : ''}
        >
          {link.label}
        </SkipLink>
      ))}
    </div>
  );
};

/**
 * useSkipLinkTarget - Hook for managing skip link targets
 *
 * Returns ref and props to be spread on the target element.
 *
 * @example
 * ```tsx
 * const MainContent: React.FC = () => {
 *   const skipTarget = useSkipLinkTarget('main-content');
 *
 *   return (
 *     <main {...skipTarget}>
 *       Content here...
 *     </main>
 *   );
 * };
 * ```
 */
export const useSkipLinkTarget = (id: string) => {
  const ref = useRef<HTMLElement>(null);

  return {
    ref,
    id,
    tabIndex: -1,
    'aria-labelledby': undefined,
  };
};

export default SkipLink;
