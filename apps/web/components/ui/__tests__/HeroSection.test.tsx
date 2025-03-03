import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import HeroSection from '../HeroSection';

// Mock dependencies
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    h2: ({ children, ...props }: any) => <h2 {...props}>{children}</h2>,
    p: ({ children, ...props }: any) => <p {...props}>{children}</p>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

jest.mock('../ParticleBackground', () => ({
  __esModule: true,
  default: ({ className }: any) => <div data-testid="particle-bg" className={className} />,
}));

jest.mock('../AINetworkGraph', () => ({
  __esModule: true,
  default: ({ className, height }: any) => (
    <div data-testid="ai-network-graph" className={className} style={{ height }} />
  ),
}));

jest.mock('../../utils/analytics', () => ({
  analytics: {
    trackEvent: jest.fn(),
    trackError: jest.fn(),
  },
}));

describe('HeroSection', () => {
  const mockOnSubmit = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  it('renders correctly with default props', () => {
    render(<HeroSection />);
    
    expect(screen.getByText('AI-Powered Email Marketing for the Future')).toBeInTheDocument();
    expect(screen.getByTestId('particle-bg')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter your email')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /get started/i })).toBeInTheDocument();
  });
  
  it('renders with custom title and subtitle', () => {
    const customTitle = 'Custom Title';
    const customSubtitle = 'Custom subtitle text';
    
    render(
      <HeroSection 
        title={customTitle}
        subtitle={customSubtitle}
      />
    );
    
    expect(screen.getByText(customTitle)).toBeInTheDocument();
    expect(screen.getByText(customSubtitle)).toBeInTheDocument();
  });
  
  it('validates email correctly', async () => {
    render(<HeroSection />);
    
    const emailInput = screen.getByPlaceholderText('Enter your email');
    const submitButton = screen.getByRole('button', { name: /get started/i });
    
    // Initial state - button should be disabled
    expect(submitButton).toBeDisabled();
    
    // Type invalid email
    await userEvent.type(emailInput, 'invalid-email');
    expect(submitButton).toBeDisabled();
    
    // Type valid email
    await userEvent.clear(emailInput);
    await userEvent.type(emailInput, 'test@example.com');
    expect(submitButton).not.toBeDisabled();
  });
  
  it('calls onSubmit when form is submitted with valid email', async () => {
    mockOnSubmit.mockResolvedValueOnce(undefined);
    
    render(<HeroSection onSubmit={mockOnSubmit} />);
    
    const emailInput = screen.getByPlaceholderText('Enter your email');
    const submitButton = screen.getByRole('button', { name: /get started/i });
    
    // Type valid email and submit
    await userEvent.type(emailInput, 'test@example.com');
    await userEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith('test@example.com');
    });
  });
  
  it('changes feature on button click', async () => {
    render(<HeroSection />);
    
    // Find the first feature (should be active by default)
    const firstFeatureButton = screen.getByText('Cognitive Canvas', { exact: false });
    expect(firstFeatureButton.closest('button')).toHaveClass('bg-primary');
    
    // Click on second feature
    const secondFeatureButton = screen.getByText('AI Mesh Network', { exact: false });
    await userEvent.click(secondFeatureButton);
    
    // Second feature should now be active
    expect(secondFeatureButton.closest('button')).toHaveClass('bg-primary');
  });
}); 