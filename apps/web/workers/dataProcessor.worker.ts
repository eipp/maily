const ctx: Worker = self as any;

interface ProcessMessage {
  type: 'process';
  data: any[];
  chunkSize: number;
  transform?: string;
}

interface ProgressMessage {
  type: 'progress';
  chunk: any[];
}

interface CompleteMessage {
  type: 'complete';
}

interface ErrorMessage {
  type: 'error';
  error: Error;
}

function processChunk(chunk: any[], transform?: string): any[] {
  if (!Array.isArray(chunk)) {
    throw new Error('Invalid data type: input must be an array');
  }

  switch (transform) {
    case 'double':
      return chunk.map(item => {
        if (typeof item !== 'number') {
          throw new Error('Invalid data type: items must be numbers for double transformation');
        }
        return item * 2;
      });
    default:
      return chunk;
  }
}

ctx.onmessage = (event: MessageEvent<ProcessMessage>) => {
  const { data, chunkSize, transform } = event.data;

  try {
    // Validate input
    if (!Array.isArray(data)) {
      throw new Error('Invalid data type: input must be an array');
    }

    // Process data in chunks
    for (let i = 0; i < data.length; i += chunkSize) {
      const chunk = data.slice(i, i + chunkSize);
      const processedChunk = processChunk(chunk, transform);

      // Send progress update
      ctx.postMessage({
        type: 'progress',
        chunk: processedChunk,
      } as ProgressMessage);
    }

    // Signal completion
    ctx.postMessage({
      type: 'complete',
    } as CompleteMessage);
  } catch (error) {
    // Handle errors
    ctx.postMessage({
      type: 'error',
      error: error instanceof Error ? error : new Error('Unknown error occurred'),
    } as ErrorMessage);
  }
};

export type { ProcessMessage, ProgressMessage, CompleteMessage, ErrorMessage };
