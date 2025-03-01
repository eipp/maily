import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { apiClient } from '@/lib/api'

/**
 * Types for the email canvas store
 */
export interface Suggestion {
  id: string;
  type: 'content' | 'design';
  content: string;
  preview?: string;
  position?: [number, number];
  changes?: any[];
}

export interface AiRequestParams {
  canvasState: any;
  contentText?: string;
  campaignId: string;
  shapes?: number;
  suggestionType: 'content' | 'design';
}

interface EmailCanvasState {
  // Suggestions from AI
  aiSuggestions: Suggestion[];
  designSuggestions: Suggestion[];
  isGenerating: boolean;

  // Actions
  requestAiSuggestion: (params: AiRequestParams) => Promise<void>;
  applyAiSuggestion: (suggestion: Suggestion) => void;
  clearSuggestions: () => void;

  // Canvas history
  canvasHistory: any[];
  currentHistoryIndex: number;
  pushToHistory: (state: any) => void;
  undo: () => any | null;
  redo: () => any | null;

  // Stats and metadata
  stats: {
    suggestionsApplied: number;
    suggestionsRequested: number;
    lastSuggestionTime: string | null;
  };
}

/**
 * Create a store for email canvas with AI assistance
 */
export const useEmailCanvasStore = create<EmailCanvasState>()(
  persist(
    (set, get) => ({
      // Initial state
      aiSuggestions: [],
      designSuggestions: [],
      isGenerating: false,
      canvasHistory: [],
      currentHistoryIndex: -1,
      stats: {
        suggestionsApplied: 0,
        suggestionsRequested: 0,
        lastSuggestionTime: null
      },

      /**
       * Request AI suggestions for the canvas
       */
      requestAiSuggestion: async (params: AiRequestParams) => {
        // Skip if already generating
        if (get().isGenerating) return;

        // Start generating
        set({ isGenerating: true });

        try {
          // Determine API endpoint based on suggestion type
          const endpoint = params.suggestionType === 'content'
            ? '/api/ai/canvas/content-suggestions'
            : '/api/ai/canvas/design-suggestions';

          // Make API request
          const response = await apiClient.post(endpoint, {
            campaignId: params.campaignId,
            canvasState: params.canvasState,
            contentText: params.contentText,
            shapesCount: params.shapes || 0
          });

          if (response.data?.success) {
            const suggestions = response.data.suggestions || [];

            // Update the appropriate suggestions list
            if (params.suggestionType === 'content') {
              set({ aiSuggestions: suggestions });
            } else {
              set({ designSuggestions: suggestions });
            }

            // Update stats
            set(state => ({
              stats: {
                ...state.stats,
                suggestionsRequested: state.stats.suggestionsRequested + 1,
                lastSuggestionTime: new Date().toISOString()
              }
            }));
          }
        } catch (error) {
          console.error('Failed to get AI suggestions:', error);
        } finally {
          // End generating state
          set({ isGenerating: false });
        }
      },

      /**
       * Apply an AI suggestion to the canvas
       */
      applyAiSuggestion: (suggestion: Suggestion) => {
        // Update stats when a suggestion is applied
        set(state => ({
          stats: {
            ...state.stats,
            suggestionsApplied: state.stats.suggestionsApplied + 1
          }
        }));

        // NOTE: The actual application of the suggestion to the canvas
        // happens in the EmailCanvas component, this just tracks metrics
      },

      /**
       * Clear all suggestions
       */
      clearSuggestions: () => {
        set({
          aiSuggestions: [],
          designSuggestions: []
        });
      },

      /**
       * Push canvas state to history for undo/redo
       */
      pushToHistory: (state: any) => {
        const { canvasHistory, currentHistoryIndex } = get();

        // Create new history array with states up to current index
        const newHistory = canvasHistory.slice(0, currentHistoryIndex + 1);

        // Add the new state
        newHistory.push(state);

        // Limit history size to prevent memory issues
        const limitedHistory = newHistory.slice(-50);

        // Update state
        set({
          canvasHistory: limitedHistory,
          currentHistoryIndex: limitedHistory.length - 1
        });
      },

      /**
       * Undo the last canvas change
       */
      undo: () => {
        const { canvasHistory, currentHistoryIndex } = get();

        // Return null if no history or at beginning
        if (canvasHistory.length === 0 || currentHistoryIndex <= 0) {
          return null;
        }

        // Get the previous state
        const newIndex = currentHistoryIndex - 1;
        const previousState = canvasHistory[newIndex];

        // Update index
        set({ currentHistoryIndex: newIndex });

        return previousState;
      },

      /**
       * Redo a previously undone canvas change
       */
      redo: () => {
        const { canvasHistory, currentHistoryIndex } = get();

        // Return null if no history or at most recent
        if (
          canvasHistory.length === 0 ||
          currentHistoryIndex >= canvasHistory.length - 1
        ) {
          return null;
        }

        // Get the next state
        const newIndex = currentHistoryIndex + 1;
        const nextState = canvasHistory[newIndex];

        // Update index
        set({ currentHistoryIndex: newIndex });

        return nextState;
      }
    }),
    {
      name: 'maily-email-canvas', // localStorage key
      partialize: state => ({
        // Only persist these parts of the state
        stats: state.stats
      })
    }
  )
);
