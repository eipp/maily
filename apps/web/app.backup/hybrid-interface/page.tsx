"use client"

import React, { useState } from 'react';
import { useMode, useUI, useFeatureFlags } from '@/lib/providers';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { CanvasWorkspace } from '@/components/canvas/CanvasWorkspace';
import { AgentHub, AgentType } from '@/components/ai-mesh/AgentHub';
import { ReasoningPanel } from '@/components/ai-mesh/ReasoningPanel';
import { ModeController } from '@/components/modes/ModeController';

export default function HybridInterfacePage() {
  // Get state from context
  const { mode, setMode } = useMode();
  const { isReasoningPanelOpen, setReasoningPanelOpen, isAnalyticsPanelOpen, setAnalyticsPanelOpen } = useUI();
  const { aiMesh } = useFeatureFlags();
  
  // Local state
  const [activeAgent, setActiveAgent] = useState<AgentType>('content');
  const [showModeDialog, setShowModeDialog] = useState(false);
  const [isAgentHubCollapsed, setIsAgentHubCollapsed] = useState(false);
  
  // Sample metrics data
  const metricsData = {
    opens: 1245,
    clicks: 387,
    conversions: 52,
    unsubscribes: 8,
  };
  
  // Sample insights data
  const insightsData = [
    {
      id: 'insight-1',
      title: 'Open rate above industry average',
      description: 'Your open rate of 24.9% is 5.3% higher than the industry average for health products.',
      priority: 'medium' as const,
      actionable: true,
      action: 'View detailed breakdown',
    },
    {
      id: 'insight-2',
      title: 'Click-through rate declining',
      description: 'Your CTR has decreased by 2.1% compared to your previous campaign.',
      priority: 'high' as const,
      actionable: true,
      action: 'See optimization tips',
    },
    {
      id: 'insight-3',
      title: 'Mobile engagement increasing',
      description: 'Mobile opens have increased by 8.7% in the last 3 campaigns.',
      priority: 'low' as const,
      actionable: false,
    },
  ];
  
  // Sample active users
  const activeUsers = [
    {
      id: 'user-1',
      name: 'John Doe',
      status: 'online' as const,
    },
    {
      id: 'user-2',
      name: 'Jane Smith',
      status: 'online' as const,
    },
  ];
  
  // Handle mode change
  const handleModeChange = (newMode: typeof mode) => {
    setMode(newMode);
    setShowModeDialog(false);
  };
  
  // Handle agent selection
  const handleAgentSelect = (agentId: AgentType) => {
    setActiveAgent(agentId);
  };
  
  // Handle agent hub collapse toggle
  const toggleAgentHub = () => {
    setIsAgentHubCollapsed(!isAgentHubCollapsed);
  };
  
  // Handle reasoning panel collapse toggle
  const toggleReasoningPanel = () => {
    setReasoningPanelOpen(!isReasoningPanelOpen);
  };
  
  // Handle analytics panel collapse toggle
  const toggleAnalyticsPanel = () => {
    setAnalyticsPanelOpen(!isAnalyticsPanelOpen);
  };
  
  // Handle mode dialog toggle
  const toggleModeDialog = () => {
    setShowModeDialog(!showModeDialog);
  };
  
  // Get agent color based on active agent
  const getAgentColor = (): string => {
    switch (activeAgent) {
      case 'content':
        return 'rgb(239, 68, 68)'; // red
      case 'design':
        return 'rgb(168, 85, 247)'; // violet
      case 'analytics':
        return 'rgb(14, 165, 233)'; // cyan
      case 'coordinator':
        return 'rgb(34, 197, 94)'; // green
      default:
        return 'rgb(107, 114, 128)'; // gray
    }
  };
  
  // Get agent name based on active agent
  const getAgentName = (): string => {
    switch (activeAgent) {
      case 'content':
        return 'Content Assistant';
      case 'design':
        return 'Design Assistant';
      case 'analytics':
        return 'Analytics Assistant';
      case 'coordinator':
        return 'Agent Coordinator';
      default:
        return 'AI Assistant';
    }
  };

  return (
    <>
      <div className="flex flex-col h-full">
        {aiMesh && (
          <AgentHub
            activeAgent={activeAgent}
            onAgentSelect={handleAgentSelect}
            isCollapsed={isAgentHubCollapsed}
            onToggleCollapse={toggleAgentHub}
          />
        )}
        <ChatInterface
          activeAgent={{
            name: getAgentName(),
            color: getAgentColor(),
          }}
        />
        {aiMesh && (
          <ReasoningPanel
            activeAgentId={activeAgent}
            isCollapsed={!isReasoningPanelOpen}
            onToggleCollapse={toggleReasoningPanel}
          />
        )}
      </div>
      
      <CanvasWorkspace />
      
      {/* Mode Switching Dialog */}
      {showModeDialog && (
        <ModeController
          activeMode={mode}
          onModeChange={handleModeChange}
          showDialog={showModeDialog}
          onDialogClose={() => setShowModeDialog(false)}
        />
      )}
    </>
  );
}
