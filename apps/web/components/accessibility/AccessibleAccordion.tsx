import React, { useState, useRef } from 'react';
import { createUniqueId } from '@/utils/accessibility';

export interface AccordionItem {
  /**
   * Unique identifier for the accordion item
   */
  id: string;

  /**
   * Header content for the accordion item
   */
  header: React.ReactNode;

  /**
   * Panel content for the accordion item
   */
  content: React.ReactNode;

  /**
   * Whether the accordion item is disabled
   */
  disabled?: boolean;
}

export interface AccessibleAccordionProps {
  /**
   * Array of accordion items
   */
  items: AccordionItem[];

  /**
   * Whether multiple panels can be expanded at once
   */
  allowMultiple?: boolean;

  /**
   * Default expanded item IDs
   */
  defaultExpandedIds?: string[];

  /**
   * Callback when an item's expanded state changes
   */
  onChange?: (expandedIds: string[]) => void;

  /**
   * Additional CSS class for the accordion container
   */
  className?: string;

  /**
   * Additional CSS class for accordion items
   */
  itemClassName?: string;

  /**
   * Additional CSS class for accordion headers
   */
  headerClassName?: string;

  /**
   * Additional CSS class for accordion panels
   */
  panelClassName?: string;

  /**
   * Additional CSS class for expanded accordion items
   */
  expandedClassName?: string;
}

/**
 * Accessible accordion component that follows WAI-ARIA best practices
 * Supports keyboard navigation, multiple expanded panels, and screen reader announcements
 */
export const AccessibleAccordion: React.FC<AccessibleAccordionProps> = ({
  items,
  allowMultiple = false,
  defaultExpandedIds = [],
  onChange,
  className = '',
  itemClassName = '',
  headerClassName = '',
  panelClassName = '',
  expandedClassName = '',
}) => {
  const [expandedIds, setExpandedIds] = useState<string[]>(defaultExpandedIds);
  const accordionId = useRef(createUniqueId('accordion')).current;

  // Toggle item expanded state
  const toggleItem = (itemId: string) => {
    let newExpandedIds: string[];

    if (expandedIds.includes(itemId)) {
      // Collapse the item
      newExpandedIds = expandedIds.filter(id => id !== itemId);
    } else {
      // Expand the item
      if (allowMultiple) {
        // Allow multiple items to be expanded
        newExpandedIds = [...expandedIds, itemId];
      } else {
        // Only allow one item to be expanded at a time
        newExpandedIds = [itemId];
      }
    }

    setExpandedIds(newExpandedIds);
    onChange?.(newExpandedIds);
  };

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent, itemId: string, index: number) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        // Focus next header
        const nextHeader = document.getElementById(`${accordionId}-header-${Math.min(index + 1, items.length - 1)}`);
        nextHeader?.focus();
        break;

      case 'ArrowUp':
        e.preventDefault();
        // Focus previous header
        const prevHeader = document.getElementById(`${accordionId}-header-${Math.max(index - 1, 0)}`);
        prevHeader?.focus();
        break;

      case 'Home':
        e.preventDefault();
        // Focus first header
        const firstHeader = document.getElementById(`${accordionId}-header-0`);
        firstHeader?.focus();
        break;

      case 'End':
        e.preventDefault();
        // Focus last header
        const lastHeader = document.getElementById(`${accordionId}-header-${items.length - 1}`);
        lastHeader?.focus();
        break;

      case ' ':
      case 'Enter':
        e.preventDefault();
        // Toggle item if not disabled
        if (!items[index].disabled) {
          toggleItem(itemId);
        }
        break;

      default:
        break;
    }
  };

  return (
    <div
      className={`accordion ${className}`}
      role="presentation"
    >
      {items.map((item, index) => {
        const isExpanded = expandedIds.includes(item.id);
        const headerId = `${accordionId}-header-${index}`;
        const panelId = `${accordionId}-panel-${index}`;

        return (
          <div
            key={item.id}
            className={`accordion-item ${itemClassName} ${isExpanded ? expandedClassName : ''}`}
          >
            <h3>
              <button
                id={headerId}
                className={`accordion-header w-full text-left ${headerClassName}`}
                onClick={() => !item.disabled && toggleItem(item.id)}
                onKeyDown={(e) => handleKeyDown(e, item.id, index)}
                aria-expanded={isExpanded}
                aria-controls={panelId}
                aria-disabled={item.disabled}
                disabled={item.disabled}
                type="button"
              >
                {item.header}
                <span className="accordion-icon ml-auto" aria-hidden="true">
                  {isExpanded ? '−' : '+'}
                </span>
              </button>
            </h3>

            <div
              id={panelId}
              role="region"
              aria-labelledby={headerId}
              className={`accordion-panel ${panelClassName}`}
              hidden={!isExpanded}
            >
              {item.content}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default AccessibleAccordion;
