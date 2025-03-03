'use client';

import { useRef, useEffect, useState } from 'react';
import { throttle } from 'lodash';

type Node = {
  id: string;
  x: number;
  y: number;
  size: number;
  speed: number;
  angle: number;
  color: string;
  role: string;
  neighbors: string[];
  highlighted: boolean;
};

type AINetworkGraphProps = {
  className?: string;
  height?: number;
  interactive?: boolean;
  highlightedNode?: string | null;
  onNodeHover?: (nodeId: string | null) => void;
  onNodeClick?: (nodeId: string) => void;
  density?: 'low' | 'medium' | 'high';
};

const NODE_ROLES = [
  { id: 'content', label: 'Content Agent', color: '#3b82f6' },
  { id: 'design', label: 'Design Agent', color: '#8b5cf6' },
  { id: 'analytics', label: 'Analytics Agent', color: '#10b981' },
  { id: 'personalization', label: 'Personalization Agent', color: '#f59e0b' },
  { id: 'optimization', label: 'Optimization Agent', color: '#ef4444' },
  { id: 'verification', label: 'Trust Verification', color: '#6366f1' },
];

const getNodeCount = (density: 'low' | 'medium' | 'high') => {
  switch (density) {
    case 'low': return 8;
    case 'medium': return 12;
    case 'high': return 16;
    default: return 12;
  }
};

export default function AINetworkGraph({
  className = '',
  height = 400,
  interactive = true,
  highlightedNode = null,
  onNodeHover,
  onNodeClick,
  density = 'medium',
}: AINetworkGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [animationIntensity, setAnimationIntensity] = useState<number>(0);
  const [isInView, setIsInView] = useState(false);
  
  // Handle mouse interaction
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!interactive || !canvasRef.current || !containerRef.current) return;
    
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    let closestNode: Node | null = null;
    let closestDistance = 50; // Minimum detection radius
    
    nodes.forEach(node => {
      const dx = node.x - x;
      const dy = node.y - y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      
      if (distance < closestDistance) {
        closestNode = node;
        closestDistance = distance;
      }
    });
    
    const newHoveredNode = closestNode ? closestNode.id : null;
    
    if (newHoveredNode !== hoveredNode) {
      setHoveredNode(newHoveredNode);
      if (onNodeHover) onNodeHover(newHoveredNode);
    }
  };
  
  const handleMouseLeave = () => {
    setHoveredNode(null);
    if (onNodeHover) onNodeHover(null);
  };
  
  const handleClick = () => {
    if (hoveredNode && onNodeClick) {
      onNodeClick(hoveredNode);
      // Increase animation intensity temporarily
      setAnimationIntensity(1);
      setTimeout(() => setAnimationIntensity(0), 2000);
    }
  };
  
  // Initialize nodes
  useEffect(() => {
    if (!containerRef.current) return;
    
    const containerWidth = containerRef.current.clientWidth;
    const containerHeight = height;
    const nodeCount = getNodeCount(density);
    
    // Create nodes
    const newNodes: Node[] = [];
    
    for (let i = 0; i < nodeCount; i++) {
      const role = NODE_ROLES[i % NODE_ROLES.length];
      
      newNodes.push({
        id: `node-${i}`,
        x: Math.random() * containerWidth * 0.8 + containerWidth * 0.1,
        y: Math.random() * containerHeight * 0.8 + containerHeight * 0.1,
        size: Math.random() * 5 + 5,
        speed: Math.random() * 0.2 + 0.1,
        angle: Math.random() * Math.PI * 2,
        color: role.color,
        role: role.id,
        neighbors: [],
        highlighted: false
      });
    }
    
    // Create connections (each node connects to 2-4 others)
    newNodes.forEach((node, i) => {
      const connectionCount = Math.floor(Math.random() * 3) + 2;
      const possibleTargets = [...newNodes].filter(n => n.id !== node.id);
      
      // Shuffle and take first N
      const shuffled = possibleTargets.sort(() => 0.5 - Math.random());
      const targets = shuffled.slice(0, Math.min(connectionCount, shuffled.length));
      
      targets.forEach(target => {
        if (!node.neighbors.includes(target.id)) {
          node.neighbors.push(target.id);
        }
        if (!target.neighbors.includes(node.id)) {
          target.neighbors.push(node.id);
        }
      });
    });
    
    setNodes(newNodes);
  }, [density, height]);
  
  // Animation effect
  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Handle resize with proper canvas sizing
    const resizeCanvas = () => {
      const { width, height } = container.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      
      ctx.scale(dpr, dpr);
    };
    
    resizeCanvas();
    
    const handleResize = throttle(resizeCanvas, 200);
    window.addEventListener('resize', handleResize);
    
    // Intersection Observer to only animate when in viewport
    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsInView(entry.isIntersecting);
      },
      {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
      }
    );
    
    observer.observe(container);
    
    // Animation loop
    let animationFrameId: number;
    
    const highlightNode = highlightedNode || hoveredNode;
    
    const render = () => {
      if (!isInView) {
        animationFrameId = requestAnimationFrame(render);
        return;
      }
      
      const { width, height } = container.getBoundingClientRect();
      
      ctx.clearRect(0, 0, width, height);
      
      // Update and draw node connections first (behind nodes)
      const updatedNodes = nodes.map(node => {
        // Basic movement in random direction
        const speedFactor = 1 + animationIntensity;
        
        // Move node in its current direction
        node.x += Math.cos(node.angle) * node.speed * speedFactor;
        node.y += Math.sin(node.angle) * node.speed * speedFactor;
        
        // Boundary check with direction change
        if (node.x < node.size || node.x > width - node.size) {
          node.angle = Math.PI - node.angle;
          node.x = Math.max(node.size, Math.min(width - node.size, node.x));
        }
        
        if (node.y < node.size || node.y > height - node.size) {
          node.angle = -node.angle;
          node.y = Math.max(node.size, Math.min(height - node.size, node.y));
        }
        
        // Slightly randomize direction occasionally
        if (Math.random() < 0.02) {
          node.angle += (Math.random() - 0.5) * 0.5;
        }
        
        // Set highlighted state
        node.highlighted = node.id === highlightNode || 
                          (highlightNode && node.neighbors.includes(highlightNode));
        
        return node;
      });
      
      // Draw connections
      ctx.lineWidth = 1;
      updatedNodes.forEach(node => {
        node.neighbors.forEach(neighborId => {
          const neighbor = updatedNodes.find(n => n.id === neighborId);
          if (!neighbor) return;
          
          const isHighlighted = node.highlighted && neighbor.highlighted;
          
          // Calculate distance for line opacity
          const dx = node.x - neighbor.x;
          const dy = node.y - neighbor.y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          const maxDistance = 200;
          const opacity = Math.max(0, 1 - distance / maxDistance);
          
          // Set color based on highlighting
          if (isHighlighted) {
            ctx.strokeStyle = `rgba(255, 255, 255, ${opacity * 0.8})`;
            ctx.lineWidth = 2;
          } else {
            ctx.strokeStyle = `rgba(255, 255, 255, ${opacity * 0.15})`;
            ctx.lineWidth = 1;
          }
          
          // Draw line
          ctx.beginPath();
          ctx.moveTo(node.x, node.y);
          ctx.lineTo(neighbor.x, neighbor.y);
          ctx.stroke();
          
          // Draw pulses along the connections for highlighted ones
          if (isHighlighted && opacity > 0.3) {
            const pulseCount = Math.floor(distance / 30);
            const now = Date.now() / 1000;
            
            for (let i = 0; i < pulseCount; i++) {
              // Calculate position along the line with time-based offset
              const offset = ((now * (0.4 + animationIntensity)) % 1 + i / pulseCount) % 1;
              const x = node.x + (neighbor.x - node.x) * offset;
              const y = node.y + (neighbor.y - node.y) * offset;
              
              // Draw pulse
              const pulseSize = 3 * (1 - Math.abs(offset - 0.5) * 2);
              ctx.beginPath();
              ctx.arc(x, y, pulseSize, 0, Math.PI * 2);
              ctx.fillStyle = highlightNode === node.id || highlightNode === neighbor.id
                ? node.color
                : `rgba(255, 255, 255, 0.8)`;
              ctx.fill();
            }
          }
        });
      });
      
      // Draw nodes
      updatedNodes.forEach(node => {
        ctx.beginPath();
        
        // Base glow for all nodes
        const glowSize = node.size * (1.5 + animationIntensity * 0.5);
        const gradient = ctx.createRadialGradient(
          node.x, node.y, 0,
          node.x, node.y, glowSize * 2
        );
        
        gradient.addColorStop(0, node.highlighted 
          ? `${node.color}CC` 
          : `${node.color}66`);
        gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
        
        ctx.fillStyle = gradient;
        ctx.arc(node.x, node.y, glowSize, 0, Math.PI * 2);
        ctx.fill();
        
        // Node itself
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.size, 0, Math.PI * 2);
        ctx.fillStyle = node.highlighted ? node.color : `${node.color}99`;
        ctx.fill();
        
        // Node border
        ctx.lineWidth = node.highlighted ? 2 : 1;
        ctx.strokeStyle = node.highlighted ? 'rgba(255, 255, 255, 0.8)' : 'rgba(255, 255, 255, 0.3)';
        ctx.stroke();
        
        // Draw label for hovered/highlighted node
        if (node.id === hoveredNode || node.id === highlightedNode) {
          const role = NODE_ROLES.find(r => r.id === node.role);
          if (role) {
            ctx.font = '14px Inter, sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            
            // Background for text
            const textMetrics = ctx.measureText(role.label);
            const textWidth = textMetrics.width;
            const textHeight = 20; // Approximate height
            
            ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
            ctx.fillRect(
              node.x - textWidth / 2 - 6,
              node.y + node.size + 6,
              textWidth + 12,
              textHeight
            );
            
            // Text
            ctx.fillStyle = '#FFFFFF';
            ctx.fillText(role.label, node.x, node.y + node.size + 16);
          }
        }
      });
      
      setNodes(updatedNodes);
      animationFrameId = requestAnimationFrame(render);
    };
    
    animationFrameId = requestAnimationFrame(render);
    
    return () => {
      window.removeEventListener('resize', handleResize);
      observer.disconnect();
      cancelAnimationFrame(animationFrameId);
    };
  }, [nodes, hoveredNode, highlightedNode, animationIntensity, isInView]);
  
  return (
    <div 
      ref={containerRef}
      className={`relative overflow-hidden rounded-xl bg-gradient-to-br from-gray-900 to-indigo-950 ${className}`}
      style={{ height }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={handleClick}
    >
      <canvas 
        ref={canvasRef} 
        className="absolute inset-0 w-full h-full"
      />
    </div>
  );
} 