/**
 * Accessibility utilities for Maily
 * These utilities help implement consistent accessibility features across the application
 */

import React from 'react';

/**
 * Handles keyboard navigation for a list of items
 * @param event Keyboard event
 * @param currentIndex Current focused index
 * @param itemsCount Total number of items
 * @param onSelect Callback when an item is selected
 * @returns New index or undefined if no navigation occurred
 */
export function handleListKeyboardNavigation(
  event: React.KeyboardEvent,
  currentIndex: number,
  itemsCount: number,
  onSelect?: (index: number) => void
): number | undefined {
  let newIndex: number | undefined;

  switch (event.key) {
    case 'ArrowDown':
    case 'ArrowRight':
      event.preventDefault();
      newIndex = (currentIndex + 1) % itemsCount;
      break;
    case 'ArrowUp':
    case 'ArrowLeft':
      event.preventDefault();
      newIndex = (currentIndex - 1 + itemsCount) % itemsCount;
      break;
    case 'Home':
      event.preventDefault();
      newIndex = 0;
      break;
    case 'End':
      event.preventDefault();
      newIndex = itemsCount - 1;
      break;
    case 'Enter':
    case ' ':
      event.preventDefault();
      if (onSelect) {
        onSelect(currentIndex);
      }
      return currentIndex;
    default:
      return undefined;
  }

  if (onSelect && newIndex !== undefined) {
    onSelect(newIndex);
  }

  return newIndex;
}

/**
 * Creates an ID that is unique within the document
 * @param prefix Prefix for the ID
 * @returns A unique ID
 */
export function createUniqueId(prefix: string = 'maily'): string {
  return `${prefix}-${Math.random().toString(36).substring(2, 9)}`;
}

/**
 * Announces a message to screen readers using an ARIA live region
 * @param message Message to announce
 * @param priority Priority of the announcement ('polite' or 'assertive')
 */
export function announceToScreenReader(
  message: string,
  priority: 'polite' | 'assertive' = 'polite'
): void {
  // Try to find an existing announcer element
  let announcer = document.getElementById(`sr-announcer-${priority}`);

  // Create the announcer if it doesn't exist
  if (!announcer) {
    announcer = document.createElement('div');
    announcer.id = `sr-announcer-${priority}`;
    announcer.setAttribute('aria-live', priority);
    announcer.setAttribute('aria-atomic', 'true');
    announcer.className = 'sr-only';
    document.body.appendChild(announcer);
  }

  // Set the message
  announcer.textContent = '';

  // Use setTimeout to ensure the DOM update is noticed by screen readers
  setTimeout(() => {
    if (announcer) {
      announcer.textContent = message;
    }
  }, 50);
}

/**
 * Checks if an element is visible to screen readers
 * @param element Element to check
 * @returns Whether the element is visible to screen readers
 */
export function isVisibleToScreenReaders(element: HTMLElement): boolean {
  const style = window.getComputedStyle(element);

  return !(
    element.hasAttribute('aria-hidden') && element.getAttribute('aria-hidden') === 'true' ||
    style.display === 'none' ||
    style.visibility === 'hidden' ||
    style.opacity === '0' ||
    (element.hasAttribute('hidden'))
  );
}

/**
 * Focuses the first focusable element within a container
 * @param container Container element
 * @returns Whether focus was set
 */
export function focusFirstElement(container: HTMLElement): boolean {
  const focusableElements = container.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );

  if (focusableElements.length > 0) {
    (focusableElements[0] as HTMLElement).focus();
    return true;
  }

  return false;
}

/**
 * Traps focus within a container
 * @param container Container element
 * @returns Cleanup function
 */
export function trapFocus(container: HTMLElement): () => void {
  const focusableElements = container.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );

  if (focusableElements.length === 0) return () => {};

  const firstElement = focusableElements[0] as HTMLElement;
  const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Tab') {
      if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
      } else if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
      }
    }
  };

  container.addEventListener('keydown', handleKeyDown);

  return () => {
    container.removeEventListener('keydown', handleKeyDown);
  };
}
