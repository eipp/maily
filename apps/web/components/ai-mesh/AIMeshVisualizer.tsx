/**
 * AIMeshVisualizer Component
 * 
 * This component visualizes AI agent interactions in the AI Mesh Network.
 * It displays agent connections, confidence scores, and specializations.
 */

import React, { useEffect, useRef, useState } from 'react';
import { ForceGraph2D } from 'react-force-graph';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Brain, Network, Zap, Filter, RefreshCw, Maximize2, Minimize2 } from 'lucide-react';
import { useTheme } from 'next-themes';
import { useResizeObserver } from '@/hooks/use-resize-observer';
import { useAIMesh } from '@/hooks/use-ai-mesh';
import { Agent, AgentInteraction, AgentSpecialization } from '@/types/ai-mesh';
import { ReasoningPanel } from './ReasoningPanel';

// Define the props
export interface AIMeshVisualizerProps {
  sessionId: string;
  className?: string;
  showControls?: boolean;
  showReasoningPanel?: boolean;
  height?: number;
  width?: number;
  onAgentSelect?: (agent: Agent | null) => void;
}

/**
 * AIMeshVisualizer component
 * 
 * @param props Component props
 * @returns AIMeshVisualizer component
 */
export const AIMeshVisualizer: React.FC<AIMeshVisualizerProps> = ({
  sessionId,
  className = '',
  showControls = true,
  showReasoningPanel = true,
  height,
  width,
  onAgentSelect,
}) => {
  const { theme } = useTheme();
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<any>(null);
  const { width: containerWidth, height: containerHeight } = useResizeObserver(containerRef);
  
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [confidenceThreshold, setConfidenceThreshold] = useState<number>(0.5);
  const [showLabels, setShowLabels] = useState<boolean>(true);
  const [showInactiveAgents, setShowInactiveAgents] = useState<boolean>(false);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<string>('network');
  
  // Get AI Mesh data
  const {
    agents,
    interactions,
    isLoading,
    error,
    refreshData,
  } = useAIMesh(sessionId);
  
  // Filter agents and interactions based on settings
  const filteredAgents = agents.filter(agent => 
    (showInactiveAgents || agent.status === 'active') &&
    agent.confidence >= confidenceThreshold
  );
  
  const filteredInteractions = interactions.filter(interaction => 
    filteredAgents.some(agent => agent.id === interaction.source) &&
    filteredAgents.some(agent => agent.id === interaction.target) &&
    interaction.confidence >= confidenceThreshold
  );
  
  // Prepare graph data
  const graphData = {
    nodes: filteredAgents.map(agent => ({
      id: agent.id,
      name: agent.name,
      val: agent.confidence * 10, // Node size based on confidence
      color: getAgentColor(agent),
      agent,
    })),
    links: filteredInteractions.map(interaction => ({
      source: interaction.source,
      target: interaction.target,
      value: interaction.confidence,
      color: getInteractionColor(interaction),
      interaction,
    })),
  };
  
  // Handle agent selection
  const handleNodeClick = (node: any) => {
    setSelectedAgent(node.agent);
    onAgentSelect?.(node.agent);
    
    if (graphRef.current) {
      graphRef.current.centerAt(node.x, node.y, 1000);
      graphRef.current.zoom(2, 1000);
    }
  };
  
  // Handle fullscreen toggle
  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    
    if (!isFullscreen) {
      if (containerRef.current.requestFullscreen) {
        containerRef.current.requestFullscreen();
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  };
  
  // Listen for fullscreen changes
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);
  
  // Calculate graph dimensions
  const graphWidth = width || containerWidth || 800;
  const graphHeight = height || containerHeight || 600;
  
  return (
    <div
      ref={containerRef}
      className={`relative border rounded-lg overflow-hidden ${className}`}
      style={{ height: height || '600px' }}
    >
      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="absolute top-2 left-2 z-10 bg-background/80 backdrop-blur-sm rounded-lg p-1"
      >
        <TabsList>
          <TabsTrigger value="network">
            <Network className="h-4 w-4 mr-2" />
            Network
          </TabsTrigger>
          <TabsTrigger value="agents">
            <Brain className="h-4 w-4 mr-2" />
            Agents
          </TabsTrigger>
        </TabsList>
      </Tabs>
      
      {/* Controls */}
      {showControls && (
        <Card className="absolute top-14 left-2 z-10 w-64 bg-background/80 backdrop-blur-sm">
          <CardHeader className="p-3">
            <CardTitle className="text-sm flex items-center">
              <Filter className="h-4 w-4 mr-2" />
              Visualization Controls
            </CardTitle>
          </CardHeader>
          <CardContent className="p-3 space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="confidence-threshold">Confidence Threshold</Label>
                <Badge variant="outline">{confidenceThreshold.toFixed(2)}</Badge>
              </div>
              <Slider
                id="confidence-threshold"
                min={0}
                max={1}
                step={0.05}
                value={[confidenceThreshold]}
                onValueChange={(value) => setConfidenceThreshold(value[0])}
              />
            </div>
            
            <div className="flex items-center space-x-2">
              <Switch
                id="show-labels"
                checked={showLabels}
                onCheckedChange={setShowLabels}
              />
              <Label htmlFor="show-labels">Show Labels</Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Switch
                id="show-inactive"
                checked={showInactiveAgents}
                onCheckedChange={setShowInactiveAgents}
              />
              <Label htmlFor="show-inactive">Show Inactive Agents</Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Button
                size="sm"
                variant="outline"
                className="flex-1"
                onClick={refreshData}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
              
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={toggleFullscreen}
                    >
                      {isFullscreen ? (
                        <Minimize2 className="h-4 w-4" />
                      ) : (
                        <Maximize2 className="h-4 w-4" />
                      )}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    {isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'}
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* Graph visualization */}
      <TabsContent value="network" className="m-0 h-full">
        {graphData.nodes.length > 0 ? (
          <ForceGraph2D
            ref={graphRef}
            graphData={graphData}
            nodeLabel={(node: any) => `${node.name} (${(node.agent.confidence * 100).toFixed(0)}%)`}
            linkLabel={(link: any) => `Confidence: ${(link.value * 100).toFixed(0)}%`}
            nodeRelSize={6}
            linkWidth={(link: any) => link.value * 5}
            linkDirectionalParticles={4}
            linkDirectionalParticleWidth={(link: any) => link.value * 4}
            nodeCanvasObject={(node: any, ctx, globalScale) => {
              // Draw node
              const size = node.val;
              ctx.beginPath();
              ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
              ctx.fillStyle = node.color;
              ctx.fill();
              
              // Draw border for selected node
              if (selectedAgent && node.id === selectedAgent.id) {
                ctx.beginPath();
                ctx.arc(node.x, node.y, size + 2, 0, 2 * Math.PI);
                ctx.strokeStyle = theme === 'dark' ? 'white' : 'black';
                ctx.lineWidth = 2;
                ctx.stroke();
              }
              
              // Draw label if enabled
              if (showLabels && globalScale >= 1) {
                const label = node.name;
                const fontSize = 12 / globalScale;
                ctx.font = `${fontSize}px Sans-Serif`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillStyle = theme === 'dark' ? 'white' : 'black';
                ctx.fillText(label, node.x, node.y + size + fontSize);
              }
            }}
            onNodeClick={handleNodeClick}
            width={graphWidth}
            height={graphHeight}
            backgroundColor={theme === 'dark' ? '#1a1a1a' : '#ffffff'}
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-muted-foreground">
              {isLoading ? 'Loading AI Mesh data...' : 'No agents match the current filters'}
            </p>
          </div>
        )}
      </TabsContent>
      
      {/* Agents list */}
      <TabsContent value="agents" className="m-0 h-full overflow-auto p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredAgents.map(agent => (
            <Card
              key={agent.id}
              className={`cursor-pointer transition-all ${
                selectedAgent?.id === agent.id ? 'ring-2 ring-primary' : ''
              }`}
              onClick={() => handleNodeClick({ agent })}
            >
              <CardHeader className="p-4 pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">{agent.name}</CardTitle>
                  <Badge
                    variant={agent.status === 'active' ? 'default' : 'outline'}
                  >
                    {agent.status}
                  </Badge>
                </div>
                <CardDescription>
                  Confidence: {(agent.confidence * 100).toFixed(0)}%
                </CardDescription>
              </CardHeader>
              <CardContent className="p-4 pt-0">
                <div className="flex flex-wrap gap-1 mt-2">
                  {agent.specializations.map(spec => (
                    <Badge
                      key={spec}
                      variant="secondary"
                      className="text-xs"
                    >
                      {spec}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </TabsContent>
      
      {/* Reasoning panel */}
      {showReasoningPanel && selectedAgent && (
        <div className="absolute bottom-0 right-0 w-full md:w-1/3 z-10">
          <ReasoningPanel
            agent={selectedAgent}
            onClose={() => {
              setSelectedAgent(null);
              onAgentSelect?.(null);
            }}
          />
        </div>
      )}
    </div>
  );
};

/**
 * Get color for agent based on specialization and confidence
 * 
 * @param agent Agent
 * @returns Color
 */
function getAgentColor(agent: Agent): string {
  // Base colors for different specializations
  const specializationColors: Record<AgentSpecialization, string> = {
    'reasoning': '#3b82f6', // blue
    'creativity': '#8b5cf6', // purple
    'research': '#10b981', // green
    'planning': '#f59e0b', // amber
    'coding': '#ef4444', // red
    'math': '#ec4899', // pink
    'writing': '#6366f1', // indigo
    'general': '#6b7280', // gray
  };
  
  // Get primary specialization
  const primarySpecialization = agent.specializations[0] || 'general';
  
  // Get base color
  const baseColor = specializationColors[primarySpecialization as AgentSpecialization] || '#6b7280';
  
  // Adjust opacity based on confidence
  return `${baseColor}${Math.round(agent.confidence * 255).toString(16).padStart(2, '0')}`;
}

/**
 * Get color for interaction based on confidence
 * 
 * @param interaction Agent interaction
 * @returns Color
 */
function getInteractionColor(interaction: AgentInteraction): string {
  // Base color
  const baseColor = '#6b7280';
  
  // Adjust opacity based on confidence
  return `${baseColor}${Math.round(interaction.confidence * 255).toString(16).padStart(2, '0')}`;
}

export default AIMeshVisualizer;
