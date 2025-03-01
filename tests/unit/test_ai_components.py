import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';

// Import the AI components
import { AIContentGenerator } from '../../apps/web/components/AIContentGenerator';
import { AIAssistant } from '../../apps/web/components/AIAssistant';
import { AIPromptInput } from '../../apps/web/components/AIPromptInput';
import { AIResponseDisplay } from '../../apps/web/components/AIResponseDisplay';

// Mock the AI service
vi.mock('../../apps/web/lib/ai-service', () => ({
  callAIModel: vi.fn(),
}));

// Import the mocked AI service
import { callAIModel } from '../../apps/web/lib/ai-service';

describe('AIContentGenerator', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('renders the component correctly', () => {
    render(
      <AIContentGenerator
        onContentGenerated={() => {}}
        promptTemplate="Create content for {{topic}}"
        placeholders={{ topic: 'email marketing' }}
      />
    );

    expect(screen.getByText('Generate Content')).toBeInTheDocument();
    expect(screen.getByText('AI Content Generator')).toBeInTheDocument();
  });

  it('calls the AI service when generate button is clicked', async () => {
    // Mock the AI service response
    callAIModel.mockResolvedValue({
      content: 'Generated content for email marketing',
      model: 'gpt-4',
    });

    const handleContentGenerated = vi.fn();

    render(
      <AIContentGenerator
        onContentGenerated={handleContentGenerated}
        promptTemplate="Create content for {{topic}}"
        placeholders={{ topic: 'email marketing' }}
      />
    );

    // Click the generate button
    fireEvent.click(screen.getByText('Generate Content'));

    // Wait for the AI service to be called
    await waitFor(() => {
      expect(callAIModel).toHaveBeenCalledWith({
        prompt: 'Create content for email marketing',
        options: { temperature: 0.7 },
      });
    });

    // Wait for the content to be generated
    await waitFor(() => {
      expect(handleContentGenerated).toHaveBeenCalledWith('Generated content for email marketing');
    });
  });

  it('shows loading state while generating content', async () => {
    // Mock the AI service with a delayed response
    callAIModel.mockImplementation(() => {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            content: 'Generated content for email marketing',
            model: 'gpt-4',
          });
        }, 100);
      });
    });

    render(
      <AIContentGenerator
        onContentGenerated={() => {}}
        promptTemplate="Create content for {{topic}}"
        placeholders={{ topic: 'email marketing' }}
      />
    );

    // Click the generate button
    fireEvent.click(screen.getByText('Generate Content'));

    // Check that loading state is shown
    expect(screen.getByText('Generating...')).toBeInTheDocument();

    // Wait for the loading state to be removed
    await waitFor(() => {
      expect(screen.queryByText('Generating...')).not.toBeInTheDocument();
    });
  });

  it('handles errors from the AI service', async () => {
    // Mock the AI service with an error
    callAIModel.mockRejectedValue(new Error('AI service error'));

    render(
      <AIContentGenerator
        onContentGenerated={() => {}}
        promptTemplate="Create content for {{topic}}"
        placeholders={{ topic: 'email marketing' }}
      />
    );

    // Click the generate button
    fireEvent.click(screen.getByText('Generate Content'));

    // Wait for the error message to be shown
    await waitFor(() => {
      expect(screen.getByText('Error: AI service error')).toBeInTheDocument();
    });
  });
});

describe('AIAssistant', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('renders the component correctly', () => {
    render(<AIAssistant />);

    expect(screen.getByText('AI Assistant')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Ask me anything...')).toBeInTheDocument();
  });

  it('sends user query to AI service and displays response', async () => {
    // Mock the AI service response
    callAIModel.mockResolvedValue({
      content: 'This is the AI assistant response',
      model: 'gpt-4',
    });

    render(<AIAssistant />);

    // Type a query
    fireEvent.change(screen.getByPlaceholderText('Ask me anything...'), {
      target: { value: 'How do I create an email campaign?' },
    });

    // Submit the query
    fireEvent.click(screen.getByText('Send'));

    // Wait for the AI service to be called
    await waitFor(() => {
      expect(callAIModel).toHaveBeenCalledWith({
        prompt: 'How do I create an email campaign?',
        options: { temperature: 0.5 },
      });
    });

    // Wait for the response to be displayed
    await waitFor(() => {
      expect(screen.getByText('This is the AI assistant response')).toBeInTheDocument();
    });
  });

  it('maintains conversation history', async () => {
    // Mock the AI service responses
    callAIModel.mockResolvedValueOnce({
      content: 'First response',
      model: 'gpt-4',
    });

    callAIModel.mockResolvedValueOnce({
      content: 'Second response',
      model: 'gpt-4',
    });

    render(<AIAssistant />);

    // First query
    fireEvent.change(screen.getByPlaceholderText('Ask me anything...'), {
      target: { value: 'First question' },
    });
    fireEvent.click(screen.getByText('Send'));

    // Wait for the first response
    await waitFor(() => {
      expect(screen.getByText('First response')).toBeInTheDocument();
    });

    // Second query
    fireEvent.change(screen.getByPlaceholderText('Ask me anything...'), {
      target: { value: 'Second question' },
    });
    fireEvent.click(screen.getByText('Send'));

    // Wait for the second response
    await waitFor(() => {
      expect(screen.getByText('Second response')).toBeInTheDocument();
    });

    // Check that both queries and responses are in the conversation history
    expect(screen.getByText('First question')).toBeInTheDocument();
    expect(screen.getByText('First response')).toBeInTheDocument();
    expect(screen.getByText('Second question')).toBeInTheDocument();
    expect(screen.getByText('Second response')).toBeInTheDocument();
  });
});

describe('AIPromptInput', () => {
  it('renders the component correctly', () => {
    const handleSubmit = vi.fn();

    render(
      <AIPromptInput
        onSubmit={handleSubmit}
        placeholder="Enter your prompt..."
        buttonText="Submit"
      />
    );

    expect(screen.getByPlaceholderText('Enter your prompt...')).toBeInTheDocument();
    expect(screen.getByText('Submit')).toBeInTheDocument();
  });

  it('calls onSubmit with the prompt value when submitted', () => {
    const handleSubmit = vi.fn();

    render(
      <AIPromptInput
        onSubmit={handleSubmit}
        placeholder="Enter your prompt..."
        buttonText="Submit"
      />
    );

    // Type a prompt
    fireEvent.change(screen.getByPlaceholderText('Enter your prompt...'), {
      target: { value: 'Test prompt' },
    });

    // Submit the prompt
    fireEvent.click(screen.getByText('Submit'));

    // Check that onSubmit was called with the prompt value
    expect(handleSubmit).toHaveBeenCalledWith('Test prompt');
  });

  it('disables the submit button when the prompt is empty', () => {
    const handleSubmit = vi.fn();

    render(
      <AIPromptInput
        onSubmit={handleSubmit}
        placeholder="Enter your prompt..."
        buttonText="Submit"
      />
    );

    // Check that the submit button is disabled
    expect(screen.getByText('Submit')).toBeDisabled();

    // Type a prompt
    fireEvent.change(screen.getByPlaceholderText('Enter your prompt...'), {
      target: { value: 'Test prompt' },
    });

    // Check that the submit button is enabled
    expect(screen.getByText('Submit')).not.toBeDisabled();
  });
});

describe('AIResponseDisplay', () => {
  it('renders the component correctly with a response', () => {
    render(
      <AIResponseDisplay
        response="This is the AI response"
        loading={false}
        error={null}
      />
    );

    expect(screen.getByText('This is the AI response')).toBeInTheDocument();
  });

  it('shows loading state when loading is true', () => {
    render(
      <AIResponseDisplay
        response=""
        loading={true}
        error={null}
      />
    );

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('shows error message when there is an error', () => {
    render(
      <AIResponseDisplay
        response=""
        loading={false}
        error="Error message"
      />
    );

    expect(screen.getByText('Error: Error message')).toBeInTheDocument();
  });

  it('prioritizes loading state over error message', () => {
    render(
      <AIResponseDisplay
        response=""
        loading={true}
        error="Error message"
      />
    );

    expect(screen.getByText('Loading...')).toBeInTheDocument();
    expect(screen.queryByText('Error: Error message')).not.toBeInTheDocument();
  });
});
