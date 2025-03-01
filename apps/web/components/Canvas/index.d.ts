import { ReactNode } from 'react'

// AiAssistantPanel component props
export interface AiAssistantPanelProps {
  contentSuggestions: any[];
  designSuggestions: any[];
  isGenerating: boolean;
  onRequestSuggestion: () => void;
  onApplySuggestion: (suggestion: any) => void;
  campaignId: string;
}

// AiAssistantPanel component
export const AiAssistantPanel: React.FC<AiAssistantPanelProps>;

// EmailCanvas component props
export interface EmailCanvasProps {
  campaignId: string;
  userId: string;
  initialContent?: any;
  readOnly?: boolean;
  onChange?: (content: any) => void;
  onExport?: (htmlContent: string) => void;
}

// EmailCanvas component
export const EmailCanvas: React.FC<EmailCanvasProps>;

// Exported card types from EmailCardRegistry
export const EmailCardRegistry: {
  registerShapes: (app: any) => void;
};
