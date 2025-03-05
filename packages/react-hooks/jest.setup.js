// Add any global test setup here
import '@testing-library/jest-dom';

// Mock localStorage
if (typeof window !== 'undefined') {
  Object.defineProperty(window, 'localStorage', {
    value: {
      getItem: jest.fn(),
      setItem: jest.fn(),
      removeItem: jest.fn(),
      clear: jest.fn(),
    },
    writable: true,
  });
}

// Mock fetch
global.fetch = jest.fn();

// Suppress console errors during tests
console.error = jest.fn();

// Reset mocks between tests
beforeEach(() => {
  jest.clearAllMocks();
}); 