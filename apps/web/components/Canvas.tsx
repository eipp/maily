'use client';

import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { Stage, Layer, Rect, Circle, Text, Transformer, Group, Image } from 'react-konva';
import type { KonvaEventObject } from 'konva/lib/Node';
import type Konva from 'konva';
import { 
  Undo2, Redo2, Download, Square, Circle as CircleIcon, Type, Trash2,
  Layers, Eye, EyeOff, Activity, Users, UserCheck, LineChart, Loader,
  Shield, ShieldCheck
} from 'lucide-react';
import { Button } from '@/components/Button';
import { OptimizedYjsProvider } from '@/lib/optimized-yjs';
import { canvasPerformance } from '@/utils/canvasPerformance';
import { useCanvasShapeWorker } from '@/hooks/useCanvasShapeWorker';
import { useCanvasWorker } from '@/hooks/useCanvasWorker';

// Types
export interface Shape {
  id: string;
  type: 'rect' | 'circle' | 'text';
  x: number;
  y: number;
  width?: number;
  height?: number;
  radius?: number;
  fill: string;
  text?: string;
  fontSize?: number;
  isDragging?: boolean;
  isSelected?: boolean;
  layerId?: string;
}

interface HistoryState {
  past: Shape[][];
  present: Shape[];
  future: Shape[][];
}

interface Layer {
  id: string;
  name: string;
  visible: boolean;
  locked: boolean;
}

interface ConnectedUser {
  id: string;
  name: string;
  color: string;
  cursor?: { x: number, y: number };
}

interface PerformanceData {
  fps: number;
  renderTime: number;
  collaborationLatency: number;
  shapeCount: number;
}

// Constants
const COLORS = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD'];
const INITIAL_SHAPES: Shape[] = [
  {
    id: '1',
    type: 'rect',
    x: 50,
    y: 50,
    width: 100,
    height: 100,
    fill: COLORS[0],
    isDragging: false,
    isSelected: false,
    layerId: 'layer1',
  },
  {
    id: '2',
    type: 'circle',
    x: 200,
    y: 100,
    radius: 50,
    fill: COLORS[1],
    isDragging: false,
    isSelected: false,
    layerId: 'layer1',
  },
  {
    id: '3',
    type: 'text',
    x: 300,
    y: 200,
    text: 'Hello Konva',
    fontSize: 24,
    fill: COLORS[2],
    isDragging: false,
    isSelected: false,
    layerId: 'layer2',
  },
];

const INITIAL_LAYERS: Layer[] = [
  { id: 'layer1', name: 'Base Layer', visible: true, locked: false },
  { id: 'layer2', name: 'Text Layer', visible: true, locked: false },
  { id: 'layer3', name: 'Effects Layer', visible: true, locked: false },
];

// Helper hook for Yjs integration
function useOptimizedYjs(roomId: string, userId: string) {
  const [provider, setProvider] = useState<OptimizedYjsProvider | null>(null);
  const [connectedUsers, setConnectedUsers] = useState<ConnectedUser[]>([]);
  
  useEffect(() => {
    // Create provider instance
    const yjsProvider = new OptimizedYjsProvider(
      // Use websocket URL from environment or default
      process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'wss://api.maily.app/ws/canvas',
      `canvas-${roomId}`,
      userId,
      { updateThrottleMs: 50 }
    );
    
    setProvider(yjsProvider);
    
    // Set up awareness handler
    const unsubscribeAwareness = yjsProvider.onAwarenessChange((states) => {
      const users: ConnectedUser[] = [];
      states.forEach((state, clientId) => {
        if (state.user) {
          users.push({
            id: state.user.id,
            name: state.user.name || 'Anonymous',
            color: state.user.color,
            cursor: state.user.cursor,
          });
        }
      });
      setConnectedUsers(users);
    });
    
    // Clean up
    return () => {
      unsubscribeAwareness();
      yjsProvider.destroy();
    };
  }, [roomId, userId]);
  
  return { provider, connectedUsers };
}

interface VerificationStatus {
  isVerified: boolean;
  showVerificationLayer: boolean;
  certificateData?: {
    id: string;
    issuer: string;
    timestamp: string;
  };
}

interface CanvasProps {
  roomId?: string;
  userId?: string;
  initialShapes?: Shape[];
  initialLayers?: Layer[];
  readonly?: boolean;
  verificationStatus?: VerificationStatus;
  onToggleVerificationLayer?: () => void;
}

export function Canvas({
  roomId = 'default',
  userId = `user-${Math.floor(Math.random() * 100000)}`,
  initialShapes = INITIAL_SHAPES,
  initialLayers = INITIAL_LAYERS,
  readonly = false,
  verificationStatus = { isVerified: false, showVerificationLayer: false },
  onToggleVerificationLayer,
}: CanvasProps) {
  // Refs
  const stageRef = useRef<Konva.Stage>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const transformerRef = useRef<Konva.Transformer>(null);
  const performanceIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Workers
  const { isReady: isShapeWorkerReady, findShapesInSelection } = useCanvasShapeWorker();
  const { transformImage } = useCanvasWorker();

  // Yjs integration
  const { provider, connectedUsers } = useOptimizedYjs(roomId, userId);

  // State
  const [stageSize, setStageSize] = useState({ width: 800, height: 600 });
  const [history, setHistory] = useState<HistoryState>({
    past: [],
    present: initialShapes,
    future: [],
  });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [tool, setTool] = useState<'select' | 'rect' | 'circle' | 'text'>('select');
  const [layers, setLayers] = useState<Layer[]>(initialLayers);
  const [activeLayerId, setActiveLayerId] = useState<string>(initialLayers[0].id);
  const [showLayersPanel, setShowLayersPanel] = useState(false);
  const [showPerformanceMetrics, setShowPerformanceMetrics] = useState(false);
  const [showCollaborationPanel, setShowCollaborationPanel] = useState(false);
  const [performanceData, setPerformanceData] = useState<PerformanceData>({
    fps: 0,
    renderTime: 0,
    collaborationLatency: 0,
    shapeCount: 0,
  });
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Filter shapes by visible layers
  const visibleShapes = useMemo(() => {
    const visibleLayerIds = layers.filter(layer => layer.visible).map(layer => layer.id);
    return history.present.filter(shape => !shape.layerId || visibleLayerIds.includes(shape.layerId));
  }, [history.present, layers]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        setStageSize({
          width: containerRef.current.offsetWidth,
          height: containerRef.current.offsetHeight,
        });
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Update transformer on selection change
  useEffect(() => {
    if (selectedId && transformerRef.current) {
      const node = stageRef.current?.findOne(`#${selectedId}`);
      if (node) {
        transformerRef.current.nodes([node]);
        transformerRef.current.getLayer().batchDraw();
      }
    }
  }, [selectedId]);

  // Set up initial yjs connection
  useEffect(() => {
    if (provider) {
      setIsLoading(true);
      
      // Get initial data from Yjs
      try {
        const syncedShapes = provider.getData('shapes') as Record<string, any>;
        const syncedLayers = provider.getData('layers') as Record<string, any>;
        
        if (Object.keys(syncedShapes).length > 0) {
          // Convert to array
          const shapesArray = Object.entries(syncedShapes).map(([id, data]) => ({
            id,
            ...data,
          })) as Shape[];
          
          if (shapesArray.length > 0) {
            setHistory((prev) => ({
              ...prev,
              present: shapesArray,
            }));
          }
        } else {
          // Broadcast initial shapes
          initialShapes.forEach(shape => {
            provider.broadcastUpdate(`shapes/${shape.id}`, shape);
          });
        }
        
        if (Object.keys(syncedLayers).length > 0) {
          // Convert to array
          const layersArray = Object.entries(syncedLayers).map(([id, data]) => ({
            id,
            ...data,
          })) as Layer[];
          
          if (layersArray.length > 0) {
            setLayers(layersArray);
          }
        } else {
          // Broadcast initial layers
          initialLayers.forEach(layer => {
            provider.broadcastUpdate(`layers/${layer.id}`, layer);
          });
        }
      } catch (error) {
        console.error('Error getting initial data from Yjs:', error);
      }
      
      // Listen for connection changes
      const unsubscribeConnection = provider.onConnectionChange(isConnected => {
        setIsConnected(isConnected);
        setIsLoading(false);
      });
      
      // Listen for updates
      const unsubscribeUpdates = provider.onUpdate(() => {
        try {
          // Get updated shapes
          const syncedShapes = provider.getData('shapes') as Record<string, any>;
          if (Object.keys(syncedShapes).length > 0) {
            const shapesArray = Object.entries(syncedShapes).map(([id, data]) => ({
              id,
              ...data,
            })) as Shape[];
            
            setHistory((prev) => ({
              ...prev,
              present: shapesArray,
            }));
          }
          
          // Get updated layers
          const syncedLayers = provider.getData('layers') as Record<string, any>;
          if (Object.keys(syncedLayers).length > 0) {
            const layersArray = Object.entries(syncedLayers).map(([id, data]) => ({
              id,
              ...data,
            })) as Layer[];
            
            setLayers(layersArray);
          }
        } catch (error) {
          console.error('Error processing update from Yjs:', error);
        }
      });
      
      // Clean up
      return () => {
        unsubscribeConnection();
        unsubscribeUpdates();
      };
    }
  }, [provider, initialShapes, initialLayers]);

  // Set up performance monitoring
  useEffect(() => {
    if (showPerformanceMetrics) {
      performanceIntervalRef.current = setInterval(() => {
        const perfReport = canvasPerformance.generateReport();
        
        // Calculate metrics
        const renderTimeMetrics = perfReport.metrics.filter(m => m.name.startsWith('render'));
        const avgRenderTime = renderTimeMetrics.length > 0
          ? renderTimeMetrics.reduce((sum, m) => sum + (m.duration || 0), 0) / renderTimeMetrics.length
          : 0;
        
        const collaborationMetrics = perfReport.metrics.filter(m => m.name.startsWith('collaboration'));
        const avgCollabLatency = collaborationMetrics.length > 0
          ? collaborationMetrics.reduce((sum, m) => sum + (m.duration || 0), 0) / collaborationMetrics.length
          : 0;
        
        // Calculate FPS
        const fps = avgRenderTime > 0 ? Math.min(60, Math.round(1000 / avgRenderTime)) : 60;
        
        setPerformanceData({
          fps,
          renderTime: Math.round(avgRenderTime),
          collaborationLatency: Math.round(avgCollabLatency),
          shapeCount: history.present.length,
        });
        
        // Clear old metrics
        canvasPerformance.clearMetrics();
      }, 1000);
    } else if (performanceIntervalRef.current) {
      clearInterval(performanceIntervalRef.current);
      performanceIntervalRef.current = null;
    }
    
    return () => {
      if (performanceIntervalRef.current) {
        clearInterval(performanceIntervalRef.current);
      }
    };
  }, [showPerformanceMetrics, history.present.length]);

  // Track cursor position for collaboration
  useEffect(() => {
    if (provider && stageRef.current) {
      const handleMouseMove = (e: MouseEvent) => {
        if (!stageRef.current) return;
        
        const stage = stageRef.current;
        const pos = stage.getPointerPosition();
        if (pos) {
          provider.updateCursor(pos.x, pos.y);
        }
      };
      
      stageRef.current.container().addEventListener('mousemove', handleMouseMove);
      
      return () => {
        if (stageRef.current) {
          stageRef.current.container().removeEventListener('mousemove', handleMouseMove);
        }
      };
    }
  }, [provider]);

  // History management with Yjs integration
  const pushToHistory = useCallback((shapes: Shape[]) => {
    // Update local state
    setHistory((prev) => ({
      past: [...prev.past, prev.present],
      present: shapes,
      future: [],
    }));
    
    // Broadcast to Yjs
    if (provider) {
      shapes.forEach(shape => {
        provider.broadcastUpdate(`shapes/${shape.id}`, shape);
      });
    }
  }, [provider]);

  const undo = () => {
    setHistory((prev) => {
      if (prev.past.length === 0) return prev;
      const newPast = [...prev.past];
      const newPresent = newPast.pop()!;
      
      // Broadcast to Yjs
      if (provider) {
        newPresent.forEach(shape => {
          provider.broadcastUpdate(`shapes/${shape.id}`, shape);
        });
      }
      
      return {
        past: newPast,
        present: newPresent,
        future: [prev.present, ...prev.future],
      };
    });
  };

  const redo = () => {
    setHistory((prev) => {
      if (prev.future.length === 0) return prev;
      const newFuture = [...prev.future];
      const newPresent = newFuture.shift()!;
      
      // Broadcast to Yjs
      if (provider) {
        newPresent.forEach(shape => {
          provider.broadcastUpdate(`shapes/${shape.id}`, shape);
        });
      }
      
      return {
        past: [...prev.past, prev.present],
        present: newPresent,
        future: newFuture,
      };
    });
  };

  // Shape management
  const addShape = (type: 'rect' | 'circle' | 'text') => {
    const newShape: Shape = {
      id: Date.now().toString(),
      type,
      x: Math.random() * (stageSize.width - 100),
      y: Math.random() * (stageSize.height - 100),
      fill: COLORS[Math.floor(Math.random() * COLORS.length)],
      isDragging: false,
      isSelected: false,
      layerId: activeLayerId,
    };

    if (type === 'rect') {
      newShape.width = 100;
      newShape.height = 100;
    } else if (type === 'circle') {
      newShape.radius = 50;
    } else if (type === 'text') {
      newShape.text = 'Double click to edit';
      newShape.fontSize = 24;
    }

    const newShapes = [...history.present, newShape];
    pushToHistory(newShapes);
  };

  const handleDragStart = (id: string) => {
    // Check if shape is on a locked layer
    const shape = history.present.find(s => s.id === id);
    if (shape?.layerId) {
      const layer = layers.find(l => l.id === shape.layerId);
      if (layer?.locked) return;
    }
    
    const shapes = history.present.map((shape) => ({
      ...shape,
      isDragging: shape.id === id,
    }));
    setHistory({ ...history, present: shapes });
  };

  const handleDragEnd = (id: string, e: KonvaEventObject<DragEvent>) => {
    const shapes = history.present.map((shape) =>
      shape.id === id
        ? {
            ...shape,
            isDragging: false,
            x: e.target.x(),
            y: e.target.y(),
          }
        : shape
    );
    pushToHistory(shapes);
  };

  const handleSelect = (id: string | null) => {
    if (id === null) {
      setSelectedId(null);
      const shapes = history.present.map((shape) => ({
        ...shape,
        isSelected: false,
      }));
      setHistory({ ...history, present: shapes });
      return;
    }
    
    // Check if shape is on a locked layer
    const shape = history.present.find(s => s.id === id);
    if (shape?.layerId) {
      const layer = layers.find(l => l.id === shape.layerId);
      if (layer?.locked) return;
    }
    
    setSelectedId(id);
    const shapes = history.present.map((shape) => ({
      ...shape,
      isSelected: shape.id === id,
    }));
    setHistory({ ...history, present: shapes });
  };

  const handleDelete = () => {
    if (selectedId) {
      // Check if shape is on a locked layer
      const shape = history.present.find(s => s.id === selectedId);
      if (shape?.layerId) {
        const layer = layers.find(l => l.id === shape.layerId);
        if (layer?.locked) return;
      }
      
      const newShapes = history.present.filter((shape) => shape.id !== selectedId);
      pushToHistory(newShapes);
      setSelectedId(null);
    }
  };

  const handleExport = () => {
    if (stageRef.current) {
      const dataURL = stageRef.current.toDataURL();
      const link = document.createElement('a');
      link.href = dataURL;
      link.download = 'canvas.png';
      link.click();
    }
  };

  // Layer management
  const toggleLayerVisibility = (layerId: string) => {
    const updatedLayers = layers.map(layer => 
      layer.id === layerId ? { ...layer, visible: !layer.visible } : layer
    );
    setLayers(updatedLayers);
    
    // Broadcast to Yjs
    if (provider) {
      const layer = updatedLayers.find(l => l.id === layerId);
      if (layer) {
        provider.broadcastUpdate(`layers/${layerId}`, layer);
      }
    }
  };

  const toggleLayerLock = (layerId: string) => {
    const updatedLayers = layers.map(layer => 
      layer.id === layerId ? { ...layer, locked: !layer.locked } : layer
    );
    setLayers(updatedLayers);
    
    // Broadcast to Yjs
    if (provider) {
      const layer = updatedLayers.find(l => l.id === layerId);
      if (layer) {
        provider.broadcastUpdate(`layers/${layerId}`, layer);
      }
    }
  };

  const addLayer = () => {
    const newLayer: Layer = {
      id: `layer-${Date.now()}`,
      name: `Layer ${layers.length + 1}`,
      visible: true,
      locked: false,
    };
    
    const updatedLayers = [...layers, newLayer];
    setLayers(updatedLayers);
    setActiveLayerId(newLayer.id);
    
    // Broadcast to Yjs
    if (provider) {
      provider.broadcastUpdate(`layers/${newLayer.id}`, newLayer);
    }
  };

  const deleteLayer = (layerId: string) => {
    // Don't delete if it's the only layer
    if (layers.length <= 1) return;
    
    const updatedLayers = layers.filter(layer => layer.id !== layerId);
    setLayers(updatedLayers);
    
    // Update active layer if the deleted layer was active
    if (activeLayerId === layerId) {
      setActiveLayerId(updatedLayers[0].id);
    }
    
    // Update shapes to remove them from deleted layer
    const updatedShapes = history.present.filter(shape => shape.layerId !== layerId);
    if (updatedShapes.length !== history.present.length) {
      pushToHistory(updatedShapes);
    }
    
    // Broadcast to Yjs
    if (provider) {
      // Removed from provider by not updating
    }
  };

  // Render
  canvasPerformance.startMetric('render', { shapeCount: visibleShapes.length });
  
  // Performance impact of rendering cursor indicators
  const renderCursors = showCollaborationPanel && connectedUsers.length > 0;
  
  // Create the verification layer
  const renderVerificationLayer = () => {
    if (!verificationStatus.isVerified || !verificationStatus.showVerificationLayer) return null;
    
    // Create a translucent overlay with a subtle green border
    return (
      <Layer>
        {/* Translucent green overlay */}
        <Rect
          x={0}
          y={0}
          width={stageSize.width}
          height={stageSize.height}
          fill="rgba(0, 255, 0, 0.03)"
          stroke="rgba(0, 200, 0, 0.5)"
          strokeWidth={4}
          perfectDrawEnabled={false}
          listening={false}
        />
        
        {/* Verification Badge in top right corner */}
        <Group x={stageSize.width - 160} y={10}>
          <Rect
            width={150}
            height={70}
            cornerRadius={5}
            fill="rgba(240, 255, 240, 0.9)"
            stroke="rgba(0, 150, 0, 0.7)"
            strokeWidth={1}
            shadowColor="rgba(0,0,0,0.3)"
            shadowBlur={5}
            shadowOffset={{ x: 2, y: 2 }}
            shadowOpacity={0.3}
          />
          <Circle
            x={25}
            y={35}
            radius={15}
            fill="rgba(0, 180, 0, 0.2)"
          />
          <Text
            x={50}
            y={20}
            text="Verified Content"
            fontSize={14}
            fontStyle="bold"
            fill="rgba(0, 120, 0, 1)"
          />
          {verificationStatus.certificateData && (
            <Text
              x={50}
              y={40}
              text={`ID: ${verificationStatus.certificateData.id.substring(0, 8)}...`}
              fontSize={10}
              fill="rgba(0, 100, 0, 0.7)"
            />
          )}
          <Text
            x={10}
            y={55}
            text={`Verified: ${verificationStatus.certificateData?.timestamp ? 
              new Date(verificationStatus.certificateData.timestamp).toLocaleDateString() :
              new Date().toLocaleDateString()}`}
            fontSize={10}
            fill="rgba(0, 100, 0, 0.7)"
          />
        </Group>
      </Layer>
    );
  };

  const stageContent = (
    <Stage
      ref={stageRef}
      width={stageSize.width}
      height={stageSize.height}
      onClick={(e) => {
        canvasPerformance.startMetric('interaction.click');
        const clickedOnEmpty = e.target === e.target.getStage();
        if (clickedOnEmpty) {
          handleSelect(null);
        }
        canvasPerformance.endMetric('interaction.click');
      }}
      onMouseMove={(e) => {
        if (provider && stageRef.current) {
          const pos = stageRef.current.getPointerPosition();
          if (pos) {
            provider.updateCursor(pos.x, pos.y);
          }
        }
      }}
    >
      <Layer>
        {visibleShapes.map((shape) => {
          if (shape.type === 'rect') {
            return (
              <Rect
                key={shape.id}
                id={shape.id}
                x={shape.x}
                y={shape.y}
                width={shape.width}
                height={shape.height}
                fill={shape.fill}
                draggable={!readonly}
                onClick={() => handleSelect(shape.id)}
                onDragStart={() => handleDragStart(shape.id)}
                onDragEnd={(e) => handleDragEnd(shape.id, e)}
                onTap={() => handleSelect(shape.id)}
              />
            );
          } else if (shape.type === 'circle') {
            return (
              <Circle
                key={shape.id}
                id={shape.id}
                x={shape.x}
                y={shape.y}
                radius={shape.radius}
                fill={shape.fill}
                draggable={!readonly}
                onClick={() => handleSelect(shape.id)}
                onDragStart={() => handleDragStart(shape.id)}
                onDragEnd={(e) => handleDragEnd(shape.id, e)}
                onTap={() => handleSelect(shape.id)}
              />
            );
          } else if (shape.type === 'text') {
            return (
              <Text
                key={shape.id}
                id={shape.id}
                x={shape.x}
                y={shape.y}
                text={shape.text}
                fontSize={shape.fontSize}
                fill={shape.fill}
                draggable={!readonly}
                onClick={() => handleSelect(shape.id)}
                onDragStart={() => handleDragStart(shape.id)}
                onDragEnd={(e) => handleDragEnd(shape.id, e)}
                onTap={() => handleSelect(shape.id)}
                onDblClick={(e) => {
                  if (readonly) return;
                  
                  // Check if text is on a locked layer
                  const textShape = history.present.find(s => s.id === shape.id);
                  if (textShape?.layerId) {
                    const layer = layers.find(l => l.id === textShape.layerId);
                    if (layer?.locked) return;
                  }
                  
                  const textNode = e.target;
                  const textPosition = textNode.getAbsolutePosition();
                  const stageBox = stageRef.current.container().getBoundingClientRect();
                  const areaPosition = {
                    x: stageBox.left + textPosition.x,
                    y: stageBox.top + textPosition.y,
                  };

                  const textarea = document.createElement('textarea');
                  document.body.appendChild(textarea);

                  textarea.value = textNode.text();
                  textarea.style.position = 'absolute';
                  textarea.style.top = `${areaPosition.y}px`;
                  textarea.style.left = `${areaPosition.x}px`;
                  textarea.style.width = `${textNode.width()}px`;
                  textarea.style.height = `${textNode.height()}px`;
                  textarea.style.fontSize = `${textNode.fontSize()}px`;
                  textarea.style.border = 'none';
                  textarea.style.padding = '0px';
                  textarea.style.margin = '0px';
                  textarea.style.overflow = 'hidden';
                  textarea.style.background = 'none';
                  textarea.style.outline = 'none';
                  textarea.style.resize = 'none';
                  textarea.style.lineHeight = textNode.lineHeight();
                  textarea.style.fontFamily = textNode.fontFamily();
                  textarea.style.transformOrigin = 'left top';
                  textarea.style.textAlign = textNode.align();
                  textarea.style.color = textNode.fill();

                  textarea.focus();

                  textarea.addEventListener('keydown', function (e) {
                    if (e.keyCode === 13 && !e.shiftKey) {
                      textNode.text(textarea.value);
                      document.body.removeChild(textarea);
                      
                      // Update shape in history and Yjs
                      const updatedShapes = history.present.map(s => 
                        s.id === shape.id 
                          ? { ...s, text: textarea.value } 
                          : s
                      );
                      pushToHistory(updatedShapes);
                    }
                  });

                  textarea.addEventListener('blur', function () {
                    textNode.text(textarea.value);
                    document.body.removeChild(textarea);
                    
                    // Update shape in history and Yjs
                    const updatedShapes = history.present.map(s => 
                      s.id === shape.id 
                        ? { ...s, text: textarea.value } 
                        : s
                    );
                    pushToHistory(updatedShapes);
                  });
                }}
              />
            );
          }
          return null;
        })}
        
        {/* Render other users' cursors */}
        {renderCursors && connectedUsers
          .filter(user => user.id !== userId && user.cursor)
          .map(user => (
            <React.Fragment key={user.id}>
              <Circle
                x={user.cursor?.x}
                y={user.cursor?.y}
                radius={5}
                fill={user.color}
              />
              <Text
                x={user.cursor?.x + 10}
                y={user.cursor?.y - 10}
                text={user.name}
                fontSize={12}
                fill={user.color}
              />
            </React.Fragment>
          ))
        }
        
        {!readonly && selectedId && (
          <Transformer
            ref={transformerRef}
            boundBoxFunc={(oldBox, newBox) => {
              // Limit resize
              const minSize = 20;
              const maxSize = Math.min(stageSize.width, stageSize.height);
              if (
                newBox.width < minSize ||
                newBox.height < minSize ||
                newBox.width > maxSize ||
                newBox.height > maxSize
              ) {
                return oldBox;
              }
              return newBox;
            }}
            onTransformEnd={() => {
              const node = stageRef.current?.findOne(`#${selectedId}`);
              if (!node) return;
              
              // Get new position and size
              const scaleX = node.scaleX();
              const scaleY = node.scaleY();
              
              // Reset scale to avoid compounding
              node.scaleX(1);
              node.scaleY(1);
              
              const updatedShapes = history.present.map((shape) => {
                if (shape.id !== selectedId) return shape;
                
                if (shape.type === 'rect') {
                  return {
                    ...shape,
                    x: node.x(),
                    y: node.y(),
                    width: Math.max(5, node.width() * scaleX),
                    height: Math.max(5, node.height() * scaleY),
                  };
                } else if (shape.type === 'circle') {
                  return {
                    ...shape,
                    x: node.x(),
                    y: node.y(),
                    radius: Math.max(5, shape.radius! * scaleX),
                  };
                } else if (shape.type === 'text') {
                  return {
                    ...shape,
                    x: node.x(),
                    y: node.y(),
                    fontSize: Math.max(5, shape.fontSize! * scaleY),
                  };
                }
                return shape;
              });
              
              pushToHistory(updatedShapes);
            }}
          />
        )}
      </Layer>
      
      {/* Add verification overlay if enabled */}
      {renderVerificationLayer()}
    </Stage>
  );
  
  canvasPerformance.endMetric('render');

  return (
    <div className="flex flex-col space-y-4" aria-label="Interactive canvas editor">
      {/* Toolbar */}
      <div className="flex items-center justify-between" role="toolbar" aria-label="Canvas tools">
        <div className="flex items-center space-x-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={undo}
            disabled={history.past.length === 0 || readonly}
            aria-label="Undo"
          >
            <Undo2 className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={redo}
            disabled={history.future.length === 0 || readonly}
            aria-label="Redo"
          >
            <Redo2 className="h-4 w-4" />
          </Button>
          <div className="h-6 w-px bg-gray-200 dark:bg-gray-700" role="separator" />
          {!readonly && (
            <>
              <Button
                variant={tool === 'rect' ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => {
                  setTool('rect');
                  addShape('rect');
                }}
                aria-label="Add rectangle"
              >
                <Square className="h-4 w-4" />
              </Button>
              <Button
                variant={tool === 'circle' ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => {
                  setTool('circle');
                  addShape('circle');
                }}
                aria-label="Add circle"
              >
                <CircleIcon className="h-4 w-4" />
              </Button>
              <Button
                variant={tool === 'text' ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => {
                  setTool('text');
                  addShape('text');
                }}
                aria-label="Add text"
              >
                <Type className="h-4 w-4" />
              </Button>
              <div className="h-6 w-px bg-gray-200 dark:bg-gray-700" role="separator" />
              <Button
                variant="ghost"
                size="sm"
                onClick={handleDelete}
                disabled={!selectedId}
                aria-label="Delete selected shape"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleExport}
            aria-label="Export canvas"
          >
            <Download className="h-4 w-4" />
          </Button>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button
            variant={showLayersPanel ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setShowLayersPanel(!showLayersPanel)}
            aria-label="Toggle layers panel"
          >
            <Layers className="h-4 w-4" />
          </Button>
          {verificationStatus.isVerified && (
            <Button
              variant={verificationStatus.showVerificationLayer ? 'primary' : 'ghost'}
              size="sm"
              onClick={onToggleVerificationLayer}
              aria-label="Toggle verification layer"
              className={verificationStatus.isVerified ? 'text-green-500' : ''}
            >
              {verificationStatus.isVerified ? 
                <ShieldCheck className={`h-4 w-4 ${verificationStatus.showVerificationLayer ? 'text-white' : 'text-green-500'}`} /> : 
                <Shield className="h-4 w-4" />
              }
            </Button>
          )}
          <Button
            variant={showPerformanceMetrics ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setShowPerformanceMetrics(!showPerformanceMetrics)}
            aria-label="Toggle performance metrics"
          >
            <Activity className="h-4 w-4" />
          </Button>
          <Button
            variant={showCollaborationPanel ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setShowCollaborationPanel(!showCollaborationPanel)}
            aria-label="Toggle collaboration panel"
          >
            <Users className="h-4 w-4" />
          </Button>
          {isConnected ? (
            <UserCheck className="h-4 w-4 text-green-500" />
          ) : (
            <Loader className="h-4 w-4 animate-spin text-orange-500" />
          )}
        </div>
      </div>

      <div className="flex">
        {/* Main Canvas */}
        <div
          ref={containerRef}
          className="relative h-[600px] flex-grow overflow-hidden rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800"
          role="region"
          aria-label="Canvas workspace"
        >
          {isLoading ? (
            <div className="flex h-full w-full items-center justify-center">
              <Loader className="h-10 w-10 animate-spin text-blue-500" />
              <span className="ml-2 text-lg">Loading canvas...</span>
            </div>
          ) : (
            stageContent
          )}
          
          {/* Performance metrics overlay */}
          {showPerformanceMetrics && (
            <div className="absolute bottom-2 right-2 rounded bg-black/70 p-2 text-xs text-white">
              <p><strong>FPS:</strong> {performanceData.fps}</p>
              <p><strong>Render time:</strong> {performanceData.renderTime}ms</p>
              <p><strong>Collaboration latency:</strong> {performanceData.collaborationLatency}ms</p>
              <p><strong>Shape count:</strong> {performanceData.shapeCount}</p>
              <p><strong>Connected users:</strong> {connectedUsers.length}</p>
            </div>
          )}
        </div>
        
        {/* Layers panel */}
        {showLayersPanel && (
          <div className="ml-4 w-60 rounded-lg border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-800">
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-medium">Layers</h3>
              {!readonly && (
                <Button
                  variant="ghost" 
                  size="sm" 
                  onClick={addLayer}
                  aria-label="Add new layer"
                >
                  +
                </Button>
              )}
            </div>
            <div className="space-y-2">
              {layers.map((layer) => (
                <div
                  key={layer.id}
                  className={`flex items-center justify-between rounded p-2 ${
                    activeLayerId === layer.id ? 'bg-blue-100 dark:bg-blue-900' : ''
                  }`}
                  onClick={() => !readonly && setActiveLayerId(layer.id)}
                >
                  <div className="flex items-center">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="p-0"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleLayerVisibility(layer.id);
                      }}
                      aria-label={`${layer.visible ? 'Hide' : 'Show'} layer ${layer.name}`}
                    >
                      {layer.visible ? (
                        <Eye className="h-4 w-4" />
                      ) : (
                        <EyeOff className="h-4 w-4" />
                      )}
                    </Button>
                    <span className="ml-2 text-sm">{layer.name}</span>
                  </div>
                  <div className="flex space-x-1">
                    {!readonly && (
                      <>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="p-0"
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleLayerLock(layer.id);
                          }}
                          aria-label={`${layer.locked ? 'Unlock' : 'Lock'} layer ${layer.name}`}
                        >
                          {layer.locked ? '🔒' : '🔓'}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="p-0"
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteLayer(layer.id);
                          }}
                          aria-label={`Delete layer ${layer.name}`}
                          disabled={layers.length <= 1}
                        >
                          ❌
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Collaboration panel */}
        {showCollaborationPanel && (
          <div className="ml-4 w-60 rounded-lg border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-800">
            <h3 className="mb-2 text-sm font-medium">Collaborators ({connectedUsers.length})</h3>
            <div className="space-y-2">
              {connectedUsers.map((user) => (
                <div key={user.id} className="flex items-center">
                  <div
                    className="mr-2 h-3 w-3 rounded-full"
                    style={{ backgroundColor: user.color }}
                  ></div>
                  <span className="text-sm">
                    {user.name} {user.id === userId && '(you)'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
