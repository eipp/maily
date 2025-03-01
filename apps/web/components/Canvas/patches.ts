/**
 * tldraw Optimization Patches
 *
 * This module provides optimizations and patches for the tldraw library
 * to improve performance with large documents and real-time collaboration.
 */

// Types to match tldraw's internal structure
interface TLDrawState {
  selectedIds: string[];
  shapes: Record<string, any>;
  bindings: Record<string, any>;
  assets: Record<string, any>;
  [key: string]: any;
}

interface TLDrawEditor {
  state: TLDrawState;
  updateState: (partialState: Partial<TLDrawState>) => void;
  selectTool: (tool: string) => void;
  [key: string]: any;
}

interface TLDrawPatch {
  description: string;
  applyPatch: (editor: TLDrawEditor) => void;
}

/**
 * Performance patches for tldraw
 */
export const tldrawPatches: TLDrawPatch[] = [
  // Large document performance optimization
  {
    description: "Optimize selection for large documents",
    applyPatch: (editor: TLDrawEditor) => {
      // Store the original selection method reference
      const originalSelect = editor.select;

      // Replace with optimized version
      editor.select = function (ids: string[], options?: any) {
        // For large selections, use a more efficient approach
        if (ids.length > 100) {
          // Update state directly instead of individual selections
          const currentSelection = new Set(editor.state.selectedIds);
          const newSelection = new Set(ids);

          // Only update if there's an actual change
          if (
            currentSelection.size !== newSelection.size ||
            ![...currentSelection].every(id => newSelection.has(id))
          ) {
            editor.updateState({ selectedIds: ids });
          }

          return this;
        }

        // For small selections, use the original method
        return originalSelect.call(this, ids, options);
      };
    }
  },

  // Rendering optimization
  {
    description: "Optimize rendering for large documents",
    applyPatch: (editor: TLDrawEditor) => {
      if (!editor.renderer) return;

      // Patch render method to use request animation frame
      const originalRender = editor.renderer.render;
      let renderPending = false;

      editor.renderer.render = function () {
        if (renderPending) return;

        renderPending = true;
        requestAnimationFrame(() => {
          originalRender.call(this);
          renderPending = false;
        });
      };
    }
  },

  // History optimization for large operations
  {
    description: "Optimize history for large operations",
    applyPatch: (editor: TLDrawEditor) => {
      if (!editor.history) return;

      // Intercept batch operations to optimize history recording
      const originalStartBatch = editor.history.start;
      const originalEndBatch = editor.history.stop;

      editor.history.start = function (reason: string) {
        // Check if this is a large batch operation
        const isLargeOperation =
          reason?.includes('bulk') ||
          reason?.includes('import') ||
          Object.keys(editor.state.shapes).length > 1000;

        if (isLargeOperation) {
          // Disable or optimize history for large operations
          this._previousHistoryEnabled = this.enabled;
          this.enabled = false;
        }

        return originalStartBatch.call(this, reason);
      };

      editor.history.stop = function (reason: string) {
        const result = originalEndBatch.call(this, reason);

        // Restore history setting
        if (this._previousHistoryEnabled !== undefined) {
          this.enabled = this._previousHistoryEnabled;
          delete this._previousHistoryEnabled;
        }

        return result;
      };
    }
  },

  // Shape cache optimization
  {
    description: "Optimize shape caching",
    applyPatch: (editor: TLDrawEditor) => {
      // Add LRU cache for shape geometry calculations
      const CACHE_SIZE = 1000;
      const cache = new Map<string, any>();
      const cacheQueue: string[] = [];

      // Patch the getShapeGeometry method if available
      if (editor.getShapeGeometry) {
        const originalGetShapeGeometry = editor.getShapeGeometry;

        editor.getShapeGeometry = function (shape: any) {
          const cacheKey = `${shape.id}:${shape.version || '0'}`;

          // Check if cached
          if (cache.has(cacheKey)) {
            // Move to end of queue (recently used)
            const idx = cacheQueue.indexOf(cacheKey);
            if (idx >= 0) {
              cacheQueue.splice(idx, 1);
            }
            cacheQueue.push(cacheKey);

            return cache.get(cacheKey);
          }

          // Not cached, calculate geometry
          const geometry = originalGetShapeGeometry.call(this, shape);

          // Cache the result
          cache.set(cacheKey, geometry);
          cacheQueue.push(cacheKey);

          // Maintain cache size limit
          if (cacheQueue.length > CACHE_SIZE) {
            const oldestKey = cacheQueue.shift();
            if (oldestKey) {
              cache.delete(oldestKey);
            }
          }

          return geometry;
        };
      }
    }
  },

  // Yjs collaboration optimization
  {
    description: "Optimize Yjs collaboration",
    applyPatch: (editor: TLDrawEditor) => {
      if (!editor.store || !editor.store.yDoc) return;

      // Optimize Yjs update handling
      const doc = editor.store.yDoc;

      // Batch updates when possible
      let updatesPending = false;
      let updateTimeout: any = null;

      const originalApplyUpdate = doc.applyUpdate;

      doc.applyUpdate = function (update: Uint8Array) {
        // For single updates, just apply directly
        if (!updatesPending) {
          updatesPending = true;

          // Schedule batch processing
          updateTimeout = setTimeout(() => {
            originalApplyUpdate.call(this, update);
            updatesPending = false;
          }, 0);

          return;
        }

        // Cancel pending update and apply both
        clearTimeout(updateTimeout);
        originalApplyUpdate.call(this, update);
        updatesPending = false;
      };
    }
  }
];

/**
 * Apply all performance patches to a tldraw editor instance
 */
export function applyPerformancePatches(editor: any): void {
  console.log("Applying tldraw performance patches...");

  tldrawPatches.forEach(patch => {
    try {
      patch.applyPatch(editor);
      console.log(`Applied patch: ${patch.description}`);
    } catch (error) {
      console.error(`Failed to apply patch "${patch.description}":`, error);
    }
  });
}
