import { useState, useCallback, KeyboardEvent } from 'react';

interface KeyboardNavigationOptions {
  itemCount: number;
  initialIndex?: number;
  loop?: boolean;
  orientation?: 'horizontal' | 'vertical' | 'both';
  onSelect?: (index: number) => void;
  onKeyDown?: (event: KeyboardEvent) => void;
}

/**
 * A hook for managing keyboard navigation in lists, menus, and other navigable components
 * Supports arrow keys, home/end, and enter/space for selection
 */
export function useKeyboardNavigation({
  itemCount,
  initialIndex = -1,
  loop = true,
  orientation = 'both',
  onSelect,
  onKeyDown,
}: KeyboardNavigationOptions) {
  const [activeIndex, setActiveIndex] = useState<number>(initialIndex);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      // Allow custom key handling
      if (onKeyDown) {
        onKeyDown(event);
      }

      if (itemCount === 0) return;

      let newIndex = activeIndex;
      let handled = false;

      // Handle navigation keys
      switch (event.key) {
        case 'ArrowDown':
          if (orientation === 'vertical' || orientation === 'both') {
            handled = true;
            if (activeIndex < itemCount - 1) {
              newIndex = activeIndex + 1;
            } else if (loop) {
              newIndex = 0;
            }
          }
          break;

        case 'ArrowUp':
          if (orientation === 'vertical' || orientation === 'both') {
            handled = true;
            if (activeIndex > 0) {
              newIndex = activeIndex - 1;
            } else if (loop) {
              newIndex = itemCount - 1;
            }
          }
          break;

        case 'ArrowRight':
          if (orientation === 'horizontal' || orientation === 'both') {
            handled = true;
            if (activeIndex < itemCount - 1) {
              newIndex = activeIndex + 1;
            } else if (loop) {
              newIndex = 0;
            }
          }
          break;

        case 'ArrowLeft':
          if (orientation === 'horizontal' || orientation === 'both') {
            handled = true;
            if (activeIndex > 0) {
              newIndex = activeIndex - 1;
            } else if (loop) {
              newIndex = itemCount - 1;
            }
          }
          break;

        case 'Home':
          handled = true;
          newIndex = 0;
          break;

        case 'End':
          handled = true;
          newIndex = itemCount - 1;
          break;

        case 'Enter':
        case ' ':
          if (activeIndex !== -1 && onSelect) {
            handled = true;
            onSelect(activeIndex);
          }
          break;

        default:
          break;
      }

      if (handled) {
        event.preventDefault();
        setActiveIndex(newIndex);
      }
    },
    [activeIndex, itemCount, loop, orientation, onSelect, onKeyDown]
  );

  const setActiveItem = useCallback(
    (index: number) => {
      if (index >= -1 && index < itemCount) {
        setActiveIndex(index);
      }
    },
    [itemCount]
  );

  return {
    activeIndex,
    setActiveItem,
    handleKeyDown,
    getItemProps: (index: number) => ({
      tabIndex: index === activeIndex ? 0 : -1,
      'aria-selected': index === activeIndex,
      onKeyDown: handleKeyDown,
      onFocus: () => setActiveItem(index),
    }),
  };
}
