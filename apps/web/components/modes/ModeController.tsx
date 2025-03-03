"use client"

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { 
  Edit, Mail, BarChart, Users, 
  CheckCircle, AlertCircle, X
} from 'lucide-react';

// Types
export type OperationalMode = 'content' | 'campaign' | 'analytics' | 'audience';

interface ModeOption {
  id: OperationalMode;
  label: string;
  icon: React.ReactNode;
  color: string;
  description: string;
  available: boolean;
}

interface ModeControllerProps {
  className?: string;
  activeMode?: OperationalMode;
  onModeChange?: (mode: OperationalMode) => void;
  showDialog?: boolean;
  onDialogClose?: () => void;
}

export function ModeController({
  className,
  activeMode = 'content',
  onModeChange,
  showDialog = false,
  onDialogClose,
}: ModeControllerProps) {
  const [selectedMode, setSelectedMode] = useState<OperationalMode>(activeMode);
  
  // Mode options
  const modeOptions: ModeOption[] = [
    {
      id: 'content',
      label: 'Content Creation',
      icon: <Edit className="w-5 h-5" />,
      color: 'bg-blue-100 text-blue-600 border-blue-200',
      description: 'Design and edit email content with AI assistance',
      available: true,
    },
    {
      id: 'campaign',
      label: 'Campaign Flow',
      icon: <Mail className="w-5 h-5" />,
      color: 'bg-purple-100 text-purple-600 border-purple-200',
      description: 'Set up drip campaigns and automation sequences',
      available: true,
    },
    {
      id: 'analytics',
      label: 'Analytics',
      icon: <BarChart className="w-5 h-5" />,
      color: 'bg-green-100 text-green-600 border-green-200',
      description: 'View performance metrics and AI-generated insights',
      available: true,
    },
    {
      id: 'audience',
      label: 'Audience',
      icon: <Users className="w-5 h-5" />,
      color: 'bg-orange-100 text-orange-600 border-orange-200',
      description: 'Manage segments and recipient profiles',
      available: false,
    },
  ];
  
  // Handle mode selection
  const handleModeSelect = (mode: OperationalMode) => {
    const option = modeOptions.find(opt => opt.id === mode);
    
    if (option && option.available) {
      setSelectedMode(mode);
    }
  };
  
  // Handle confirm mode change
  const handleConfirmModeChange = () => {
    onModeChange?.(selectedMode);
    onDialogClose?.();
  };
  
  // Handle dialog close
  const handleDialogClose = () => {
    setSelectedMode(activeMode);
    onDialogClose?.();
  };

  if (!showDialog) {
    return null;
  }

  return (
    <div className={cn("fixed inset-0 bg-black/50 flex items-center justify-center z-50", className)}>
      <div className="bg-card rounded-lg shadow-lg w-full max-w-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h2 className="text-xl font-semibold">Switch Operational Mode</h2>
          <button 
            className="p-1 rounded-full hover:bg-muted"
            onClick={handleDialogClose}
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {/* Content */}
        <div className="p-6">
          <p className="text-muted-foreground mb-4">
            Select an operational mode to switch the interface context. Your current work will be saved automatically.
          </p>
          
          <div className="grid grid-cols-2 gap-4 mb-6">
            {modeOptions.map(mode => (
              <div 
                key={mode.id}
                className={cn(
                  "border rounded-lg p-4 cursor-pointer transition-all",
                  mode.available 
                    ? selectedMode === mode.id
                      ? `${mode.color} border-2`
                      : "hover:border-primary/30"
                    : "opacity-50 cursor-not-allowed"
                )}
                onClick={() => mode.available && handleModeSelect(mode.id)}
              >
                <div className="flex items-center mb-2">
                  <div className={cn(
                    "w-8 h-8 rounded-full flex items-center justify-center mr-3",
                    mode.color.split(' ')[0],
                    mode.color.split(' ')[1]
                  )}>
                    {mode.icon}
                  </div>
                  <h3 className="font-medium">{mode.label}</h3>
                  
                  {selectedMode === mode.id && (
                    <CheckCircle className="w-5 h-5 ml-auto text-green-600" />
                  )}
                  
                  {!mode.available && (
                    <div className="ml-auto px-2 py-0.5 bg-muted text-muted-foreground rounded text-xs">
                      Coming Soon
                    </div>
                  )}
                </div>
                
                <p className="text-sm text-muted-foreground pl-11">
                  {mode.description}
                </p>
              </div>
            ))}
          </div>
          
          <div className="flex items-center">
            <AlertCircle className="w-4 h-4 text-amber-500 mr-2" />
            <p className="text-sm text-muted-foreground">
              Switching modes will change the available tools and interface layout.
            </p>
          </div>
        </div>
        
        {/* Footer */}
        <div className="flex items-center justify-end px-6 py-4 border-t border-border bg-muted/30">
          <button 
            className="px-4 py-2 rounded-md border border-border hover:bg-muted mr-2"
            onClick={handleDialogClose}
          >
            Cancel
          </button>
          
          <button 
            className="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90"
            onClick={handleConfirmModeChange}
          >
            Switch to {modeOptions.find(m => m.id === selectedMode)?.label}
          </button>
        </div>
      </div>
    </div>
  );
}
