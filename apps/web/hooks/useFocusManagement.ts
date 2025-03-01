import { useRef, useEffect, useCallback, RefObject } from 'react';
import { focusFirstElement, trapFocus } from '@/utils/accessibility';

interface FocusManagementOptions {
  /**
   * Whether to trap focus within the container
   */
  trapFocus?: boolean;

  /**
   * Whether to auto-focus the first focusable element when mounted
   */
  autoFocus?: boolean;

  /**
   * Element to focus when the component is unmounted
   */
  returnFocusTo?: RefObject<HTMLElement> | null;

  /**
   * Whether the container is currently active/visible
   */
  active?: boolean;
}

/**
 * Hook for managing focus within a container
 * Provides focus trapping, auto-focus, and return focus functionality
 */
export function useFocusManagement({
  trapFocus: shouldTrapFocus = false,
  autoFocus = false,
  returnFocusTo = null,
  active = true,
}: FocusManagementOptions = {}) {
  const containerRef = useRef<HTMLElement>(null);
  const previouslyFocusedElement = useRef<HTMLElement | null>(null);

  // Store the previously focused element when the component mounts
  useEffect(() => {
    if (active) {
      previouslyFocusedElement.current = document.activeElement as HTMLElement;
    }

    return () => {
      // Return focus when the component unmounts
      if (active && returnFocusTo?.current) {
        returnFocusTo.current.focus();
      } else if (active && previouslyFocusedElement.current) {
        previouslyFocusedElement.current.focus();
      }
    };
  }, [active, returnFocusTo]);

  // Set up focus trapping
  useEffect(() => {
    if (!active || !shouldTrapFocus || !containerRef.current) return;

    const cleanup = trapFocus(containerRef.current);
    return cleanup;
  }, [active, shouldTrapFocus]);

  // Auto-focus the first focusable element
  useEffect(() => {
    if (active && autoFocus && containerRef.current) {
      focusFirstElement(containerRef.current);
    }
  }, [active, autoFocus]);

  // Focus the first element programmatically
  const focusFirst = useCallback(() => {
    if (containerRef.current) {
      return focusFirstElement(containerRef.current);
    }
    return false;
  }, []);

  // Focus a specific element by selector
  const focusElement = useCallback((selector: string) => {
    if (containerRef.current) {
      const element = containerRef.current.querySelector(selector) as HTMLElement;
      if (element) {
        element.focus();
        return true;
      }
    }
    return false;
  }, []);

  return {
    containerRef,
    focusFirst,
    focusElement,
  };
}
