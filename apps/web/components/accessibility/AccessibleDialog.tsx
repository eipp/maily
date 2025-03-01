import React, { useRef, ReactNode } from 'react';
import { useDialog } from '@react-aria/dialog';
import { FocusScope } from '@react-aria/focus';
import { useOverlay, useModal, OverlayContainer, DismissButton } from '@react-aria/overlays';
import { useButton } from '@react-aria/button';

interface AccessibleDialogProps {
  title: string;
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
  isDismissable?: boolean;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

/**
 * An accessible dialog component built with React Aria
 * This component ensures proper focus management, keyboard navigation,
 * and screen reader support for modal dialogs.
 */
const AccessibleDialog: React.FC<AccessibleDialogProps> = ({
  title,
  isOpen,
  onClose,
  children,
  isDismissable = true,
  size = 'md',
  className = '',
}) => {
  // Refs for DOM elements
  const dialogRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  // Handle dialog accessibility
  const { dialogProps, titleProps } = useDialog({}, dialogRef);

  // Handle overlay accessibility (backdrop, dismissing, etc.)
  const { overlayProps, underlayProps } = useOverlay(
    {
      isOpen,
      onClose,
      isDismissable,
      shouldCloseOnInteractOutside: (element) => {
        // Don't close when interacting with the dialog itself
        return !dialogRef.current?.contains(element);
      },
    },
    dialogRef
  );

  // Handle modal accessibility (focus containment, etc.)
  const { modalProps } = useModal();

  // Handle close button accessibility
  const { buttonProps } = useButton(
    {
      onPress: onClose,
      'aria-label': 'Close dialog',
    },
    closeButtonRef
  );

  // Size classes for the dialog
  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
  };

  // If the dialog is not open, don't render anything
  if (!isOpen) {
    return null;
  }

  return (
    <OverlayContainer>
      <div
        className="fixed inset-0 z-50 flex items-center justify-center"
        {...underlayProps}
      >
        {/* Backdrop */}
        <div className="fixed inset-0 bg-black bg-opacity-50 transition-opacity" />

        {/* Dialog */}
        <FocusScope contain restoreFocus autoFocus>
          <div
            {...overlayProps}
            {...dialogProps}
            {...modalProps}
            ref={dialogRef}
            className={`
              relative bg-white rounded-lg shadow-xl p-6 m-4 w-full
              ${sizeClasses[size]} z-50 overflow-y-auto max-h-[90vh]
              ${className}
            `}
            role="dialog"
            aria-modal="true"
          >
            {/* Add a hidden dismiss button at the start for screen readers */}
            <DismissButton onDismiss={onClose} />

            {/* Header */}
            <div className="flex items-start justify-between mb-4 pb-3 border-b border-gray-200">
              <h2
                {...titleProps}
                className="text-xl font-semibold text-gray-900"
              >
                {title}
              </h2>
              {isDismissable && (
                <button
                  {...buttonProps}
                  ref={closeButtonRef}
                  className="text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-md"
                >
                  <span className="sr-only">Close</span>
                  <svg
                    className="h-6 w-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              )}
            </div>

            {/* Content */}
            <div className="mt-2">{children}</div>

            {/* Add a hidden dismiss button at the end for screen readers */}
            <DismissButton onDismiss={onClose} />
          </div>
        </FocusScope>
      </div>
    </OverlayContainer>
  );
};

export default AccessibleDialog;
