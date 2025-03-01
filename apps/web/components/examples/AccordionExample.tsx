import React, { useState } from 'react';
import { AccessibleAccordion, AccordionItem } from '../accessibility';

/**
 * Example component demonstrating how to use the AccessibleAccordion
 */
export const AccordionExample: React.FC = () => {
  const [expandedIds, setExpandedIds] = useState<string[]>(['section1']);

  // Define accordion items
  const accordionItems: AccordionItem[] = [
    {
      id: 'section1',
      header: (
        <div className="flex items-center">
          <span className="mr-2">📧</span>
          <span>Email Templates</span>
        </div>
      ),
      content: (
        <div className="p-4">
          <p>Create and manage your email templates. Customize designs, save templates for reuse, and organize them into categories.</p>
          <ul className="list-disc pl-5 mt-2">
            <li>Drag-and-drop editor</li>
            <li>HTML customization</li>
            <li>Template categories</li>
          </ul>
        </div>
      ),
    },
    {
      id: 'section2',
      header: (
        <div className="flex items-center">
          <span className="mr-2">👥</span>
          <span>Subscriber Management</span>
        </div>
      ),
      content: (
        <div className="p-4">
          <p>Manage your subscriber lists, segments, and individual contacts. Import and export subscribers, track engagement, and maintain list hygiene.</p>
          <button className="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
            View Subscribers
          </button>
        </div>
      ),
    },
    {
      id: 'section3',
      header: (
        <div className="flex items-center">
          <span className="mr-2">📊</span>
          <span>Analytics & Reporting</span>
        </div>
      ),
      content: (
        <div className="p-4">
          <p>Track the performance of your email campaigns with detailed analytics. Monitor open rates, click-through rates, conversions, and more.</p>
          <div className="mt-3 h-32 bg-gray-100 rounded flex items-center justify-center">
            [Chart Placeholder]
          </div>
        </div>
      ),
    },
    {
      id: 'section4',
      header: (
        <div className="flex items-center">
          <span className="mr-2">🔒</span>
          <span>Account Settings</span>
        </div>
      ),
      content: (
        <div className="p-4">
          <p>Manage your account settings, billing information, and user permissions.</p>
          <form className="mt-2">
            <div className="mb-2">
              <label htmlFor="email" className="block mb-1">Email Address</label>
              <input
                type="email"
                id="email"
                className="w-full px-3 py-2 border rounded"
                defaultValue="user@example.com"
              />
            </div>
            <button type="button" className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600">
              Save Changes
            </button>
          </form>
        </div>
      ),
      disabled: true,
    },
  ];

  // Handle accordion changes
  const handleAccordionChange = (ids: string[]) => {
    setExpandedIds(ids);
    console.log('Expanded sections:', ids);
  };

  return (
    <div className="max-w-3xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Maily Features</h1>

      <div className="mb-8">
        <h2 className="text-lg font-semibold mb-2">Single Expansion Mode</h2>
        <AccessibleAccordion
          items={accordionItems}
          defaultExpandedIds={['section1']}
          onChange={handleAccordionChange}
          className="border rounded-lg overflow-hidden"
          itemClassName="border-b last:border-b-0"
          headerClassName="p-4 bg-gray-50 hover:bg-gray-100 flex justify-between items-center"
          panelClassName="bg-white"
          expandedClassName="bg-gray-50"
        />
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-2">Multiple Expansion Mode</h2>
        <p className="text-sm text-gray-600 mb-4">
          Currently expanded: {expandedIds.join(', ') || 'none'}
        </p>
        <AccessibleAccordion
          items={accordionItems}
          allowMultiple={true}
          defaultExpandedIds={['section2', 'section3']}
          onChange={setExpandedIds}
          className="border rounded-lg overflow-hidden"
          itemClassName="border-b last:border-b-0"
          headerClassName="p-4 bg-gray-50 hover:bg-gray-100 flex justify-between items-center"
          panelClassName="bg-white"
          expandedClassName="bg-gray-50"
        />
      </div>

      <div className="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <h3 className="font-semibold text-yellow-800">Notes:</h3>
        <ul className="mt-2 list-disc pl-5 text-sm text-yellow-700">
          <li>The "Account Settings" section is disabled and cannot be expanded</li>
          <li>The first accordion allows only one section to be expanded at a time</li>
          <li>The second accordion allows multiple sections to be expanded simultaneously</li>
          <li>Both accordions are fully keyboard accessible - try using Tab, arrows, Home, End, Enter, and Space</li>
        </ul>
      </div>
    </div>
  );
};

export default AccordionExample;
