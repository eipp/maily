import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import Canvas from '../../components/Canvas';

// Mock the canvas worker
jest.mock('../../workers/canvas.worker', () => ({
  postMessage: jest.fn(),
  onmessage: null,
}));

describe('Canvas Component', () => {
  const mockProps = {
    width: 800,
    height: 600,
    onImageChange: jest.fn(),
  };

  beforeEach(() => {
    // Mock canvas context methods
    const mockContext = {
      drawImage: jest.fn(),
      getImageData: jest.fn(() => ({
        data: new Uint8ClampedArray(800 * 600 * 4),
        width: 800,
        height: 600,
        colorSpace: 'srgb' as PredefinedColorSpace,
      })),
      putImageData: jest.fn(),
    } as unknown as CanvasRenderingContext2D;

    jest.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(mockContext);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders canvas with correct dimensions', () => {
    render(<Canvas {...mockProps} />);
    const canvas = screen.getByRole('img', { name: /canvas/i });

    expect(canvas).toBeInTheDocument();
    expect(canvas).toHaveAttribute('width', '800');
    expect(canvas).toHaveAttribute('height', '600');
  });

  it('handles image upload', async () => {
    render(<Canvas {...mockProps} />);

    const file = new File(['test'], 'test.png', { type: 'image/png' });
    const input = screen.getByLabelText(/upload image/i);

    await act(async () => {
      fireEvent.change(input, { target: { files: [file] } });
    });

    expect(mockProps.onImageChange).toHaveBeenCalled();
  });

  it('applies brightness adjustment', async () => {
    render(<Canvas {...mockProps} />);

    const brightnessSlider = screen.getByLabelText(/brightness/i);

    await act(async () => {
      fireEvent.change(brightnessSlider, { target: { value: '50' } });
    });

    // Verify worker message was sent
    expect(Worker.prototype.postMessage).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'transform',
        params: {
          transformType: 'brightness',
          value: 50,
        },
      })
    );
  });

  it('applies filters', async () => {
    render(<Canvas {...mockProps} />);

    const filterSelect = screen.getByLabelText(/filter/i);

    await act(async () => {
      fireEvent.change(filterSelect, { target: { value: 'grayscale' } });
    });

    // Verify worker message was sent
    expect(Worker.prototype.postMessage).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'filter',
        params: {
          filterType: 'grayscale',
        },
      })
    );
  });

  it('computes histogram', async () => {
    render(<Canvas {...mockProps} />);

    const histogramButton = screen.getByText(/histogram/i);

    await act(async () => {
      fireEvent.click(histogramButton);
    });

    // Verify worker message was sent
    expect(Worker.prototype.postMessage).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'histogram',
      })
    );
  });

  it('handles worker responses', async () => {
    render(<Canvas {...mockProps} />);

    const mockWorkerResponse = {
      data: {
        success: true,
        result: {
          data: new Uint8ClampedArray(800 * 600 * 4),
          width: 800,
          height: 600,
          colorSpace: 'srgb' as PredefinedColorSpace,
        },
      },
    };

    await act(async () => {
      // Simulate worker response
      const worker = new Worker('');
      worker.onmessage?.(mockWorkerResponse as unknown as MessageEvent);
    });

    // Verify image was updated
    expect(mockProps.onImageChange).toHaveBeenCalled();
  });

  it('handles worker errors', async () => {
    render(<Canvas {...mockProps} />);

    const mockWorkerError = {
      data: {
        success: false,
        error: 'Test error',
      },
    };

    await act(async () => {
      // Simulate worker error
      const worker = new Worker('');
      worker.onmessage?.(mockWorkerError as unknown as MessageEvent);
    });

    // Verify error is displayed
    expect(screen.getByText(/test error/i)).toBeInTheDocument();
  });
});
