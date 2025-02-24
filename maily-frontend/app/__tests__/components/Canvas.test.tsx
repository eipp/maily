import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import Canvas from '../../components/Canvas';
import React from 'react';

// Mock the worker
const mockWorker = {
  postMessage: jest.fn(),
  terminate: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn()
};

// Mock the performance monitoring hook
jest.mock('../../utils/performance', () => ({
  usePerformanceMonitoring: () => ({
    measureApiCall: (fn: () => Promise<any>) => fn()
  })
}));

// Mock the canvas worker hook
jest.mock('../../hooks/useCanvasWorker', () => ({
  useCanvasWorker: () => ({
    transformImage: jest.fn().mockResolvedValue({ data: new Uint8ClampedArray(4), width: 1, height: 1 }),
    applyFilter: jest.fn().mockResolvedValue({ data: new Uint8ClampedArray(4), width: 1, height: 1 }),
    computeHistogram: jest.fn().mockResolvedValue({
      red: new Array(256).fill(0),
      green: new Array(256).fill(0),
      blue: new Array(256).fill(0)
    })
  })
}));

// Mock the canvas context
const mockContext = {
  getImageData: jest.fn().mockReturnValue({ data: new Uint8ClampedArray(4), width: 1, height: 1 }),
  putImageData: jest.fn(),
  clearRect: jest.fn(),
  drawImage: jest.fn()
};

describe('Canvas Component', () => {
  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks();
    
    // Mock canvas context
    HTMLCanvasElement.prototype.getContext = jest.fn().mockReturnValue(mockContext);
    
    // Mock window.Worker
    global.Worker = jest.fn().mockImplementation(() => mockWorker);
    
    // Mock requestAnimationFrame
    jest.spyOn(window, 'requestAnimationFrame').mockImplementation(cb => {
      cb(0);
      return 0;
    });
  });

  it('renders canvas element with correct dimensions', () => {
    const { container } = render(<Canvas width={800} height={600} />);
    const canvas = container.querySelector('canvas');
    
    expect(canvas).toBeInTheDocument();
    expect(canvas).toHaveAttribute('width', '800');
    expect(canvas).toHaveAttribute('height', '600');
  });

  it('renders control buttons', () => {
    render(<Canvas />);
    
    expect(screen.getByText('Increase Brightness')).toBeInTheDocument();
    expect(screen.getByText('Grayscale')).toBeInTheDocument();
    expect(screen.getByText('Compute Histogram')).toBeInTheDocument();
  });

  it('handles brightness adjustment', async () => {
    const { container } = render(<Canvas />);
    
    fireEvent.click(screen.getByText('Increase Brightness'));
    
    await waitFor(() => {
      expect(mockContext.putImageData).toHaveBeenCalled();
    });
  });

  it('handles filter application', async () => {
    const { container } = render(<Canvas />);
    
    fireEvent.click(screen.getByText('Grayscale'));
    
    await waitFor(() => {
      expect(mockContext.putImageData).toHaveBeenCalled();
    });
  });

  it('handles histogram computation', async () => {
    const consoleSpy = jest.spyOn(console, 'log');
    
    render(<Canvas />);
    fireEvent.click(screen.getByText('Compute Histogram'));
    
    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(
        'Histogram data:',
        expect.objectContaining({
          red: expect.any(Array),
          green: expect.any(Array),
          blue: expect.any(Array)
        })
      );
    });
  });

  it('handles errors gracefully', async () => {
    const consoleSpy = jest.spyOn(console, 'error');
    
    // Mock an error in the worker
    jest.mock('../../hooks/useCanvasWorker', () => ({
      useCanvasWorker: () => ({
        transformImage: jest.fn().mockRejectedValue(new Error('Test error')),
        applyFilter: jest.fn().mockRejectedValue(new Error('Test error')),
        computeHistogram: jest.fn().mockRejectedValue(new Error('Test error'))
      })
    }), { virtual: true });
    
    render(<Canvas />);
    
    fireEvent.click(screen.getByText('Increase Brightness'));
    
    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(
        'Error adjusting brightness:',
        expect.any(Error)
      );
    });
  });
}); 