import React, { useState } from 'react';
import AccessibleComboBox from '../AccessibleComboBox';

// Sample data for the ComboBox
const countries = [
  { id: '1', name: 'United States' },
  { id: '2', name: 'Canada' },
  { id: '3', name: 'United Kingdom' },
  { id: '4', name: 'Australia' },
  { id: '5', name: 'Germany' },
  { id: '6', name: 'France' },
  { id: '7', name: 'Japan' },
  { id: '8', name: 'Brazil' },
  { id: '9', name: 'India' },
  { id: '10', name: 'China' },
  { id: '11', name: 'South Africa' },
  { id: '12', name: 'Mexico' },
  { id: '13', name: 'Italy' },
  { id: '14', name: 'Spain' },
  { id: '15', name: 'Netherlands' },
];

/**
 * Example component demonstrating the usage of the AccessibleComboBox
 */
const ComboBoxExample: React.FC = () => {
  const [selectedCountry, setSelectedCountry] = useState<{ id: string; name: string } | null>(null);

  // Handler for selection changes
  const handleSelectionChange = (option: { id: string; name: string } | null) => {
    setSelectedCountry(option);
    console.log('Selected country:', option?.name);
  };

  return (
    <div className="p-6 max-w-md mx-auto bg-white rounded-xl shadow-md">
      <h2 className="text-xl font-bold mb-4">Accessible ComboBox Example</h2>

      <div className="mb-6">
        <AccessibleComboBox
          label="Select a country"
          options={countries}
          onSelectionChange={handleSelectionChange}
          placeholder="Type to search countries..."
        />
      </div>

      <div className="mt-4 p-3 bg-gray-50 rounded-md">
        <h3 className="text-sm font-medium text-gray-700">Selected Country:</h3>
        <p className="mt-1 text-sm text-gray-900">
          {selectedCountry ? selectedCountry.name : 'No country selected'}
        </p>
      </div>

      <div className="mt-6">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Accessibility Features:</h3>
        <ul className="list-disc pl-5 text-sm text-gray-600 space-y-1">
          <li>Keyboard navigation (Tab, Arrow keys, Enter, Escape)</li>
          <li>Screen reader announcements</li>
          <li>ARIA attributes for accessibility</li>
          <li>Focus management</li>
          <li>Autocomplete functionality</li>
          <li>Proper labeling and state announcements</li>
        </ul>
      </div>

      <div className="mt-6">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Usage Instructions:</h3>
        <ul className="list-disc pl-5 text-sm text-gray-600 space-y-1">
          <li>Type to filter options</li>
          <li>Press Down Arrow to open dropdown and navigate options</li>
          <li>Press Enter to select the highlighted option</li>
          <li>Press Escape to close the dropdown</li>
          <li>Click on an option to select it</li>
        </ul>
      </div>
    </div>
  );
};

export default ComboBoxExample;
