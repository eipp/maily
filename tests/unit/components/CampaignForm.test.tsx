import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CampaignForm from '../../components/CampaignForm';
import { createCampaign } from '../../services/api';

// Mock the API service
jest.mock('../../services/api', () => ({
  createCampaign: jest.fn(),
}));

describe('CampaignForm', () => {
  beforeEach(() => {
    // Clear mock before each test
    jest.clearAllMocks();
  });

  it('renders all form fields', () => {
    render(<CampaignForm />);

    expect(screen.getByLabelText(/campaign name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/subject/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/content/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create campaign/i })).toBeInTheDocument();
  });

  it('handles form submission correctly', async () => {
    const mockCampaign = {
      name: 'Test Campaign',
      subject: 'Welcome to Maily',
      content: 'Hello {name}, welcome to our platform!',
    };

    (createCampaign as jest.Mock).mockResolvedValueOnce({ id: '123', ...mockCampaign });

    render(<CampaignForm />);

    // Fill out the form
    await userEvent.type(screen.getByLabelText(/campaign name/i), mockCampaign.name);
    await userEvent.type(screen.getByLabelText(/subject/i), mockCampaign.subject);
    await userEvent.type(screen.getByLabelText(/content/i), mockCampaign.content);

    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: /create campaign/i }));

    // Verify API was called with correct data
    await waitFor(() => {
      expect(createCampaign).toHaveBeenCalledWith(mockCampaign);
    });
  });

  it('displays validation errors', async () => {
    render(<CampaignForm />);

    // Submit empty form
    fireEvent.click(screen.getByRole('button', { name: /create campaign/i }));

    // Check for validation messages
    await waitFor(() => {
      expect(screen.getByText(/campaign name is required/i)).toBeInTheDocument();
      expect(screen.getByText(/subject is required/i)).toBeInTheDocument();
      expect(screen.getByText(/content is required/i)).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    const error = new Error('API Error');
    (createCampaign as jest.Mock).mockRejectedValueOnce(error);

    render(<CampaignForm />);

    // Fill out form
    await userEvent.type(screen.getByLabelText(/campaign name/i), 'Test Campaign');
    await userEvent.type(screen.getByLabelText(/subject/i), 'Test Subject');
    await userEvent.type(screen.getByLabelText(/content/i), 'Test Content');

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /create campaign/i }));

    // Check for error message
    await waitFor(() => {
      expect(screen.getByText(/failed to create campaign/i)).toBeInTheDocument();
    });
  });
});
