type ImageOperation = 'histogram' | 'transform' | 'filter';
type FilterType = 'grayscale' | 'sepia' | 'invert';
type TransformType = 'brightness' | 'contrast' | 'saturation';

interface ImageDataLike {
  data: Uint8ClampedArray;
  width: number;
  height: number;
  colorSpace: PredefinedColorSpace;
}

interface WorkerMessage {
  type: ImageOperation;
  data: ImageDataLike;
  params?: {
    filterType?: FilterType;
    transformType?: TransformType;
    value?: number;
  };
}

function transformImage(
  imageData: ImageDataLike,
  type: TransformType,
  value: number
): ImageDataLike {
  if (!imageData?.data || !imageData.width || !imageData.height) {
    throw new Error('Invalid image data');
  }

  const data = new Uint8ClampedArray(imageData.data);

  switch (type) {
    case 'brightness':
      for (let i = 0; i < data.length; i += 4) {
        data[i] = Math.min(255, Math.max(0, data[i] + value)); // Red
        data[i + 1] = Math.min(255, Math.max(0, data[i + 1] + value)); // Green
        data[i + 2] = Math.min(255, Math.max(0, data[i + 2] + value)); // Blue
      }
      break;

    case 'contrast':
      const factor = (259 * (value + 255)) / (255 * (259 - value));
      for (let i = 0; i < data.length; i += 4) {
        data[i] = Math.min(255, Math.max(0, factor * (data[i] - 128) + 128));
        data[i + 1] = Math.min(255, Math.max(0, factor * (data[i + 1] - 128) + 128));
        data[i + 2] = Math.min(255, Math.max(0, factor * (data[i + 2] - 128) + 128));
      }
      break;

    case 'saturation':
      for (let i = 0; i < data.length; i += 4) {
        const gray = 0.2989 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
        data[i] = Math.min(255, Math.max(0, gray + value * (data[i] - gray)));
        data[i + 1] = Math.min(255, Math.max(0, gray + value * (data[i + 1] - gray)));
        data[i + 2] = Math.min(255, Math.max(0, gray + value * (data[i + 2] - gray)));
      }
      break;

    default:
      throw new Error(`Unsupported transform type: ${type}`);
  }

  return {
    data,
    width: imageData.width,
    height: imageData.height,
    colorSpace: imageData.colorSpace,
  };
}

function applyFilter(imageData: ImageDataLike, type: FilterType): ImageDataLike {
  if (!imageData?.data || !imageData.width || !imageData.height) {
    throw new Error('Invalid image data');
  }

  const data = new Uint8ClampedArray(imageData.data);

  switch (type) {
    case 'grayscale':
      for (let i = 0; i < data.length; i += 4) {
        const gray = 0.2989 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
        data[i] = data[i + 1] = data[i + 2] = gray;
      }
      break;

    case 'sepia':
      for (let i = 0; i < data.length; i += 4) {
        const r = data[i],
          g = data[i + 1],
          b = data[i + 2];
        data[i] = Math.min(255, r * 0.393 + g * 0.769 + b * 0.189);
        data[i + 1] = Math.min(255, r * 0.349 + g * 0.686 + b * 0.168);
        data[i + 2] = Math.min(255, r * 0.272 + g * 0.534 + b * 0.131);
      }
      break;

    case 'invert':
      for (let i = 0; i < data.length; i += 4) {
        data[i] = 255 - data[i];
        data[i + 1] = 255 - data[i + 1];
        data[i + 2] = 255 - data[i + 2];
      }
      break;

    default:
      throw new Error(`Unsupported filter type: ${type}`);
  }

  return {
    data,
    width: imageData.width,
    height: imageData.height,
    colorSpace: imageData.colorSpace,
  };
}

function computeHistogram(imageData: ImageDataLike) {
  if (!imageData?.data || !imageData.width || !imageData.height) {
    return {
      red: new Array(256).fill(0),
      green: new Array(256).fill(0),
      blue: new Array(256).fill(0),
    };
  }

  const red = new Array(256).fill(0);
  const green = new Array(256).fill(0);
  const blue = new Array(256).fill(0);

  for (let i = 0; i < imageData.data.length; i += 4) {
    red[imageData.data[i]]++;
    green[imageData.data[i + 1]]++;
    blue[imageData.data[i + 2]]++;
  }

  return { red, green, blue };
}

function createImageData(data: Uint8ClampedArray, width: number, height: number): ImageDataLike {
  return {
    data,
    width,
    height,
    colorSpace: 'srgb',
  };
}

// Message handler with improved type safety and error handling
self.onmessage = (e: MessageEvent<WorkerMessage>) => {
  try {
    const { type, data, params } = e.data;
    let result;

    switch (type) {
      case 'transform':
        if (!params?.transformType || typeof params.value !== 'number') {
          throw new Error('Missing transform parameters');
        }
        result = transformImage(data, params.transformType, params.value);
        break;

      case 'filter':
        if (!params?.filterType) {
          throw new Error('Missing filter type');
        }
        result = applyFilter(data, params.filterType);
        break;

      case 'histogram':
        result = computeHistogram(data);
        break;

      default:
        throw new Error(`Unknown operation type: ${type}`);
    }

    self.postMessage({ success: true, result });
  } catch (error) {
    self.postMessage({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    });
  }
};
