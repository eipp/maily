/**
 * Accessibility components for Maily
 * This file exports all accessibility-related components for easy imports
 */

export { default as AccessibleTooltip } from './AccessibleTooltip';
export { default as AccessibleModal } from './AccessibleModal';
export { default as AccessibleTabs } from './AccessibleTabs';
export { default as AccessibleAccordion } from './AccessibleAccordion';
export { default as SkipNavigation } from './SkipNavigation';
export { default as AxeAccessibility } from './AxeAccessibility';

// Re-export types
export type { AccessibleTooltipProps } from './AccessibleTooltip';
export type { AccessibleModalProps } from './AccessibleModal';
export type { AccessibleTabsProps, TabItem } from './AccessibleTabs';
export type { AccessibleAccordionProps, AccordionItem } from './AccessibleAccordion';
export type { SkipNavigationProps } from './SkipNavigation';
export type { AxeAccessibilityProps } from './AxeAccessibility';
