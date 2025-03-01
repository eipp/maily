import React, { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { createUniqueId, trapFocus, announceToScreenReader } from '@/utils/accessibility';
import { useFocusManagement } from '@/hooks/useFocusManagement';

export interface AccessibleModalProps {
  /**
   * Whether the modal is open
   */
  isOpen: boolean;

  /**
   * Callback when the modal is closed
   */
  onClose: () => void;

  /**
   * Modal title (for screen readers and heading)
   */
  title: string;

  /**
   * Modal content
   */
  children: React.ReactNode;

  /**
   * Whether to close the modal when clicking outside
   */
  closeOnOutsideClick?: boolean;

  /**
   * Whether to close the modal when pressing Escape
   */
  closeOnEscape?: boolean;

  /**
   * Additional CSS class for the modal
   */
  className?: string;

  /**
   * Additional CSS class for the overlay
   */
  overlayClassName?: string;

  /**
   * Additional CSS class for the modal content
   */
  contentClassName?: string;

  /**
   * Whether to show a close button
   */
  showCloseButton?: boolean;

  /**
   * Label for the close button
   */
  closeButtonLabel?: string;

  /**
   * Initial element to focus when the modal opens
   */
  initialFocusSelector?: string;
}

/**
 * Accessible modal component that follows WAI-ARIA best practices
 * Includes focus management, keyboard navigation, and screen reader support
 */
export const AccessibleModal: React.FC<AccessibleModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  closeOnOutsideClick = true,
  closeOnEscape = true,
  className = '',
  overlayClassName = '',
  contentClassName = '',
  showCloseButton = true,
  closeButtonLabel = 'Close',
  initialFocusSelector,
}) => {
  const modalId = useRef(createUniqueId('modal')).current;
  const titleId = useRef(createUniqueId('modal-title')).current;
  const descriptionId = useRef(createUniqueId('modal-description')).current;

  // Use focus management hook
  const { containerRef, focusFirst, focusElement } = useFocusManagement({
    trapFocus: true,
    autoFocus: !initialFocusSelector,
    active: isOpen,
  });

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (isOpen && closeOnEscape && e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, closeOnEscape, onClose]);

  // Focus initial element
  useEffect(() => {
    if (isOpen && initialFocusSelector) {
      // Small delay to ensure the modal is rendered
      setTimeout(() => {
        focusElement(initialFocusSelector);
      }, 50);
    }
  }, [isOpen, initialFocusSelector, focusElement]);

  // Announce modal to screen readers
  useEffect(() => {
    if (isOpen) {
      announceToScreenReader(`Dialog opened: ${title}`);
    }
  }, [isOpen, title]);

  // Prevent body scrolling when modal is open
  useEffect(() => {
    if (isOpen) {
      const originalStyle = window.getComputedStyle(document.body).overflow;
      document.body.style.overflow = 'hidden';

      return () => {
        document.body.style.overflow = originalStyle;
      };
    }
  }, [isOpen]);

  // Handle outside click
  const handleOverlayClick = (e: React.MouseEvent) => {
    if (closeOnOutsideClick && e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!isOpen) {
    return null;
  }

  // Use createPortal to render the modal at the end of the document body
  return createPortal(
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center ${overlayClassName}`}
      style={{
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
      }}
      onClick={handleOverlayClick}
      role="presentation"
    >
      <div
        ref={containerRef as React.RefObject<HTMLDivElement>}
        id={modalId}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
        className={`relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-auto ${className}`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 id={titleId} className="text-xl font-semibold">
            {title}
          </h2>

          {showCloseButton && (
            <button
              type="button"
              onClick={onClose}
              aria-label={closeButtonLabel}
              className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          )}
        </div>

        <div id={descriptionId} className={`p-4 ${contentClassName}`}>
          {children}
        </div>
      </div>
    </div>,
    document.body
  );
};

export default AccessibleModal;
