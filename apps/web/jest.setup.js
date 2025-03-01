import '@testing-library/jest-dom';
import 'jest-canvas-mock';

// Mock window object
const mockWindow = {
  matchMedia: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
  performance: {
    getEntriesByType: jest.fn(),
    getEntriesByName: jest.fn(),
    now: jest.fn(),
    mark: jest.fn(),
    measure: jest.fn(),
    clearMarks: jest.fn(),
    clearMeasures: jest.fn(),
  },
  requestAnimationFrame: jest.fn(cb => {
    cb(performance.now());
    return 1;
  }),
  cancelAnimationFrame: jest.fn(),
  URL: {
    createObjectURL: jest.fn(),
    revokeObjectURL: jest.fn(),
  },
  IntersectionObserver: class {
    constructor(callback) {
      this.callback = callback;
    }
    observe = jest.fn();
    unobserve = jest.fn();
    disconnect = jest.fn();
  },
  ResizeObserver: class {
    constructor(callback) {
      this.callback = callback;
    }
    observe = jest.fn();
    unobserve = jest.fn();
    disconnect = jest.fn();
  },
  PerformanceObserver: class {
    constructor(callback) {
      this.callback = callback;
    }
    observe = jest.fn();
    disconnect = jest.fn();
  },
};

// Apply mocks to global object
Object.defineProperty(global, 'window', {
  value: mockWindow,
  writable: true,
});

Object.defineProperty(global, 'document', {
  value: {
    ...global.document,
    createElement: jest.fn().mockImplementation(tag => {
      if (tag === 'canvas') {
        return {
          getContext: jest.fn().mockReturnValue({
            drawImage: jest.fn(),
            getImageData: jest.fn().mockReturnValue(new ImageData(1, 1)),
            putImageData: jest.fn(),
            clearRect: jest.fn(),
          }),
          toDataURL: jest.fn(),
          width: 0,
          height: 0,
        };
      }
      return {};
    }),
  },
  writable: true,
});

// Mock ImageData
global.ImageData = class {
  constructor(data, width, height) {
    this.data = new Uint8ClampedArray(data);
    this.width = width;
    this.height = height;
  }
};

// Mock Web Worker
global.Worker = class {
  constructor() {
    this.onmessage = null;
    this.postMessage = jest.fn();
    this.addEventListener = jest.fn();
    this.removeEventListener = jest.fn();
  }
};

// Mock self for Web Worker context
global.self = {
  postMessage: jest.fn(),
  onmessage: null,
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
};

// Mock fetch
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
    blob: () => Promise.resolve(new Blob()),
  })
);

// Mock console methods
const originalConsole = { ...console };
beforeAll(() => {
  global.console = {
    ...console,
    log: jest.fn(),
    error: jest.fn(),
    warn: jest.fn(),
    info: jest.fn(),
    debug: jest.fn(),
  };
});

afterAll(() => {
  global.console = originalConsole;
});

// Clean up after each test
afterEach(() => {
  jest.clearAllMocks();
});
