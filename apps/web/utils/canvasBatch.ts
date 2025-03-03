'use client';

/**
 * Utility for batching canvas rendering operations
 * Ensures updates are efficiently processed in a single animation frame
 */
class CanvasBatchRenderer {
  private updateQueue: Map<string, () => void> = new Map();
  private isRenderScheduled = false;
  private renderCallbacks: Set<() => void> = new Set();
  
  /**
   * Queue an update operation for batch processing
   * @param id Unique identifier for the operation (used for deduplication)
   * @param updateFn Function to execute when rendering
   */
  queueUpdate(id: string, updateFn: () => void): void {
    // Store update function, overwriting previous updates with same ID
    this.updateQueue.set(id, updateFn);
    
    // Schedule a render if not already scheduled
    if (!this.isRenderScheduled) {
      this.scheduleRender();
    }
  }
  
  /**
   * Register a callback to be called after rendering
   * @param callback Function to call after rendering is complete
   * @returns Function to unregister the callback
   */
  onAfterRender(callback: () => void): () => void {
    this.renderCallbacks.add(callback);
    
    // Return unsubscribe function
    return () => {
      this.renderCallbacks.delete(callback);
    };
  }
  
  /**
   * Schedule a render on the next animation frame
   */
  private scheduleRender(): void {
    if (typeof window !== 'undefined') {
      this.isRenderScheduled = true;
      requestAnimationFrame(() => this.processQueue());
    }
  }
  
  /**
   * Process all queued updates in a single batch
   */
  private processQueue(): void {
    // Execute all updates
    const startTime = performance.now();
    
    // Get all unique update functions
    const updates = Array.from(this.updateQueue.values());
    
    // Clear the queue before executing updates
    // (in case updates queue more updates)
    this.updateQueue.clear();
    this.isRenderScheduled = false;
    
    // Execute all updates
    for (const update of updates) {
      update();
    }
    
    // Call render callbacks
    for (const callback of this.renderCallbacks) {
      callback();
    }
    
    // Log performance if it took more than 16ms (1 frame at 60fps)
    const duration = performance.now() - startTime;
    if (duration > 16) {
      console.debug(`Canvas batch render took ${duration.toFixed(2)}ms for ${updates.length} updates`);
    }
  }
  
  /**
   * Flush all queued updates immediately
   */
  flushUpdates(): void {
    if (this.updateQueue.size > 0) {
      this.processQueue();
    }
  }
}

// Singleton instance
export const canvasBatch = new CanvasBatchRenderer();