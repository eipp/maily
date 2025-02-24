/**
 * @jest-environment node
 */

// Mock self for worker environment
const self = {
  postMessage: jest.fn(),
  onmessage: null as any
} as unknown as Worker;
(global as any).self = self;

// Import worker after mocking self
import '../../workers/canvas.worker';

describe('Canvas Worker', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const createImageData = (width: number, height: number, value = 100): ImageData => {
    const data = new Uint8ClampedArray(width * height * 4).fill(value);
    return { data, width, height } as ImageData;
  };

  const createMessageEvent = (data: any) => ({
    data,
    type: 'message',
    target: null,
    currentTarget: null,
    eventPhase: 0,
    bubbles: false,
    cancelable: false,
    defaultPrevented: false,
    composed: false,
    timeStamp: Date.now(),
    srcElement: null,
    returnValue: true,
    cancelBubble: false,
    path: [],
    preventDefault: jest.fn(),
    stopPropagation: jest.fn(),
    stopImmediatePropagation: jest.fn(),
    composedPath: jest.fn(() => []),
    initEvent: jest.fn(),
  });

  describe('transformImage', () => {
    it('handles brightness transformation', () => {
      const imageData = createImageData(2, 2);
      const message = {
        operation: 'transform',
        imageData,
        type: 'brightness',
        value: 120
      };

      self.onmessage(createMessageEvent(message));

      expect(self.postMessage).toHaveBeenCalledWith({
        result: expect.objectContaining({
          data: expect.any(Uint8ClampedArray),
          width: 2,
          height: 2
        }),
        error: null
      });
    });

    it('handles contrast transformation', () => {
      const imageData = createImageData(2, 2);
      const message = {
        operation: 'transform',
        imageData,
        type: 'contrast',
        value: 150
      };

      self.onmessage(createMessageEvent(message));

      expect(self.postMessage).toHaveBeenCalledWith({
        result: expect.objectContaining({
          data: expect.any(Uint8ClampedArray),
          width: 2,
          height: 2
        }),
        error: null
      });
    });

    it('handles saturation transformation', () => {
      const imageData = createImageData(2, 2);
      const message = {
        operation: 'transform',
        imageData,
        type: 'saturation',
        value: 80
      };

      self.onmessage(createMessageEvent(message));

      expect(self.postMessage).toHaveBeenCalledWith({
        result: expect.objectContaining({
          data: expect.any(Uint8ClampedArray),
          width: 2,
          height: 2
        }),
        error: null
      });
    });
  });

  describe('applyFilter', () => {
    it('applies grayscale filter', () => {
      const imageData = createImageData(2, 2);
      const message = {
        operation: 'filter',
        imageData,
        type: 'grayscale'
      };

      self.onmessage(createMessageEvent(message));

      expect(self.postMessage).toHaveBeenCalledWith({
        result: expect.objectContaining({
          data: expect.any(Uint8ClampedArray),
          width: 2,
          height: 2
        }),
        error: null
      });
    });

    it('applies sepia filter', () => {
      const imageData = createImageData(2, 2);
      const message = {
        operation: 'filter',
        imageData,
        type: 'sepia'
      };

      self.onmessage(createMessageEvent(message));

      expect(self.postMessage).toHaveBeenCalledWith({
        result: expect.objectContaining({
          data: expect.any(Uint8ClampedArray),
          width: 2,
          height: 2
        }),
        error: null
      });
    });

    it('applies invert filter', () => {
      const imageData = createImageData(2, 2);
      const message = {
        operation: 'filter',
        imageData,
        type: 'invert'
      };

      self.onmessage(createMessageEvent(message));

      expect(self.postMessage).toHaveBeenCalledWith({
        result: expect.objectContaining({
          data: expect.any(Uint8ClampedArray),
          width: 2,
          height: 2
        }),
        error: null
      });
    });
  });

  describe('computeHistogram', () => {
    it('computes histogram for valid image data', () => {
      const imageData = createImageData(2, 2);
      const message = {
        operation: 'histogram',
        imageData
      };

      self.onmessage(createMessageEvent(message));

      expect(self.postMessage).toHaveBeenCalledWith({
        result: expect.objectContaining({
          red: expect.any(Array),
          green: expect.any(Array),
          blue: expect.any(Array)
        }),
        error: null
      });
    });

    it('returns empty histograms for empty image data', () => {
      const imageData = { data: new Uint8ClampedArray(0), width: 0, height: 0 };
      const message = {
        operation: 'histogram',
        imageData
      };

      self.onmessage(createMessageEvent(message));

      expect(self.postMessage).toHaveBeenCalledWith({
        result: {
          red: new Array(256).fill(0),
          green: new Array(256).fill(0),
          blue: new Array(256).fill(0)
        },
        error: null
      });
    });
  });

  describe('error handling', () => {
    it('handles invalid operation type', () => {
      const message = {
        operation: 'invalid',
        imageData: createImageData(2, 2)
      };

      self.onmessage(createMessageEvent(message));

      expect(self.postMessage).toHaveBeenCalledWith({
        result: null,
        error: expect.stringContaining('Unknown operation')
      });
    });

    it('handles invalid image data', () => {
      const message = {
        operation: 'transform',
        imageData: null,
        type: 'brightness',
        value: 120
      };

      self.onmessage(createMessageEvent(message));

      expect(self.postMessage).toHaveBeenCalledWith({
        result: null,
        error: expect.stringContaining('Invalid image data')
      });
    });
  });
}); 