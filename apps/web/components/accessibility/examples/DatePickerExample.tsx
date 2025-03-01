import React, { useState } from 'react';
import { parseDate, today, getLocalTimeZone } from '@internationalized/date';
import AccessibleDatePicker from '../AccessibleDatePicker';

/**
 * Example component demonstrating the usage of the AccessibleDatePicker
 */
const DatePickerExample: React.FC = () => {
  // Initialize with today's date
  const [date, setDate] = useState(today(getLocalTimeZone()));

  // Handler for date changes
  const handleDateChange = (newDate: any) => {
    setDate(newDate);
    console.log('Selected date:', newDate.toString());
  };

  return (
    <div className="p-6 max-w-md mx-auto bg-white rounded-xl shadow-md">
      <h2 className="text-xl font-bold mb-4">Accessible Date Picker Example</h2>

      <div className="mb-6">
        <AccessibleDatePicker
          label="Select a date"
          value={date}
          onChange={handleDateChange}
          minValue={parseDate('2023-01-01')}
          maxValue={parseDate('2025-12-31')}
        />
      </div>

      <div className="mt-4 p-3 bg-gray-50 rounded-md">
        <h3 className="text-sm font-medium text-gray-700">Selected Date:</h3>
        <p className="mt-1 text-sm text-gray-900">
          {date ? date.toString() : 'No date selected'}
        </p>
      </div>

      <div className="mt-6">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Accessibility Features:</h3>
        <ul className="list-disc pl-5 text-sm text-gray-600 space-y-1">
          <li>Keyboard navigation (Tab, Arrow keys, Space, Enter)</li>
          <li>Screen reader announcements</li>
          <li>ARIA attributes for accessibility</li>
          <li>Focus management</li>
          <li>High contrast visuals</li>
        </ul>
      </div>
    </div>
  );
};

export default DatePickerExample;
