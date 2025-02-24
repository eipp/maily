/**
 * @jest-environment node
 */

interface MockMessageEvent<T = unknown> {
  data: T;
  type: string;
  target: null;
  currentTarget: null;
  eventPhase: number;
  bubbles: boolean;
  cancelable: boolean;
  defaultPrevented: boolean;
  composed: boolean;
  timeStamp: number;
  srcElement: null;
  returnValue: boolean;
  stopPropagation: jest.Mock;
  stopImmediatePropagation: jest.Mock;
  preventDefault: jest.Mock;
  initEvent: jest.Mock;
  lastEventId: string;
  origin: string;
  ports: unknown[];
  source: null;
}

interface MockWorkerGlobal {
  postMessage: jest.Mock;
  onmessage?: (event: MockMessageEvent) => void;
}

interface MockGlobal {
  self?: MockWorkerGlobal;
}

describe('Canvas Worker', () => {
  let mockPostMessage: jest.Mock;

  beforeEach(() => {
    mockPostMessage = jest.fn();
    const mockGlobal = global as unknown as MockGlobal;
    mockGlobal.self = {
      postMessage: mockPostMessage,
    };
    jest.isolateModules(() => {
      require('../../workers/canvas.worker');
    });
  });

  afterEach(() => {
    jest.resetModules();
    const mockGlobal = global as unknown as MockGlobal;
    delete mockGlobal.self;
  });

  const createMockMessageEvent = <T>(data: T): MockMessageEvent<T> => ({
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
    stopPropagation: jest.fn(),
    stopImmediatePropagation: jest.fn(),
    preventDefault: jest.fn(),
    initEvent: jest.fn(),
    lastEventId: '',
    origin: '',
    ports: [],
    source: null,
  });

  const createImageData = (width: number, height: number) => ({
    data: new Uint8ClampedArray(width * height * 4),
    width,
    height,
    colorSpace: 'srgb' as PredefinedColorSpace,
  });

  it('should handle brightness transform', () => {
    const imageData = createImageData(2, 2);
    const message = {
      type: 'transform',
      data: imageData,
      params: {
        transformType: 'brightness',
        value: 50,
      },
    };

    const mockGlobal = global as unknown as MockGlobal;
    mockGlobal.self?.onmessage?.(createMockMessageEvent(message));

    expect(mockPostMessage).toHaveBeenCalledWith(
      expect.objectContaining({
        success: true,
        result: expect.any(Object),
      })
    );
  });

  it('should handle grayscale filter', () => {
    const imageData = createImageData(2, 2);
    const message = {
      type: 'filter',
      data: imageData,
      params: {
        filterType: 'grayscale',
      },
    };

    const mockGlobal = global as unknown as MockGlobal;
    mockGlobal.self?.onmessage?.(createMockMessageEvent(message));

    expect(mockPostMessage).toHaveBeenCalledWith(
      expect.objectContaining({
        success: true,
        result: expect.any(Object),
      })
    );
  });

  it('should compute histogram', () => {
    const imageData = createImageData(2, 2);
    const message = {
      type: 'histogram',
      data: imageData,
    };

    const mockGlobal = global as unknown as MockGlobal;
    mockGlobal.self?.onmessage?.(createMockMessageEvent(message));

    expect(mockPostMessage).toHaveBeenCalledWith(
      expect.objectContaining({
        success: true,
        result: expect.objectContaining({
          red: expect.any(Array),
          green: expect.any(Array),
          blue: expect.any(Array),
        }),
      })
    );
  });

  it('should handle errors gracefully', () => {
    const message = {
      type: 'unknown' as const,
      data: createImageData(2, 2),
    };

    const mockGlobal = global as unknown as MockGlobal;
    mockGlobal.self?.onmessage?.(createMockMessageEvent(message));

    expect(mockPostMessage).toHaveBeenCalledWith(
      expect.objectContaining({
        success: false,
        error: expect.any(String),
      })
    );
  });
});
