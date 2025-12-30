/**
 * Accessibility Hooks
 * Aureon by Rhematek Solutions
 *
 * Collection of React hooks for building accessible components.
 * Helps achieve WCAG 2.1 Level AA compliance and Lighthouse 95+ scores.
 */

import { useEffect, useRef, useState, useCallback, useMemo } from 'react';

/**
 * useReducedMotion - Detects user preference for reduced motion
 *
 * @returns boolean indicating if reduced motion is preferred
 *
 * @example
 * ```tsx
 * const prefersReducedMotion = useReducedMotion();
 *
 * return (
 *   <div className={prefersReducedMotion ? 'static' : 'animate-slide-in'}>
 *     Content
 *   </div>
 * );
 * ```
 */
export const useReducedMotion = (): boolean => {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(() => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

    const handleChange = (event: MediaQueryListEvent) => {
      setPrefersReducedMotion(event.matches);
    };

    // Modern browsers
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }

    // Legacy browsers
    mediaQuery.addListener(handleChange);
    return () => mediaQuery.removeListener(handleChange);
  }, []);

  return prefersReducedMotion;
};

/**
 * useHighContrastMode - Detects if user prefers high contrast mode
 *
 * @returns boolean indicating if high contrast is enabled
 */
export const useHighContrastMode = (): boolean => {
  const [isHighContrast, setIsHighContrast] = useState(() => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia('(forced-colors: active)').matches;
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const mediaQuery = window.matchMedia('(forced-colors: active)');

    const handleChange = (event: MediaQueryListEvent) => {
      setIsHighContrast(event.matches);
    };

    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }

    mediaQuery.addListener(handleChange);
    return () => mediaQuery.removeListener(handleChange);
  }, []);

  return isHighContrast;
};

/**
 * useKeyboardNavigation - Handles keyboard navigation for lists
 *
 * @param itemCount - Number of items in the list
 * @param options - Configuration options
 *
 * @example
 * ```tsx
 * const { activeIndex, handleKeyDown, setActiveIndex } = useKeyboardNavigation(items.length, {
 *   loop: true,
 *   onSelect: (index) => handleItemSelect(items[index]),
 * });
 *
 * return (
 *   <ul role="listbox" onKeyDown={handleKeyDown}>
 *     {items.map((item, index) => (
 *       <li
 *         key={item.id}
 *         role="option"
 *         aria-selected={index === activeIndex}
 *         tabIndex={index === activeIndex ? 0 : -1}
 *       >
 *         {item.label}
 *       </li>
 *     ))}
 *   </ul>
 * );
 * ```
 */
interface KeyboardNavigationOptions {
  /** Whether to loop from last to first and vice versa */
  loop?: boolean;
  /** Whether navigation is horizontal */
  horizontal?: boolean;
  /** Callback when Enter/Space is pressed */
  onSelect?: (index: number) => void;
  /** Callback when Escape is pressed */
  onEscape?: () => void;
  /** Initial active index */
  initialIndex?: number;
}

export const useKeyboardNavigation = (
  itemCount: number,
  options: KeyboardNavigationOptions = {}
) => {
  const {
    loop = false,
    horizontal = false,
    onSelect,
    onEscape,
    initialIndex = 0,
  } = options;

  const [activeIndex, setActiveIndex] = useState(initialIndex);

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      const prevKey = horizontal ? 'ArrowLeft' : 'ArrowUp';
      const nextKey = horizontal ? 'ArrowRight' : 'ArrowDown';

      switch (event.key) {
        case prevKey:
          event.preventDefault();
          setActiveIndex((prev) => {
            if (prev <= 0) {
              return loop ? itemCount - 1 : 0;
            }
            return prev - 1;
          });
          break;

        case nextKey:
          event.preventDefault();
          setActiveIndex((prev) => {
            if (prev >= itemCount - 1) {
              return loop ? 0 : itemCount - 1;
            }
            return prev + 1;
          });
          break;

        case 'Home':
          event.preventDefault();
          setActiveIndex(0);
          break;

        case 'End':
          event.preventDefault();
          setActiveIndex(itemCount - 1);
          break;

        case 'Enter':
        case ' ':
          event.preventDefault();
          onSelect?.(activeIndex);
          break;

        case 'Escape':
          event.preventDefault();
          onEscape?.();
          break;
      }
    },
    [activeIndex, itemCount, loop, horizontal, onSelect, onEscape]
  );

  return { activeIndex, handleKeyDown, setActiveIndex };
};

/**
 * useAriaLiveAnnounce - Announces messages to screen readers
 *
 * @param priority - 'polite' or 'assertive'
 *
 * @example
 * ```tsx
 * const announce = useAriaLiveAnnounce();
 *
 * const handleSave = async () => {
 *   await saveData();
 *   announce('Changes saved successfully');
 * };
 * ```
 */
export const useAriaLiveAnnounce = (priority: 'polite' | 'assertive' = 'polite') => {
  const announce = useCallback(
    (message: string, customPriority?: 'polite' | 'assertive') => {
      // Find or create the live region
      let liveRegion = document.getElementById('aria-live-region');

      if (!liveRegion) {
        liveRegion = document.createElement('div');
        liveRegion.id = 'aria-live-region';
        liveRegion.setAttribute('aria-live', customPriority || priority);
        liveRegion.setAttribute('aria-atomic', 'true');
        liveRegion.setAttribute('role', 'status');
        liveRegion.className = 'sr-only';
        Object.assign(liveRegion.style, {
          position: 'absolute',
          width: '1px',
          height: '1px',
          padding: '0',
          margin: '-1px',
          overflow: 'hidden',
          clip: 'rect(0, 0, 0, 0)',
          whiteSpace: 'nowrap',
          border: '0',
        });
        document.body.appendChild(liveRegion);
      } else {
        liveRegion.setAttribute('aria-live', customPriority || priority);
      }

      // Clear and set the message (this triggers the announcement)
      liveRegion.textContent = '';
      requestAnimationFrame(() => {
        liveRegion!.textContent = message;
      });

      // Clear after a delay
      setTimeout(() => {
        if (liveRegion) {
          liveRegion.textContent = '';
        }
      }, 1000);
    },
    [priority]
  );

  return announce;
};

/**
 * useFocusVisible - Detects if focus should be visible
 *
 * Returns true only when the user is navigating with keyboard.
 * Helps implement :focus-visible behavior for browsers that don't support it.
 */
export const useFocusVisible = (): boolean => {
  const [focusVisible, setFocusVisible] = useState(false);
  const hadKeyboardEvent = useRef(false);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Tab' || event.key === 'Escape') {
        hadKeyboardEvent.current = true;
      }
    };

    const handlePointerDown = () => {
      hadKeyboardEvent.current = false;
    };

    const handleFocus = () => {
      if (hadKeyboardEvent.current) {
        setFocusVisible(true);
      }
    };

    const handleBlur = () => {
      setFocusVisible(false);
    };

    document.addEventListener('keydown', handleKeyDown, true);
    document.addEventListener('pointerdown', handlePointerDown, true);
    document.addEventListener('focus', handleFocus, true);
    document.addEventListener('blur', handleBlur, true);

    return () => {
      document.removeEventListener('keydown', handleKeyDown, true);
      document.removeEventListener('pointerdown', handlePointerDown, true);
      document.removeEventListener('focus', handleFocus, true);
      document.removeEventListener('blur', handleBlur, true);
    };
  }, []);

  return focusVisible;
};

/**
 * useTabIndex - Manages tab index for roving tabindex pattern
 *
 * @param isSelected - Whether this item is currently selected
 * @param isDisabled - Whether this item is disabled
 *
 * @example
 * ```tsx
 * const Tab = ({ isSelected, isDisabled, onClick, children }) => {
 *   const tabIndex = useTabIndex(isSelected, isDisabled);
 *
 *   return (
 *     <button
 *       role="tab"
 *       aria-selected={isSelected}
 *       aria-disabled={isDisabled}
 *       tabIndex={tabIndex}
 *       onClick={onClick}
 *     >
 *       {children}
 *     </button>
 *   );
 * };
 * ```
 */
export const useTabIndex = (isSelected: boolean, isDisabled: boolean = false): number => {
  return useMemo(() => {
    if (isDisabled) return -1;
    return isSelected ? 0 : -1;
  }, [isSelected, isDisabled]);
};

/**
 * useDocumentTitle - Sets the document title with accessibility considerations
 *
 * @param title - The page title
 * @param options - Configuration options
 *
 * @example
 * ```tsx
 * const DashboardPage = () => {
 *   useDocumentTitle('Dashboard', { suffix: 'Aureon' });
 *
 *   return <div>Dashboard content</div>;
 * };
 * ```
 */
interface DocumentTitleOptions {
  /** Suffix to append (e.g., app name) */
  suffix?: string;
  /** Separator between title and suffix */
  separator?: string;
  /** Whether to restore the original title on unmount */
  restoreOnUnmount?: boolean;
}

export const useDocumentTitle = (
  title: string,
  options: DocumentTitleOptions = {}
) => {
  const { suffix = 'Aureon', separator = ' | ', restoreOnUnmount = false } = options;
  const previousTitle = useRef<string>('');

  useEffect(() => {
    previousTitle.current = document.title;
    const fullTitle = suffix ? `${title}${separator}${suffix}` : title;
    document.title = fullTitle;

    return () => {
      if (restoreOnUnmount) {
        document.title = previousTitle.current;
      }
    };
  }, [title, suffix, separator, restoreOnUnmount]);
};

/**
 * useId - Generates a unique ID for accessibility purposes
 *
 * This is a polyfill for React 18's useId hook for older React versions.
 *
 * @param prefix - Optional prefix for the ID
 *
 * @example
 * ```tsx
 * const Input = ({ label }) => {
 *   const id = useId('input');
 *
 *   return (
 *     <>
 *       <label htmlFor={id}>{label}</label>
 *       <input id={id} type="text" />
 *     </>
 *   );
 * };
 * ```
 */
let idCounter = 0;

export const useId = (prefix: string = 'aureon'): string => {
  const [id] = useState(() => {
    idCounter += 1;
    return `${prefix}-${idCounter}`;
  });

  return id;
};

/**
 * useEscapeKey - Calls a callback when Escape key is pressed
 *
 * @param callback - Function to call on Escape
 * @param enabled - Whether the hook is active
 *
 * @example
 * ```tsx
 * const Modal = ({ isOpen, onClose }) => {
 *   useEscapeKey(onClose, isOpen);
 *
 *   if (!isOpen) return null;
 *   return <div>Modal content</div>;
 * };
 * ```
 */
export const useEscapeKey = (callback: () => void, enabled: boolean = true) => {
  useEffect(() => {
    if (!enabled) return;

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        callback();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [callback, enabled]);
};

/**
 * useClickOutside - Detects clicks outside an element
 *
 * @param callback - Function to call on outside click
 * @param enabled - Whether the hook is active
 *
 * @example
 * ```tsx
 * const Dropdown = ({ isOpen, onClose }) => {
 *   const ref = useClickOutside<HTMLDivElement>(onClose, isOpen);
 *
 *   return <div ref={ref}>Dropdown content</div>;
 * };
 * ```
 */
export const useClickOutside = <T extends HTMLElement>(
  callback: () => void,
  enabled: boolean = true
) => {
  const ref = useRef<T>(null);

  useEffect(() => {
    if (!enabled) return;

    const handleClick = (event: MouseEvent | TouchEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        callback();
      }
    };

    document.addEventListener('mousedown', handleClick);
    document.addEventListener('touchstart', handleClick);

    return () => {
      document.removeEventListener('mousedown', handleClick);
      document.removeEventListener('touchstart', handleClick);
    };
  }, [callback, enabled]);

  return ref;
};

/**
 * useScrollLock - Prevents body scroll when active
 *
 * @param locked - Whether scroll should be locked
 *
 * @example
 * ```tsx
 * const Modal = ({ isOpen }) => {
 *   useScrollLock(isOpen);
 *
 *   return <div>Modal content</div>;
 * };
 * ```
 */
export const useScrollLock = (locked: boolean) => {
  useEffect(() => {
    if (!locked) return;

    const originalStyle = window.getComputedStyle(document.body).overflow;
    document.body.style.overflow = 'hidden';

    return () => {
      document.body.style.overflow = originalStyle;
    };
  }, [locked]);
};
