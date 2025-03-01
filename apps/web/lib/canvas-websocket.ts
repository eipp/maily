// This file is now a wrapper around the optimized-yjs implementation
// It maintains the same API for backward compatibility

import { OptimizedYjsProvider } from './optimized-yjs';

// Re-export the optimized implementation with the original name
export * from './optimized-yjs';

// For backward compatibility
export default OptimizedYjsProvider;
