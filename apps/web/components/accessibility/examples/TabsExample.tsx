import React, { useState } from 'react';
import AccessibleTabs, { TabItem } from '../AccessibleTabs';

/**
 * Example component demonstrating the usage of the AccessibleTabs
 */
const TabsExample: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState('tab1');

  // Handle tab selection change
  const handleTabChange = (key: string) => {
    setSelectedTab(key);
    console.log('Selected tab:', key);
  };

  return (
    <div className="p-6 max-w-3xl mx-auto bg-white rounded-xl shadow-md">
      <h2 className="text-xl font-bold mb-4">Accessible Tabs Example</h2>

      <div className="mb-6">
        <p className="text-gray-600 mb-4">
          This example demonstrates accessible tabs with both horizontal and vertical orientations.
          The tabs support keyboard navigation, proper ARIA attributes, and focus management.
        </p>
      </div>

      <div className="mb-8">
        <h3 className="text-lg font-medium mb-3">Horizontal Tabs</h3>
        <AccessibleTabs
          label="Product Information"
          defaultSelectedKey="tab1"
          onSelectionChange={handleTabChange}
          className="mb-6"
        >
          <TabItem key="tab1" title="Description">
            <div className="prose">
              <h4 className="text-lg font-medium mb-2">Product Description</h4>
              <p>
                This is a high-quality product designed for maximum durability and performance.
                Made with premium materials, it's built to last and exceed your expectations.
              </p>
              <p className="mt-2">
                Our product has been tested in extreme conditions to ensure it meets the highest
                standards of quality and reliability.
              </p>
            </div>
          </TabItem>
          <TabItem key="tab2" title="Specifications">
            <div className="prose">
              <h4 className="text-lg font-medium mb-2">Technical Specifications</h4>
              <ul className="list-disc pl-5 space-y-1">
                <li>Dimensions: 10" x 8" x 2"</li>
                <li>Weight: 2.5 lbs</li>
                <li>Material: Aircraft-grade aluminum</li>
                <li>Battery Life: 12 hours</li>
                <li>Water Resistance: IP67 rated</li>
              </ul>
            </div>
          </TabItem>
          <TabItem key="tab3" title="Reviews">
            <div className="prose">
              <h4 className="text-lg font-medium mb-2">Customer Reviews</h4>
              <div className="space-y-3">
                <div className="border-b pb-3">
                  <div className="flex items-center">
                    <span className="text-yellow-500">★★★★★</span>
                    <span className="ml-2 font-medium">Excellent product!</span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    This exceeded my expectations. Would definitely recommend!
                  </p>
                </div>
                <div className="border-b pb-3">
                  <div className="flex items-center">
                    <span className="text-yellow-500">★★★★☆</span>
                    <span className="ml-2 font-medium">Great value</span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    Good quality for the price. Very satisfied with my purchase.
                  </p>
                </div>
              </div>
            </div>
          </TabItem>
        </AccessibleTabs>
      </div>

      <div className="mb-8">
        <h3 className="text-lg font-medium mb-3">Vertical Tabs</h3>
        <div className="flex">
          <AccessibleTabs
            label="Company Information"
            defaultSelectedKey="about"
            orientation="vertical"
            className="min-h-[200px]"
          >
            <TabItem key="about" title="About Us">
              <div className="prose">
                <h4 className="text-lg font-medium mb-2">About Our Company</h4>
                <p>
                  Founded in 2010, our company has been at the forefront of innovation
                  in our industry. We're dedicated to creating products that improve
                  people's lives while maintaining the highest standards of quality.
                </p>
              </div>
            </TabItem>
            <TabItem key="mission" title="Our Mission">
              <div className="prose">
                <h4 className="text-lg font-medium mb-2">Our Mission</h4>
                <p>
                  Our mission is to provide sustainable, high-quality products that
                  meet the needs of our customers while minimizing our environmental
                  impact. We believe in responsible business practices and giving back
                  to our community.
                </p>
              </div>
            </TabItem>
            <TabItem key="team" title="Our Team">
              <div className="prose">
                <h4 className="text-lg font-medium mb-2">Meet Our Team</h4>
                <p>
                  Our diverse team of experts brings together decades of experience
                  in design, engineering, and customer service. We're passionate about
                  what we do and committed to excellence in every aspect of our work.
                </p>
              </div>
            </TabItem>
          </AccessibleTabs>
        </div>
      </div>

      <div className="mt-6">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Accessibility Features:</h3>
        <ul className="list-disc pl-5 text-sm text-gray-600 space-y-1">
          <li>Keyboard navigation (Tab, Arrow keys)</li>
          <li>ARIA attributes for screen reader support</li>
          <li>Focus management</li>
          <li>Proper tab and panel relationships</li>
          <li>Support for both horizontal and vertical orientations</li>
          <li>Visual indicators for focus and selection states</li>
        </ul>
      </div>

      <div className="mt-4">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Keyboard Navigation:</h3>
        <ul className="list-disc pl-5 text-sm text-gray-600 space-y-1">
          <li><strong>Tab:</strong> Move focus to the tab list</li>
          <li><strong>Arrow Left/Right:</strong> Navigate between tabs (horizontal orientation)</li>
          <li><strong>Arrow Up/Down:</strong> Navigate between tabs (vertical orientation)</li>
          <li><strong>Space/Enter:</strong> Activate the focused tab</li>
          <li><strong>Home:</strong> Move focus to the first tab</li>
          <li><strong>End:</strong> Move focus to the last tab</li>
        </ul>
      </div>
    </div>
  );
};

export default TabsExample;
