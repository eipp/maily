import React from 'react';
import DatePickerExample from './examples/DatePickerExample';
import ComboBoxExample from './examples/ComboBoxExample';
import DialogExample from './examples/DialogExample';
import TabsExample from './examples/TabsExample';
import AccessibleTabs, { TabItem } from './AccessibleTabs';

/**
 * A showcase component that demonstrates all the accessible components
 * This component can be used as a reference and documentation for developers
 */
const AccessibilityShowcase: React.FC = () => {
  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-bold mb-2">Accessibility Components Showcase</h1>
        <p className="text-gray-600 max-w-3xl mx-auto">
          This showcase demonstrates the accessible components implemented as part of Sprint 7.
          These components follow WCAG 2.1 AA guidelines and provide a solid foundation for building
          accessible user interfaces.
        </p>
      </header>

      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-4 border-b pb-2">Component Gallery</h2>
        <p className="mb-4">
          Select a component category below to view examples and documentation.
        </p>

        <AccessibleTabs
          label="Component Categories"
          defaultSelectedKey="datepicker"
          className="mb-8"
        >
          <TabItem key="datepicker" title="Date Picker">
            <div className="py-4">
              <h3 className="text-xl font-semibold mb-4">Accessible Date Picker</h3>
              <p className="mb-4 text-gray-700">
                The AccessibleDatePicker component provides a fully accessible date selection experience
                with keyboard navigation, screen reader support, and proper ARIA attributes.
              </p>
              <DatePickerExample />
            </div>
          </TabItem>

          <TabItem key="combobox" title="Combo Box">
            <div className="py-4">
              <h3 className="text-xl font-semibold mb-4">Accessible Combo Box</h3>
              <p className="mb-4 text-gray-700">
                The AccessibleComboBox component provides an accessible autocomplete input with dropdown
                that supports keyboard navigation, screen readers, and proper ARIA attributes.
              </p>
              <ComboBoxExample />
            </div>
          </TabItem>

          <TabItem key="dialog" title="Dialog">
            <div className="py-4">
              <h3 className="text-xl font-semibold mb-4">Accessible Dialog</h3>
              <p className="mb-4 text-gray-700">
                The AccessibleDialog component ensures proper focus management, keyboard navigation,
                and screen reader support for modal dialogs.
              </p>
              <DialogExample />
            </div>
          </TabItem>

          <TabItem key="tabs" title="Tabs">
            <div className="py-4">
              <h3 className="text-xl font-semibold mb-4">Accessible Tabs</h3>
              <p className="mb-4 text-gray-700">
                The AccessibleTabs component provides an accessible tabbed interface with support for
                both horizontal and vertical orientations, keyboard navigation, and screen reader announcements.
              </p>
              <TabsExample />
            </div>
          </TabItem>
        </AccessibleTabs>
      </div>

      <div className="bg-gray-50 p-6 rounded-lg">
        <h2 className="text-2xl font-bold mb-4">Accessibility Guidelines</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-semibold mb-2">Keyboard Navigation</h3>
            <p className="mb-2 text-gray-700">
              All components support full keyboard navigation, allowing users to interact
              without relying on a mouse or touch input.
            </p>
            <ul className="list-disc pl-5 text-gray-600 space-y-1">
              <li>Use Tab to navigate between interactive elements</li>
              <li>Use arrow keys for navigation within components</li>
              <li>Use Enter or Space to activate buttons and controls</li>
              <li>Use Escape to close dialogs and dropdowns</li>
            </ul>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-2">Screen Reader Support</h3>
            <p className="mb-2 text-gray-700">
              Components include appropriate ARIA attributes and follow best practices
              for screen reader compatibility.
            </p>
            <ul className="list-disc pl-5 text-gray-600 space-y-1">
              <li>Proper labeling of interactive elements</li>
              <li>Appropriate role attributes</li>
              <li>State announcements (expanded, selected, etc.)</li>
              <li>Descriptive error messages</li>
            </ul>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-2">Focus Management</h3>
            <p className="mb-2 text-gray-700">
              Components handle focus appropriately, ensuring users always know where they are
              in the interface.
            </p>
            <ul className="list-disc pl-5 text-gray-600 space-y-1">
              <li>Visible focus indicators</li>
              <li>Focus trapping in modal dialogs</li>
              <li>Focus restoration when components unmount</li>
              <li>Logical focus order</li>
            </ul>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-2">Visual Design</h3>
            <p className="mb-2 text-gray-700">
              Components are designed with accessibility in mind, ensuring sufficient contrast
              and clear visual indicators.
            </p>
            <ul className="list-disc pl-5 text-gray-600 space-y-1">
              <li>Color contrast meeting WCAG AA standards</li>
              <li>Visual indicators not relying solely on color</li>
              <li>Consistent design patterns</li>
              <li>Adequate text size and spacing</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AccessibilityShowcase;
