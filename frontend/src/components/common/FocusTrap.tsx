/**
 * FocusTrap Component
 * Aureon by Rhematek Solutions
 *
 * Traps focus within a container for accessible modals, dialogs, and menus.
 * Essential for WCAG 2.1 Level A compliance (Success Criterion 2.4.3)
 */

import React, { useEffect, useRef, useCallback, ReactNode } from 'react';

interface FocusTrapProps {
  /** Child elements to render within the focus trap */
  children: ReactNode;
  /** Whether the focus trap is active */
  active?: boolean;
  /** Whether to automatically focus the first focusable element on mount */
  autoFocus?: boolean;
  /** Whether to restore focus to the previously focused element on unmount */
  restoreFocus?: boolean;
  /** Callback when escape key is pressed */
  onEscape?: () => void;
  /** Custom initial focus element selector */
  initialFocusSelector?: string;
  /** Whether to include the container itself in the tab order */
  includeContainer?: boolean;
  /** Additional CSS classes */
  className?: string;
  /** ARIA role for the container */
  role?: string;
  /** ARIA label for the container */
  'aria-label'?: string;
  /** ARIA labelledby for the container */
  'aria-labelledby'?: string;
  /** ARIA describedby for the container */
  'aria-describedby'?: string;
  /** Whether the content is a modal dialog */
  'aria-modal'?: boolean;
}

// Selector for all focusable elements
const FOCUSABLE_SELECTOR = [
  'a[href]:not([disabled]):not([tabindex="-1"])',
  'button:not([disabled]):not([tabindex="-1"])',
  'input:not([disabled]):not([tabindex="-1"]):not([type="hidden"])',
  'select:not([disabled]):not([tabindex="-1"])',
  'textarea:not([disabled]):not([tabindex="-1"])',
  '[tabindex]:not([tabindex="-1"])',
  '[contenteditable="true"]',
].join(', ');

/**
 * FocusTrap - Traps keyboard focus within a container
 *
 * @example
 * ```tsx
 * // Modal with focus trap
 * <FocusTrap
 *   active={isOpen}
 *   onEscape={handleClose}
 *   role="dialog"
 *   aria-labelledby="modal-title"
 *   aria-modal
 * >
 *   <div className="modal">
 *     <h2 id="modal-title">Modal Title</h2>
 *     <button onClick={handleClose}>Close</button>
 *   </div>
 * </FocusTrap>
 * ```
 */
const FocusTrap: React.FC<FocusTrapProps> = ({
  children,
  active = true,
  autoFocus = true,
  restoreFocus = true,
  onEscape,
  initialFocusSelector,
  includeContainer = false,
  className = '',
  role,
  'aria-label': ariaLabel,
  'aria-labelledby': ariaLabelledby,
  'aria-describedby': ariaDescribedby,
  'aria-modal': ariaModal,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<Element | null>(null);

  // Get all focusable elements within the container
  const getFocusableElements = useCallback((): HTMLElement[] => {
    if (!containerRef.current) return [];

    const elements = Array.from(
      containerRef.current.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)
    );

    // Filter out elements that are not visible
    return elements.filter((el) => {
      const style = window.getComputedStyle(el);
      return (
        style.display !== 'none' &&
        style.visibility !== 'hidden' &&
        el.offsetParent !== null
      );
    });
  }, []);

  // Focus the first focusable element
  const focusFirstElement = useCallback(() => {
    if (!containerRef.current) return;

    // Try custom initial focus selector first
    if (initialFocusSelector) {
      const initialElement = containerRef.current.querySelector<HTMLElement>(
        initialFocusSelector
      );
      if (initialElement) {
        initialElement.focus();
        return;
      }
    }

    // Focus the first focusable element
    const focusableElements = getFocusableElements();
    if (focusableElements.length > 0) {
      focusableElements[0].focus();
    } else if (includeContainer && containerRef.current) {
      // Focus the container itself if no focusable children
      containerRef.current.tabIndex = -1;
      containerRef.current.focus();
    }
  }, [getFocusableElements, initialFocusSelector, includeContainer]);

  // Handle Tab key navigation
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!active) return;

      // Handle Escape key
      if (event.key === 'Escape' && onEscape) {
        event.preventDefault();
        onEscape();
        return;
      }

      // Handle Tab key for focus trap
      if (event.key === 'Tab') {
        const focusableElements = getFocusableElements();
        if (focusableElements.length === 0) return;

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        // Shift + Tab on first element -> focus last element
        if (event.shiftKey && document.activeElement === firstElement) {
          event.preventDefault();
          lastElement.focus();
        }
        // Tab on last element -> focus first element
        else if (!event.shiftKey && document.activeElement === lastElement) {
          event.preventDefault();
          firstElement.focus();
        }
      }
    },
    [active, getFocusableElements, onEscape]
  );

  // Store the previously focused element and set up event listeners
  useEffect(() => {
    if (!active) return;

    // Store currently focused element
    previousActiveElement.current = document.activeElement;

    // Add keydown listener
    document.addEventListener('keydown', handleKeyDown);

    // Auto focus the first element
    if (autoFocus) {
      // Use setTimeout to ensure the focus trap content is rendered
      const timeoutId = setTimeout(focusFirstElement, 0);
      return () => {
        clearTimeout(timeoutId);
        document.removeEventListener('keydown', handleKeyDown);
      };
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [active, autoFocus, focusFirstElement, handleKeyDown]);

  // Restore focus when unmounting or deactivating
  useEffect(() => {
    return () => {
      if (restoreFocus && previousActiveElement.current) {
        const element = previousActiveElement.current as HTMLElement;
        if (element && typeof element.focus === 'function') {
          // Use setTimeout to ensure focus restoration happens after any other updates
          setTimeout(() => element.focus(), 0);
        }
      }
    };
  }, [restoreFocus]);

  // Handle clicks outside the focus trap (prevent focus from escaping)
  const handleFocusOut = useCallback(
    (event: FocusEvent) => {
      if (!active || !containerRef.current) return;

      const relatedTarget = event.relatedTarget as HTMLElement;

      // If focus is moving outside the container, bring it back
      if (relatedTarget && !containerRef.current.contains(relatedTarget)) {
        event.preventDefault();
        focusFirstElement();
      }
    },
    [active, focusFirstElement]
  );

  useEffect(() => {
    if (!active || !containerRef.current) return;

    const container = containerRef.current;
    container.addEventListener('focusout', handleFocusOut as EventListener);

    return () => {
      container.removeEventListener('focusout', handleFocusOut as EventListener);
    };
  }, [active, handleFocusOut]);

  return (
    <div
      ref={containerRef}
      className={className}
      role={role}
      aria-label={ariaLabel}
      aria-labelledby={ariaLabelledby}
      aria-describedby={ariaDescribedby}
      aria-modal={ariaModal}
    >
      {children}
    </div>
  );
};

export default FocusTrap;

/**
 * useFocusReturn hook - Returns focus to a specified element
 *
 * @example
 * ```tsx
 * const { setFocusReturnTarget, returnFocus } = useFocusReturn();
 *
 * // When opening a modal
 * setFocusReturnTarget(buttonRef.current);
 *
 * // When closing the modal
 * returnFocus();
 * ```
 */
export const useFocusReturn = () => {
  const focusReturnTarget = useRef<HTMLElement | null>(null);

  const setFocusReturnTarget = useCallback((element: HTMLElement | null) => {
    focusReturnTarget.current = element;
  }, []);

  const returnFocus = useCallback(() => {
    if (focusReturnTarget.current) {
      focusReturnTarget.current.focus();
      focusReturnTarget.current = null;
    }
  }, []);

  return { setFocusReturnTarget, returnFocus };
};

/**
 * useFocusOnMount hook - Focuses an element when mounted
 *
 * @example
 * ```tsx
 * const inputRef = useFocusOnMount<HTMLInputElement>();
 *
 * return <input ref={inputRef} type="text" />;
 * ```
 */
export const useFocusOnMount = <T extends HTMLElement>() => {
  const ref = useRef<T>(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.focus();
    }
  }, []);

  return ref;
};
