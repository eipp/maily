import React, { useState, useRef, useEffect } from 'react';
import { createUniqueId } from '@/utils/accessibility';

export interface AccessibleTooltipProps {
  /**
   * Content to display in the tooltip
   */
  content: React.ReactNode;

  /**
   * Children element that triggers the tooltip
   */
  children: React.ReactElement;

  /**
   * Position of the tooltip
   */
  position?: 'top' | 'right' | 'bottom' | 'left';

  /**
   * Delay before showing the tooltip (ms)
   */
  showDelay?: number;

  /**
   * Delay before hiding the tooltip (ms)
   */
  hideDelay?: number;

  /**
   * Whether the tooltip is disabled
   */
  disabled?: boolean;

  /**
   * Additional CSS class for the tooltip
   */
  className?: string;
}

/**
 * Accessible tooltip component that follows WAI-ARIA best practices
 * Supports keyboard and mouse interactions
 */
export const AccessibleTooltip: React.FC<AccessibleTooltipProps> = ({
  content,
  children,
  position = 'top',
  showDelay = 300,
  hideDelay = 200,
  disabled = false,
  className = '',
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const tooltipId = useRef(createUniqueId('tooltip')).current;
  const showTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const hideTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const triggerRef = useRef<HTMLElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  // Clear timeouts on unmount
  useEffect(() => {
    return () => {
      if (showTimeoutRef.current) clearTimeout(showTimeoutRef.current);
      if (hideTimeoutRef.current) clearTimeout(hideTimeoutRef.current);
    };
  }, []);

  // Show tooltip with delay
  const showTooltip = () => {
    if (disabled) return;

    if (hideTimeoutRef.current) {
      clearTimeout(hideTimeoutRef.current);
      hideTimeoutRef.current = null;
    }

    if (!isVisible && !showTimeoutRef.current) {
      showTimeoutRef.current = setTimeout(() => {
        setIsVisible(true);
        showTimeoutRef.current = null;
      }, showDelay);
    }
  };

  // Hide tooltip with delay
  const hideTooltip = () => {
    if (showTimeoutRef.current) {
      clearTimeout(showTimeoutRef.current);
      showTimeoutRef.current = null;
    }

    if (isVisible && !hideTimeoutRef.current) {
      hideTimeoutRef.current = setTimeout(() => {
        setIsVisible(false);
        hideTimeoutRef.current = null;
      }, hideDelay);
    }
  };

  // Handle mouse enter
  const handleMouseEnter = () => {
    setIsHovered(true);
    showTooltip();
  };

  // Handle mouse leave
  const handleMouseLeave = () => {
    setIsHovered(false);
    if (!isFocused) {
      hideTooltip();
    }
  };

  // Handle focus
  const handleFocus = () => {
    setIsFocused(true);
    showTooltip();
  };

  // Handle blur
  const handleBlur = () => {
    setIsFocused(false);
    if (!isHovered) {
      hideTooltip();
    }
  };

  // Handle escape key
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape' && isVisible) {
      setIsVisible(false);
      if (showTimeoutRef.current) {
        clearTimeout(showTimeoutRef.current);
        showTimeoutRef.current = null;
      }
      if (hideTimeoutRef.current) {
        clearTimeout(hideTimeoutRef.current);
        hideTimeoutRef.current = null;
      }
    }
  };

  // Calculate tooltip position
  const getTooltipStyle = () => {
    if (!triggerRef.current || !tooltipRef.current) {
      return {};
    }

    const triggerRect = triggerRef.current.getBoundingClientRect();
    const tooltipRect = tooltipRef.current.getBoundingClientRect();

    let top = 0;
    let left = 0;

    switch (position) {
      case 'top':
        top = -tooltipRect.height - 8;
        left = (triggerRect.width - tooltipRect.width) / 2;
        break;
      case 'right':
        top = (triggerRect.height - tooltipRect.height) / 2;
        left = triggerRect.width + 8;
        break;
      case 'bottom':
        top = triggerRect.height + 8;
        left = (triggerRect.width - tooltipRect.width) / 2;
        break;
      case 'left':
        top = (triggerRect.height - tooltipRect.height) / 2;
        left = -tooltipRect.width - 8;
        break;
    }

    return {
      top: `${top}px`,
      left: `${left}px`,
    };
  };

  // Clone the child element to add event handlers and aria attributes
  const triggerElement = React.cloneElement(children, {
    ref: triggerRef,
    'aria-describedby': isVisible ? tooltipId : undefined,
    onMouseEnter: (e: React.MouseEvent) => {
      handleMouseEnter();
      if (children.props.onMouseEnter) {
        children.props.onMouseEnter(e);
      }
    },
    onMouseLeave: (e: React.MouseEvent) => {
      handleMouseLeave();
      if (children.props.onMouseLeave) {
        children.props.onMouseLeave(e);
      }
    },
    onFocus: (e: React.FocusEvent) => {
      handleFocus();
      if (children.props.onFocus) {
        children.props.onFocus(e);
      }
    },
    onBlur: (e: React.FocusEvent) => {
      handleBlur();
      if (children.props.onBlur) {
        children.props.onBlur(e);
      }
    },
    onKeyDown: (e: React.KeyboardEvent) => {
      handleKeyDown(e);
      if (children.props.onKeyDown) {
        children.props.onKeyDown(e);
      }
    },
  });

  return (
    <div className="relative inline-block">
      {triggerElement}

      {isVisible && (
        <div
          ref={tooltipRef}
          id={tooltipId}
          role="tooltip"
          className={`absolute z-50 px-2 py-1 text-sm rounded shadow-md ${className}`}
          style={{
            ...getTooltipStyle(),
            backgroundColor: 'var(--tooltip-bg, #333)',
            color: 'var(--tooltip-text, white)',
          }}
        >
          {content}
          <div
            className="tooltip-arrow"
            style={{
              position: 'absolute',
              width: '8px',
              height: '8px',
              backgroundColor: 'inherit',
              transform: 'rotate(45deg)',
              ...(position === 'top' && {
                bottom: '-4px',
                left: 'calc(50% - 4px)',
              }),
              ...(position === 'right' && {
                left: '-4px',
                top: 'calc(50% - 4px)',
              }),
              ...(position === 'bottom' && {
                top: '-4px',
                left: 'calc(50% - 4px)',
              }),
              ...(position === 'left' && {
                right: '-4px',
                top: 'calc(50% - 4px)',
              }),
            }}
          />
        </div>
      )}
    </div>
  );
};

export default AccessibleTooltip;
