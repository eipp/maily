import React, { useEffect, useRef, useState } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MarkerType,
  ReactFlowProvider,
  useNodesState,
  useEdgesState
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertCircle, Brain, CheckCircle, ChevronDown, ChevronUp, XCircle } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';

// Define node types for different thought types
const nodeTypes = {
  initial: 'initial',
  analytical: 'analytical',
  creative: 'creative',
  critical: 'critical',
  question: 'question',
  summary: 'summary',
  decision: 'decision'
};

// Define edge types
const edgeTypes = {
  parent: 'parent',
  reference: 'reference'
};

// Role color mapping
const roleColors = {
  coordinator: '#0ea5e9', // sky
  designer: '#f97316',    // orange
  analyst: '#10b981',     // emerald
  writer: '#8b5cf6',      // violet
  researcher: '#ec4899',  // pink
  reviewer: '#f43f5e',    // rose
  user: '#6b7280'         // gray
};

// Thought type icon mapping
const thoughtTypeIcons = {
  initial: <Brain size={16} />,
  analytical: <Brain size={16} />,
  creative: <Brain size={16} />,
  critical: <AlertCircle size={16} />,
  question: <Brain size={16} />,
  summary: <Brain size={16} />,
  decision: <CheckCircle size={16} />
};

// Custom node component
const CustomNode = ({ data }: { data: any }) => {
  const [isOpen, setIsOpen] = useState(false);
  const role = data.role || 'user';
  const type = data.type || 'analytical';
  const confidence = data.confidence || 0;

  const confidenceColor = confidence >= 0.7
    ? 'bg-green-100 text-green-800'
    : confidence >= 0.4
      ? 'bg-yellow-100 text-yellow-800'
      : 'bg-red-100 text-red-800';

  return (
    <Card className="w-64 shadow-md border-l-4" style={{ borderLeftColor: roleColors[role] }}>
      <CardHeader className="p-2">
        <div className="flex justify-between items-center">
          <Badge variant="outline" className="capitalize">
            {role}
          </Badge>
          <Badge variant="secondary" className="capitalize flex items-center gap-1">
            {thoughtTypeIcons[type]} {type}
          </Badge>
        </div>
        <CardTitle className="text-sm mt-1 truncate">{data.label}</CardTitle>
      </CardHeader>
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger asChild>
          <Button variant="ghost" size="sm" className="w-full flex justify-between items-center">
            {isOpen ? 'Hide details' : 'Show details'}
            {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent className="p-2 text-xs">
            <p className="text-gray-700 whitespace-pre-wrap">{data.data.content}</p>
            {confidence > 0 && (
              <div className="mt-2">
                <Badge variant="outline" className={`${confidenceColor} text-xs`}>
                  Confidence: {Math.round(confidence * 100)}%
                </Badge>
              </div>
            )}
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
};

// Interface for the component props
interface ThoughtVisualizerProps {
  canvasId: string;
  rootThoughtId?: string;
  onSelectThought?: (thoughtId: string) => void;
  className?: string;
  height?: string;
}

// Fetch thought tree data from API
const fetchThoughtTree = async (canvasId: string, rootThoughtId?: string) => {
  let url = `/api/v1/canvas/ai/thought_tree/${canvasId}`;
  if (rootThoughtId) {
    url += `?root_thought_id=${rootThoughtId}`;
  }

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to fetch thought tree');
  }

  return response.json();
};

// Fetch all thoughts for a canvas
const fetchAllThoughts = async (canvasId: string) => {
  const response = await fetch(`/api/v1/canvas/ai/thoughts/${canvasId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch thoughts');
  }

  return response.json();
};

// Main component
const ThoughtVisualizer: React.FC<ThoughtVisualizerProps> = ({
  canvasId,
  rootThoughtId,
  onSelectThought,
  className = '',
  height = '600px'
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<'graph' | 'list'>('graph');
  const [allThoughts, setAllThoughts] = useState<any[]>([]);

  // Reference to capture the ReactFlow instance
  const reactFlowInstance = useRef(null);

  // Process data into ReactFlow format
  const processData = (data: any) => {
    // Convert nodes
    const flowNodes = data.nodes.map((node: any) => ({
      id: node.id,
      position: node.position || { x: 0, y: 0 },
      data: {
        label: node.label,
        role: node.role,
        type: node.type,
        confidence: node.confidence,
        data: node.data
      },
      type: 'custom',
    }));

    // Convert edges
    const flowEdges = data.edges.map((edge: any) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: edge.type === 'reference' ? 'step' : 'default',
      markerEnd: {
        type: MarkerType.ArrowClosed,
        width: 15,
        height: 15,
      },
      style: {
        strokeWidth: edge.type === 'reference' ? 1 : 2,
        stroke: edge.type === 'reference' ? '#9ca3af' : '#64748b',
        strokeDasharray: edge.type === 'reference' ? '5 5' : '',
      },
    }));

    return { nodes: flowNodes, edges: flowEdges };
  };

  // Load data
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);

      try {
        // Fetch graph data
        const graphData = await fetchThoughtTree(canvasId, rootThoughtId);
        const { nodes, edges } = processData(graphData);
        setNodes(nodes);
        setEdges(edges);

        // Fetch all thoughts for the list view
        const thoughts = await fetchAllThoughts(canvasId);
        setAllThoughts(thoughts);
      } catch (err) {
        console.error('Error loading thought data:', err);
        setError('Failed to load thought data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [canvasId, rootThoughtId]);

  // Handle node click
  const onNodeClick = (event: any, node: Node) => {
    if (onSelectThought) {
      onSelectThought(node.id);
    }
  };

  // Render loading state
  if (loading) {
    return (
      <Card className={`${className}`}>
        <CardHeader>
          <CardTitle>AI Thought Process</CardTitle>
          <CardDescription>Loading thought visualization...</CardDescription>
        </CardHeader>
        <CardContent className="flex justify-center items-center" style={{ height }}>
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
        </CardContent>
      </Card>
    );
  }

  // Render error state
  if (error) {
    return (
      <Card className={`${className}`}>
        <CardHeader>
          <CardTitle>AI Thought Process</CardTitle>
          <CardDescription>Error loading thought visualization</CardDescription>
        </CardHeader>
        <CardContent className="flex justify-center items-center" style={{ height }}>
          <div className="text-red-500 flex items-center gap-2">
            <XCircle size={16} />
            <span>{error}</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={`${className}`}>
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <div>
            <CardTitle>AI Thought Process</CardTitle>
            <CardDescription>Visualize the AI's chain of thought</CardDescription>
          </div>
          <Tabs defaultValue={view} onValueChange={(v) => setView(v as 'graph' | 'list')}>
            <TabsList>
              <TabsTrigger value="graph">Graph View</TabsTrigger>
              <TabsTrigger value="list">List View</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </CardHeader>
      <CardContent className="p-0" style={{ height }}>
        {view === 'graph' && (
          <ReactFlowProvider>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeClick={onNodeClick}
              nodeTypes={{ custom: CustomNode }}
              fitView
              attributionPosition="bottom-right"
              defaultEdgeOptions={{
                type: 'default',
                markerEnd: {
                  type: MarkerType.ArrowClosed,
                },
              }}
            >
              <Controls />
              <Background />
            </ReactFlow>
          </ReactFlowProvider>
        )}

        {view === 'list' && (
          <div className="p-4 overflow-y-auto" style={{ height: '100%' }}>
            <div className="space-y-4">
              {allThoughts
                .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
                .map((thought) => (
                  <Card
                    key={thought.thought_id}
                    className="border-l-4 cursor-pointer hover:bg-gray-50"
                    style={{ borderLeftColor: roleColors[thought.agent_role] }}
                    onClick={() => onSelectThought && onSelectThought(thought.thought_id)}
                  >
                    <CardHeader className="p-3">
                      <div className="flex justify-between">
                        <Badge variant="outline" className="capitalize">
                          {thought.agent_role}
                        </Badge>
                        <Badge variant="secondary" className="capitalize flex items-center gap-1">
                          {thoughtTypeIcons[thought.thought_type]} {thought.thought_type}
                        </Badge>
                      </div>
                      <CardTitle className="text-sm mt-1">{thought.content.substring(0, 100)}...</CardTitle>
                      <CardDescription className="text-xs">
                        {new Date(thought.timestamp).toLocaleString()}
                      </CardDescription>
                    </CardHeader>
                  </Card>
                ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ThoughtVisualizer;
