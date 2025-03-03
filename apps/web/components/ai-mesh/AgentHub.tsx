"use client"

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { 
  Bot, Brain, Sparkles, Cpu, 
  BarChart, ChevronDown, ChevronUp, 
  Zap, AlertCircle, CheckCircle
} from 'lucide-react';

// Types
export type AgentType = 'content' | 'design' | 'analytics' | 'coordinator';

interface Agent {
  id: AgentType;
  name: string;
  icon: React.ReactNode;
  color: string;
  description: string;
  confidence?: number;
  status: 'idle' | 'thinking' | 'active' | 'error';
}

interface AgentHubProps {
  className?: string;
  activeAgent?: AgentType;
  onAgentSelect?: (agentId: AgentType) => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

export function AgentHub({
  className,
  activeAgent = 'content',
  onAgentSelect,
  isCollapsed = false,
  onToggleCollapse,
}: AgentHubProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  // Agent configurations
  const agents: Agent[] = [
    {
      id: 'content',
      name: 'Content Assistant',
      icon: <Bot className="w-4 h-4" />,
      color: 'rgb(239, 68, 68)', // red
      description: 'Generates and refines email content with Claude 3.7 Sonnet',
      confidence: 0.92,
      status: 'active',
    },
    {
      id: 'design',
      name: 'Design Assistant',
      icon: <Sparkles className="w-4 h-4" />,
      color: 'rgb(168, 85, 247)', // violet
      description: 'Suggests layout and visual improvements with Gemini 2.0',
      confidence: 0.85,
      status: 'idle',
    },
    {
      id: 'analytics',
      name: 'Analytics Assistant',
      icon: <BarChart className="w-4 h-4" />,
      color: 'rgb(14, 165, 233)', // cyan
      description: 'Provides data-driven insights and performance predictions',
      confidence: 0.78,
      status: 'idle',
    },
    {
      id: 'coordinator',
      name: 'Agent Coordinator',
      icon: <Brain className="w-4 h-4" />,
      color: 'rgb(34, 197, 94)', // green
      description: 'Orchestrates agent collaboration and resolves conflicts',
      status: 'idle',
    },
  ];
  
  // Toggle expanded view
  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
  };
  
  // Handle agent selection
  const handleAgentSelect = (agentId: AgentType) => {
    onAgentSelect?.(agentId);
  };
  
  // Get active agent
  const getActiveAgent = () => {
    return agents.find(agent => agent.id === activeAgent) || agents[0];
  };
  
  // Render agent status icon
  const renderStatusIcon = (status: Agent['status']) => {
    switch (status) {
      case 'thinking':
        return (
          <div className="flex space-x-1">
            <div className="w-1.5 h-1.5 rounded-full bg-current animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-1.5 h-1.5 rounded-full bg-current animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-1.5 h-1.5 rounded-full bg-current animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        );
      case 'active':
        return <Zap className="w-3.5 h-3.5" />;
      case 'error':
        return <AlertCircle className="w-3.5 h-3.5" />;
      case 'idle':
      default:
        return <CheckCircle className="w-3.5 h-3.5 opacity-50" />;
    }
  };
  
  // If collapsed, show minimal view
  if (isCollapsed) {
    const active = getActiveAgent();
    
    return (
      <div 
        className={cn(
          "flex flex-col items-center p-2 border-b border-border",
          className
        )}
      >
        <button 
          className="w-full flex items-center justify-between p-2 rounded hover:bg-muted"
          onClick={onToggleCollapse}
        >
          <div className="flex items-center">
            <div 
              className="w-6 h-6 rounded-full flex items-center justify-center mr-2 text-white"
              style={{ backgroundColor: active.color }}
            >
              {active.icon}
            </div>
            <span className="font-medium text-sm">{active.name}</span>
          </div>
          <ChevronDown className="w-4 h-4 text-muted-foreground" />
        </button>
      </div>
    );
  }

  return (
    <div 
      className={cn(
        "flex flex-col border-b border-border",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-3">
        <div className="flex items-center">
          <Brain className="w-4 h-4 mr-2 text-primary" />
          <h2 className="font-medium text-sm">AI Mesh Network</h2>
        </div>
        
        <div className="flex items-center">
          <button 
            className="p-1 rounded hover:bg-muted"
            onClick={toggleExpanded}
            title={isExpanded ? "Collapse" : "Expand"}
          >
            {isExpanded ? (
              <ChevronUp className="w-4 h-4 text-muted-foreground" />
            ) : (
              <ChevronDown className="w-4 h-4 text-muted-foreground" />
            )}
          </button>
          
          <button 
            className="p-1 rounded hover:bg-muted ml-1"
            onClick={onToggleCollapse}
            title="Minimize"
          >
            <ChevronDown className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>
      </div>
      
      {/* Agents List */}
      <div className="px-3 pb-3">
        <div className="space-y-2">
          {agents.map(agent => (
            <div 
              key={agent.id}
              className={cn(
                "border rounded-md p-2 cursor-pointer transition-all",
                agent.id === activeAgent 
                  ? "border-2"
                  : "border hover:border-primary/30"
              )}
              style={{ 
                borderColor: agent.id === activeAgent ? agent.color : undefined,
                backgroundColor: agent.id === activeAgent ? `${agent.color}10` : undefined,
              }}
              onClick={() => handleAgentSelect(agent.id)}
            >
              <div className="flex items-center">
                <div 
                  className="w-7 h-7 rounded-full flex items-center justify-center mr-3 text-white"
                  style={{ backgroundColor: agent.color }}
                >
                  {agent.icon}
                </div>
                
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium text-sm">{agent.name}</h3>
                    <div 
                      className="text-xs opacity-80"
                      style={{ color: agent.color }}
                    >
                      {renderStatusIcon(agent.status)}
                    </div>
                  </div>
                  
                  {isExpanded && (
                    <>
                      <p className="text-xs text-muted-foreground mt-1">
                        {agent.description}
                      </p>
                      
                      {agent.confidence && (
                        <div className="mt-2">
                          <div className="flex items-center justify-between text-xs mb-1">
                            <span className="text-muted-foreground">Confidence</span>
                            <span className="font-medium">{Math.round(agent.confidence * 100)}%</span>
                          </div>
                          <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
                            <div 
                              className="h-full rounded-full"
                              style={{ 
                                width: `${agent.confidence * 100}%`,
                                backgroundColor: agent.color,
                              }}
                            />
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
