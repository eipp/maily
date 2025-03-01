import React, { useState, useRef, useEffect } from 'react';
import { createUniqueId, handleListKeyboardNavigation } from '@/utils/accessibility';
import { useKeyboardNavigation } from '@/hooks/useKeyboardNavigation';

export interface TabItem {
  /**
   * Unique identifier for the tab
   */
  id: string;

  /**
   * Tab label
   */
  label: React.ReactNode;

  /**
   * Tab content
   */
  content: React.ReactNode;

  /**
   * Whether the tab is disabled
   */
  disabled?: boolean;
}

export interface AccessibleTabsProps {
  /**
   * Array of tab items
   */
  tabs: TabItem[];

  /**
   * Default active tab index
   */
  defaultActiveTab?: number;

  /**
   * Callback when tab changes
   */
  onChange?: (index: number) => void;

  /**
   * Additional CSS class for the tabs container
   */
  className?: string;

  /**
   * Additional CSS class for the tab list
   */
  tabListClassName?: string;

  /**
   * Additional CSS class for the tab panels
   */
  tabPanelClassName?: string;

  /**
   * Additional CSS class for the active tab
   */
  activeTabClassName?: string;

  /**
   * Additional CSS class for inactive tabs
   */
  inactiveTabClassName?: string;
}

/**
 * Accessible tabs component that follows WAI-ARIA best practices
 * Supports keyboard navigation and screen reader announcements
 */
export const AccessibleTabs: React.FC<AccessibleTabsProps> = ({
  tabs,
  defaultActiveTab = 0,
  onChange,
  className = '',
  tabListClassName = '',
  tabPanelClassName = '',
  activeTabClassName = '',
  inactiveTabClassName = '',
}) => {
  const [activeTab, setActiveTab] = useState(defaultActiveTab);
  const tabsId = useRef(createUniqueId('tabs')).current;

  // Use keyboard navigation hook
  const { activeIndex, handleKeyDown, getItemProps } = useKeyboardNavigation({
    itemCount: tabs.length,
    initialIndex: defaultActiveTab,
    orientation: 'horizontal',
    onSelect: (index) => {
      if (!tabs[index].disabled) {
        setActiveTab(index);
        onChange?.(index);
      }
    },
  });

  // Update active tab when defaultActiveTab changes
  useEffect(() => {
    setActiveTab(defaultActiveTab);
  }, [defaultActiveTab]);

  // Handle tab click
  const handleTabClick = (index: number) => {
    if (!tabs[index].disabled) {
      setActiveTab(index);
      onChange?.(index);
    }
  };

  return (
    <div className={`tabs-container ${className}`}>
      <div
        role="tablist"
        aria-label="Tabs"
        className={`flex border-b ${tabListClassName}`}
      >
        {tabs.map((tab, index) => (
          <button
            key={tab.id}
            id={`${tabsId}-tab-${index}`}
            role="tab"
            aria-selected={activeTab === index}
            aria-controls={`${tabsId}-panel-${index}`}
            aria-disabled={tab.disabled}
            tabIndex={activeTab === index ? 0 : -1}
            onClick={() => handleTabClick(index)}
            onKeyDown={handleKeyDown}
            className={`px-4 py-2 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary ${
              tab.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
            } ${
              activeTab === index
                ? `border-b-2 border-primary font-medium ${activeTabClassName}`
                : `text-gray-500 hover:text-gray-700 ${inactiveTabClassName}`
            }`}
            disabled={tab.disabled}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {tabs.map((tab, index) => (
        <div
          key={tab.id}
          id={`${tabsId}-panel-${index}`}
          role="tabpanel"
          aria-labelledby={`${tabsId}-tab-${index}`}
          tabIndex={0}
          hidden={activeTab !== index}
          className={`p-4 focus:outline-none ${tabPanelClassName}`}
        >
          {tab.content}
        </div>
      ))}
    </div>
  );
};

export default AccessibleTabs;
