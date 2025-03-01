import { DataProcessorWorker } from '@/workers/dataProcessor.worker';

// Mock Worker and MessageChannel
class MockWorker {
  onmessage: ((e: MessageEvent) => void) | null = null;
  postMessage(data: any) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', { data }));
    }
  }
}

describe('DataProcessor Worker', () => {
  let worker: MockWorker;

  beforeEach(() => {
    // Setup mock worker
    worker = new MockWorker();
    (global as any).Worker = jest.fn().mockImplementation(() => worker);
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it('processes data in chunks', async () => {
    const testData = Array.from({ length: 1000 }, (_, i) => i);
    const processedData: number[] = [];

    // Create a promise that resolves when all data is processed
    const processingComplete = new Promise<void>(resolve => {
      worker.onmessage = (e: MessageEvent) => {
        if (e.data.type === 'progress') {
          processedData.push(...e.data.chunk);
        } else if (e.data.type === 'complete') {
          resolve();
        }
      };
    });

    // Start processing
    worker.postMessage({
      type: 'process',
      data: testData,
      chunkSize: 100,
    });

    await processingComplete;

    expect(processedData).toHaveLength(1000);
    expect(processedData[0]).toBe(0);
    expect(processedData[999]).toBe(999);
  });

  it('handles empty data array', async () => {
    const processingComplete = new Promise<void>(resolve => {
      worker.onmessage = (e: MessageEvent) => {
        if (e.data.type === 'complete') {
          resolve();
        }
      };
    });

    worker.postMessage({
      type: 'process',
      data: [],
      chunkSize: 100,
    });

    await processingComplete;
    // Test passes if promise resolves without error
  });

  it('processes data with custom transformation', async () => {
    const testData = [1, 2, 3, 4, 5];
    const processedData: number[] = [];

    const processingComplete = new Promise<void>(resolve => {
      worker.onmessage = (e: MessageEvent) => {
        if (e.data.type === 'progress') {
          processedData.push(...e.data.chunk);
        } else if (e.data.type === 'complete') {
          resolve();
        }
      };
    });

    worker.postMessage({
      type: 'process',
      data: testData,
      chunkSize: 2,
      transform: 'double', // Example transformation type
    });

    await processingComplete;

    expect(processedData).toEqual([2, 4, 6, 8, 10]);
  });

  it('handles errors gracefully', async () => {
    const testData = ['invalid', 'data', 'type'];
    let error: Error | null = null;

    const processingComplete = new Promise<void>(resolve => {
      worker.onmessage = (e: MessageEvent) => {
        if (e.data.type === 'error') {
          error = e.data.error;
          resolve();
        }
      };
    });

    worker.postMessage({
      type: 'process',
      data: testData,
      chunkSize: 1,
    });

    await processingComplete;

    expect(error).toBeTruthy();
    expect(error?.message).toContain('Invalid data type');
  });
});
