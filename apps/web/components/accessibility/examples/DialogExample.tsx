import React, { useState } from 'react';
import AccessibleDialog from '../AccessibleDialog';
import AccessibleButton from '../AccessibleButton';

/**
 * Example component demonstrating the usage of the AccessibleDialog
 */
const DialogExample: React.FC = () => {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
  });
  const [submittedData, setSubmittedData] = useState<{ name: string; email: string } | null>(null);

  // Open the dialog
  const openDialog = () => {
    setIsDialogOpen(true);
  };

  // Close the dialog
  const closeDialog = () => {
    setIsDialogOpen(false);
  };

  // Handle form input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittedData({ ...formData });
    closeDialog();

    // Reset form data
    setFormData({
      name: '',
      email: '',
    });
  };

  return (
    <div className="p-6 max-w-md mx-auto bg-white rounded-xl shadow-md">
      <h2 className="text-xl font-bold mb-4">Accessible Dialog Example</h2>

      <div className="mb-6">
        <p className="text-gray-600 mb-4">
          Click the button below to open an accessible dialog with a form.
          The dialog demonstrates proper focus management, keyboard navigation,
          and screen reader support.
        </p>

        <AccessibleButton
          variant="primary"
          onPress={openDialog}
        >
          Open Dialog
        </AccessibleButton>
      </div>

      {submittedData && (
        <div className="mt-4 p-3 bg-gray-50 rounded-md">
          <h3 className="text-sm font-medium text-gray-700">Submitted Data:</h3>
          <p className="mt-1 text-sm text-gray-900">
            Name: {submittedData.name}
          </p>
          <p className="text-sm text-gray-900">
            Email: {submittedData.email}
          </p>
        </div>
      )}

      <div className="mt-6">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Accessibility Features:</h3>
        <ul className="list-disc pl-5 text-sm text-gray-600 space-y-1">
          <li>Focus is trapped within the dialog when open</li>
          <li>Focus is restored to the trigger button when closed</li>
          <li>Escape key closes the dialog</li>
          <li>Screen readers announce the dialog title</li>
          <li>ARIA attributes for proper screen reader support</li>
          <li>Clicking outside the dialog closes it</li>
        </ul>
      </div>

      {/* The Dialog Component */}
      <AccessibleDialog
        title="Contact Form"
        isOpen={isDialogOpen}
        onClose={closeDialog}
        size="md"
      >
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label
                htmlFor="name"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Name
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>

            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Email
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>

            <div className="flex justify-end space-x-3 pt-4 mt-4 border-t border-gray-200">
              <AccessibleButton
                variant="outline"
                onPress={closeDialog}
                type="button"
              >
                Cancel
              </AccessibleButton>

              <AccessibleButton
                variant="primary"
                type="submit"
              >
                Submit
              </AccessibleButton>
            </div>
          </div>
        </form>
      </AccessibleDialog>
    </div>
  );
};

export default DialogExample;
