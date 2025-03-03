import React, { useEffect, useRef, useState } from 'react';
import { Box, Heading, Text, Flex, Badge, Spinner, useColorModeValue, Tooltip, VStack, HStack, Icon } from '@chakra-ui/react';
import { InfoIcon, WarningIcon, CheckCircleIcon } from '@chakra-ui/icons';
import { FaBrain, FaNetworkWired, FaRobot, FaExchangeAlt, FaMemory } from 'react-icons/fa';

interface Agent {
  id: string;
  name: string;
  type: string;
  status: 'idle' | 'working' | 'error' | 'completed';
  confidence: number;
  lastAction?: string;
  assignedTasks?: string[];
  connections?: string[];
  model?: string;
}

interface Task {
  id: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  assignedTo?: string;
  createdAt: string;
  completedAt?: string;
  dependencies?: string[];
  result?: string;
}

interface Memory {
  id: string;
  type: 'fact' | 'context' | 'decision' | 'feedback';
  content: string;
  createdAt: string;
  createdBy: string;
  confidence: number;
  relatedTo?: string[];
}

interface AgentNetworkVisualizerProps {
  networkId: string;
  height?: string | number;
  showDetails?: boolean;
  onAgentClick?: (agentId: string) => void;
  onTaskClick?: (taskId: string) => void;
  onMemoryClick?: (memoryId: string) => void;
}

const AgentNetworkVisualizer: React.FC<AgentNetworkVisualizerProps> = ({
  networkId,
  height = '500px',
  showDetails = false,
  onAgentClick,
  onTaskClick,
  onMemoryClick
}) => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  
  useEffect(() => {
    const fetchNetworkData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch network data from API
        const response = await fetch(`/api/v1/ai-mesh/networks/${networkId}`);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch network data: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
          setAgents(data.data.agents || []);
          setTasks(data.data.tasks || []);
          setMemories(data.data.memories || []);
        } else {
          setError(data.message || 'Failed to fetch network data');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
      } finally {
        setLoading(false);
      }
    };
    
    if (networkId) {
      fetchNetworkData();
    }
    
    // Set up polling for real-time updates
    const intervalId = setInterval(() => {
      if (networkId) {
        fetchNetworkData();
      }
    }, 5000); // Poll every 5 seconds
    
    return () => clearInterval(intervalId);
  }, [networkId]);
  
  useEffect(() => {
    if (loading || error || !canvasRef.current || agents.length === 0) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Resize canvas to container size
    const resizeCanvas = () => {
      if (containerRef.current && canvas) {
        const rect = containerRef.current.getBoundingClientRect();
        canvas.width = rect.width;
        canvas.height = rect.height;
        drawNetwork();
      }
    };
    
    // Draw network visualization
    const drawNetwork = () => {
      if (!ctx) return;
      
      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Calculate positions (simple circle layout)
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      const radius = Math.min(centerX, centerY) * 0.8;
      
      const agentPositions: Record<string, {x: number, y: number}> = {};
      
      // Position agents in a circle
      agents.forEach((agent, index) => {
        const angle = (index / agents.length) * Math.PI * 2;
        const x = centerX + radius * Math.cos(angle);
        const y = centerY + radius * Math.sin(angle);
        
        agentPositions[agent.id] = { x, y };
        
        // Draw agent node
        ctx.beginPath();
        ctx.arc(x, y, 20, 0, Math.PI * 2);
        
        // Color based on status
        switch (agent.status) {
          case 'idle':
            ctx.fillStyle = '#718096'; // gray.500
            break;
          case 'working':
            ctx.fillStyle = '#3182CE'; // blue.500
            break;
          case 'error':
            ctx.fillStyle = '#E53E3E'; // red.500
            break;
          case 'completed':
            ctx.fillStyle = '#38A169'; // green.500
            break;
          default:
            ctx.fillStyle = '#718096'; // gray.500
        }
        
        // Highlight selected agent
        if (agent.id === selectedAgentId) {
          ctx.lineWidth = 3;
          ctx.strokeStyle = '#F6AD55'; // orange.300
        } else {
          ctx.lineWidth = 1;
          ctx.strokeStyle = '#A0AEC0'; // gray.400
        }
        
        ctx.fill();
        ctx.stroke();
        
        // Draw agent label
        ctx.font = '10px sans-serif';
        ctx.fillStyle = '#FFFFFF';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(agent.name.charAt(0), x, y);
        
        // Draw agent name below
        ctx.font = '12px sans-serif';
        ctx.fillStyle = '#2D3748'; // gray.700
        ctx.fillText(agent.name, x, y + 35);
      });
      
      // Draw connections between agents
      ctx.lineWidth = 1;
      agents.forEach(agent => {
        if (!agent.connections) return;
        
        const fromPos = agentPositions[agent.id];
        
        agent.connections.forEach(targetId => {
          const toPos = agentPositions[targetId];
          
          if (fromPos && toPos) {
            ctx.beginPath();
            ctx.moveTo(fromPos.x, fromPos.y);
            ctx.lineTo(toPos.x, toPos.y);
            ctx.strokeStyle = '#A0AEC0'; // gray.400
            ctx.stroke();
            
            // Draw arrow
            const angle = Math.atan2(toPos.y - fromPos.y, toPos.x - fromPos.x);
            const arrowSize = 8;
            
            ctx.beginPath();
            ctx.moveTo(
              toPos.x - arrowSize * Math.cos(angle - Math.PI / 6),
              toPos.y - arrowSize * Math.sin(angle - Math.PI / 6)
            );
            ctx.lineTo(toPos.x, toPos.y);
            ctx.lineTo(
              toPos.x - arrowSize * Math.cos(angle + Math.PI / 6),
              toPos.y - arrowSize * Math.sin(angle + Math.PI / 6)
            );
            ctx.strokeStyle = '#A0AEC0'; // gray.400
            ctx.stroke();
          }
        });
      });
    };
    
    // Handle canvas click
    const handleCanvasClick = (event: MouseEvent) => {
      if (!canvas) return;
      
      const rect = canvas.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;
      
      // Check if click is on an agent
      for (const agent of agents) {
        const agentPos = agentPositions[agent.id];
        if (!agentPos) continue;
        
        const distance = Math.sqrt(
          Math.pow(x - agentPos.x, 2) + Math.pow(y - agentPos.y, 2)
        );
        
        if (distance <= 20) {
          setSelectedAgentId(agent.id);
          if (onAgentClick) {
            onAgentClick(agent.id);
          }
          break;
        }
      }
    };
    
    // Add event listeners
    canvas.addEventListener('click', handleCanvasClick);
    window.addEventListener('resize', resizeCanvas);
    
    // Initial draw
    resizeCanvas();
    
    return () => {
      canvas.removeEventListener('click', handleCanvasClick);
      window.removeEventListener('resize', resizeCanvas);
    };
  }, [agents, loading, error, selectedAgentId, onAgentClick]);
  
  const getAgentStatusColor = (status: Agent['status']) => {
    switch (status) {
      case 'idle': return 'gray';
      case 'working': return 'blue';
      case 'error': return 'red';
      case 'completed': return 'green';
      default: return 'gray';
    }
  };
  
  const getTaskStatusColor = (status: Task['status']) => {
    switch (status) {
      case 'pending': return 'gray';
      case 'in_progress': return 'blue';
      case 'completed': return 'green';
      case 'failed': return 'red';
      default: return 'gray';
    }
  };
  
  const getMemoryTypeIcon = (type: Memory['type']) => {
    switch (type) {
      case 'fact': return InfoIcon;
      case 'context': return FaNetworkWired;
      case 'decision': return CheckCircleIcon;
      case 'feedback': return WarningIcon;
      default: return InfoIcon;
    }
  };
  
  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString();
    } catch (err) {
      return dateString;
    }
  };
  
  const renderAgentDetails = () => {
    if (!selectedAgentId) return null;
    
    const agent = agents.find(a => a.id === selectedAgentId);
    if (!agent) return null;
    
    const agentTasks = tasks.filter(t => t.assignedTo === agent.id);
    
    return (
      <Box 
        p={4} 
        borderWidth={1} 
        borderRadius="md" 
        borderColor={borderColor}
        bg={bgColor}
        boxShadow="sm"
        mt={4}
      >
        <Flex justifyContent="space-between" alignItems="center" mb={2}>
          <Heading size="md">{agent.name}</Heading>
          <Badge colorScheme={getAgentStatusColor(agent.status)}>
            {agent.status}
          </Badge>
        </Flex>
        
        <Text fontSize="sm" color="gray.500" mb={2}>
          Type: {agent.type}
        </Text>
        
        {agent.model && (
          <Text fontSize="sm" color="gray.500" mb={2}>
            Model: {agent.model}
          </Text>
        )}
        
        <Text fontSize="sm" mb={2}>
          Confidence: {agent.confidence.toFixed(2)}
        </Text>
        
        {agent.lastAction && (
          <Text fontSize="sm" mb={2}>
            Last Action: {agent.lastAction}
          </Text>
        )}
        
        {agentTasks.length > 0 && (
          <Box mt={3}>
            <Heading size="xs" mb={2}>Assigned Tasks</Heading>
            <VStack align="stretch" spacing={2}>
              {agentTasks.map(task => (
                <Box 
                  key={task.id}
                  p={2}
                  borderWidth={1}
                  borderRadius="md"
                  borderColor={borderColor}
                  onClick={() => onTaskClick && onTaskClick(task.id)}
                  cursor="pointer"
                  _hover={{ bg: 'gray.50' }}
                >
                  <Flex justifyContent="space-between" alignItems="center">
                    <Text fontSize="sm" fontWeight="medium" noOfLines={1}>
                      {task.description}
                    </Text>
                    <Badge colorScheme={getTaskStatusColor(task.status)} size="sm">
                      {task.status}
                    </Badge>
                  </Flex>
                </Box>
              ))}
            </VStack>
          </Box>
        )}
      </Box>
    );
  };
  
  const renderNetworkStats = () => {
    if (loading || error || agents.length === 0) return null;
    
    const activeAgents = agents.filter(a => a.status === 'working').length;
    const completedTasks = tasks.filter(t => t.status === 'completed').length;
    const pendingTasks = tasks.filter(t => t.status === 'pending').length;
    
    return (
      <HStack spacing={4} mt={4} justify="center">
        <Tooltip label="Active Agents">
          <Flex 
            direction="column" 
            align="center" 
            p={3} 
            borderWidth={1} 
            borderRadius="md" 
            borderColor={borderColor}
          >
            <Icon as={FaRobot} boxSize={5} color="blue.500" mb={1} />
            <Text fontWeight="bold">{activeAgents}</Text>
            <Text fontSize="xs">Active</Text>
          </Flex>
        </Tooltip>
        
        <Tooltip label="Total Agents">
          <Flex 
            direction="column" 
            align="center" 
            p={3} 
            borderWidth={1} 
            borderRadius="md" 
            borderColor={borderColor}
          >
            <Icon as={FaBrain} boxSize={5} color="purple.500" mb={1} />
            <Text fontWeight="bold">{agents.length}</Text>
            <Text fontSize="xs">Agents</Text>
          </Flex>
        </Tooltip>
        
        <Tooltip label="Completed Tasks">
          <Flex 
            direction="column" 
            align="center" 
            p={3} 
            borderWidth={1} 
            borderRadius="md" 
            borderColor={borderColor}
          >
            <Icon as={CheckCircleIcon} boxSize={5} color="green.500" mb={1} />
            <Text fontWeight="bold">{completedTasks}</Text>
            <Text fontSize="xs">Completed</Text>
          </Flex>
        </Tooltip>
        
        <Tooltip label="Pending Tasks">
          <Flex 
            direction="column" 
            align="center" 
            p={3} 
            borderWidth={1} 
            borderRadius="md" 
            borderColor={borderColor}
          >
            <Icon as={FaExchangeAlt} boxSize={5} color="orange.500" mb={1} />
            <Text fontWeight="bold">{pendingTasks}</Text>
            <Text fontSize="xs">Pending</Text>
          </Flex>
        </Tooltip>
        
        <Tooltip label="Shared Memories">
          <Flex 
            direction="column" 
            align="center" 
            p={3} 
            borderWidth={1} 
            borderRadius="md" 
            borderColor={borderColor}
          >
            <Icon as={FaMemory} boxSize={5} color="cyan.500" mb={1} />
            <Text fontWeight="bold">{memories.length}</Text>
            <Text fontSize="xs">Memories</Text>
          </Flex>
        </Tooltip>
      </HStack>
    );
  };
  
  return (
    <Box>
      <Heading size="md" mb={4}>AI Mesh Network</Heading>
      
      {loading ? (
        <Flex justify="center" align="center" height={height}>
          <Spinner size="xl" />
        </Flex>
      ) : error ? (
        <Flex 
          justify="center" 
          align="center" 
          height={height}
          direction="column"
          bg="red.50"
          borderRadius="md"
          p={4}
        >
          <WarningIcon color="red.500" boxSize={10} mb={4} />
          <Text color="red.500">{error}</Text>
        </Flex>
      ) : agents.length === 0 ? (
        <Flex 
          justify="center" 
          align="center" 
          height={height}
          direction="column"
          bg="gray.50"
          borderRadius="md"
          p={4}
        >
          <InfoIcon color="blue.500" boxSize={10} mb={4} />
          <Text>No agents found in this network.</Text>
        </Flex>
      ) : (
        <>
          {renderNetworkStats()}
          
          <Box 
            ref={containerRef}
            height={height} 
            borderWidth={1} 
            borderRadius="md" 
            borderColor={borderColor}
            position="relative"
            overflow="hidden"
            mt={4}
          >
            <canvas 
              ref={canvasRef} 
              style={{ 
                width: '100%', 
                height: '100%',
                display: 'block'
              }}
            />
          </Box>
          
          {showDetails && renderAgentDetails()}
        </>
      )}
    </Box>
  );
};

export default AgentNetworkVisualizer;
