'use client';

import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { Stage, Layer, Rect, Circle, Text, Transformer, Group, Image } from 'react-konva';
import type { KonvaEventObject } from 'konva/lib/Node';
import type Konva from 'konva';
import { useDrop } from 'react-dnd';
import { 
  Undo2, Redo2, Download, Square, Circle as CircleIcon, Type, Trash2,
  Layers, Eye, EyeOff, Activity, Users, UserCheck, LineChart, Loader,
  Shield, ShieldCheck, Maximize, Minimize, ZoomIn, ZoomOut
} from 'lucide-react';
import { Button } from '@/components/Button';
import { OptimizedYjsProvider } from '@/lib/optimized-yjs';
import { canvasPerformance } from '@/utils/canvasPerformance';
import { useCanvasShapeWorker } from '@/hooks/useCanvasShapeWorker';
import { useCanvasWorker } from '@/hooks/useCanvasWorker';
import { DndContext } from '@/components/DndContext';
import { LayersPanel } from '@/components/LayersPanel';
import { PerformanceMetricsPanel } from '@/components/PerformanceMetricsPanel';
import { Layer as LayerType } from '@/components/DraggableLayer';
import { createUniqueLayerName } from '@/utils/canvas';

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

interface ConnectedUser {
  id: string;
  name: string;
  color: string;
  cursor?: { x: number, y: number };
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

// For React DnD
interface DragItemShape {
  type: 'shape';
  shape: Shape;
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

const INITIAL_LAYERS: LayerType[] = [
  { id: 'layer1', name: 'Base Layer', visible: true, locked: false, opacity: 100 },
  { id: 'layer2', name: 'Text Layer', visible: true, locked: false, opacity: 100 },
  { id: 'layer3', name: 'Effects Layer', visible: true, locked: false, opacity: 100 },
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

interface EnhancedCanvasProps {
  roomId?: string;
  userId?: string;
  initialShapes?: Shape[];
  initialLayers?: LayerType[];
  readonly?: boolean;
  verificationStatus?: VerificationStatus;
  onToggleVerificationLayer?: () => void;
}

export function EnhancedCanvas({
  roomId = 'default',
  userId = `user-${Math.floor(Math.random() * 100000)}`,
  initialShapes = INITIAL_SHAPES,
  initialLayers = INITIAL_LAYERS,
  readonly = false,
  verificationStatus = { isVerified: false, showVerificationLayer: false },
  onToggleVerificationLayer,
}: EnhancedCanvasProps) {
  // Refs
  const stageRef = useRef<Konva.Stage>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const transformerRef = useRef<Konva.Transformer>(null);
  
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
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [tool, setTool] = useState<'select' | 'rect' | 'circle' | 'text'>('select');
  const [layers, setLayers] = useState<LayerType[]>(initialLayers);
  const [activeLayerId, setActiveLayerId] = useState<string>(initialLayers[0].id);
  const [showLayersPanel, setShowLayersPanel] = useState(false);
  const [showPerformanceMetrics, setShowPerformanceMetrics] = useState(false);
  const [showCollaborationPanel, setShowCollaborationPanel] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDraggingStage, setIsDraggingStage] = useState(false);

  // Filter shapes by visible layers
  const visibleShapes = useMemo(() => {
    const visibleLayerIds = layers
      .filter(layer => layer.visible)
      .map(layer => layer.id);
    
    return history.present.filter(shape => 
      !shape.layerId || visibleLayerIds.includes(shape.layerId)
    );
  }, [history.present, layers]);
  
  // Set up React DnD drop functionality for importing elements
  const [{ canDrop, isOver }, drop] = useDrop({
    accept: ['shape', 'template', 'image', 'element'],
    drop: (item: any, monitor) => {
      // Get the mouse coordinates relative to the stage
      if (!stageRef.current || !containerRef.current) return;
      
      const containerRect = containerRef.current.getBoundingClientRect();
      const dropPosition = monitor.getClientOffset();
      
      if (!dropPosition) return;
      
      // Calculate position in the stage coordinate system
      const x = (dropPosition.x - containerRect.left - position.x) / scale;
      const y = (dropPosition.y - containerRect.top - position.y) / scale;
      
      // Handle different dropped item types
      if (item.type === 'shape') {
        addShapeAtPosition(item.shapeType, x, y);
      } else if (item.type === 'image' && item.url) {
        addImageAtPosition(item.url, x, y);
      } else if (item.type === 'template' && item.shapes) {
        addShapesAtPosition(item.shapes, x, y);
      }
    },
    collect: (monitor) => ({
      isOver: monitor.isOver(),
      canDrop: monitor.canDrop(),
    }),
  });
  
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
        transformerRef.current.getLayer()?.batchDraw();
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
          })) as LayerType[];
          
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
            })) as LayerType[];
            
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
      x: Math.random() * (stageSize.width / scale - 100),
      y: Math.random() * (stageSize.height / scale - 100),
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
  
  // Add a shape at a specific position (for drag and drop)
  const addShapeAtPosition = (type: 'rect' | 'circle' | 'text', x: number, y: number) => {
    const newShape: Shape = {
      id: Date.now().toString(),
      type,
      x,
      y,
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
  
  // Add multiple shapes at once (for templates)
  const addShapesAtPosition = (shapes: Partial<Shape>[], x: number, y: number) => {
    // Calculate the center of the shapes
    let minX = Infinity, minY = Infinity;
    let maxX = -Infinity, maxY = -Infinity;
    
    shapes.forEach(shape => {
      minX = Math.min(minX, shape.x || 0);
      minY = Math.min(minY, shape.y || 0);
      maxX = Math.max(maxX, (shape.x || 0) + (shape.width || shape.radius || 0));
      maxY = Math.max(maxY, (shape.y || 0) + (shape.height || shape.radius || 0));
    });
    
    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;
    
    // Create new shapes with adjusted positions
    const newShapes = shapes.map(shape => ({
      ...shape,
      id: Date.now() + '_' + Math.random().toString(36).substr(2, 9),
      x: (shape.x || 0) - centerX + x,
      y: (shape.y || 0) - centerY + y,
      isDragging: false,
      isSelected: false,
      layerId: activeLayerId,
    })) as Shape[];
    
    pushToHistory([...history.present, ...newShapes]);
  };
  
  // Add an image at a specific position
  const addImageAtPosition = (url: string, x: number, y: number) => {
    // In a real implementation, we would load the image and create a Konva.Image
    // For now, we'll add a placeholder rectangle
    const newShape: Shape = {
      id: Date.now().toString(),
      type: 'rect',
      x,
      y,
      width: 100,
      height: 100,
      fill: '#f0f0f0',
      isDragging: false,
      isSelected: false,
      layerId: activeLayerId,
    };
    
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

  const handleSelect = (id: string | null, isMultiSelect = false) => {
    if (id === null) {
      setSelectedId(null);
      setSelectedIds([]);
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
    
    // Update selectedIds for multi-selection
    let newSelectedIds: string[] = [];
    if (isMultiSelect) {
      newSelectedIds = selectedIds.includes(id)
        ? selectedIds.filter(selectedId => selectedId !== id)
        : [...selectedIds, id];
    } else {
      newSelectedIds = [id];
    }
    
    setSelectedId(newSelectedIds.length > 0 ? newSelectedIds[0] : null);
    setSelectedIds(newSelectedIds);
    
    const shapes = history.present.map((shape) => ({
      ...shape,
      isSelected: newSelectedIds.includes(shape.id),
    }));
    setHistory({ ...history, present: shapes });
  };

  const handleDelete = () => {
    if (selectedIds.length > 0) {
      // Check if any selected shape is on a locked layer
      const canDelete = selectedIds.every(id => {
        const shape = history.present.find(s => s.id === id);
        if (shape?.layerId) {
          const layer = layers.find(l => l.id === shape.layerId);
          return !layer?.locked;
        }
        return true;
      });
      
      if (!canDelete) return;
      
      const newShapes = history.present.filter((shape) => !selectedIds.includes(shape.id));
      pushToHistory(newShapes);
      setSelectedId(null);
      setSelectedIds([]);
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
    const newLayer: LayerType = {
      id: `layer-${Date.now()}`,
      name: createUniqueLayerName(layers),
      visible: true,
      locked: false,
      opacity: 100
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
  
  // Set the opacity of a layer
  const handleLayerOpacityChange = (layerId: string, opacity: number) => {
    const updatedLayers = layers.map(layer => 
      layer.id === layerId ? { ...layer, opacity } : layer
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
  
  // Reorder layers (called from LayersPanel)
  const handleReorderLayers = (reorderedLayers: LayerType[]) => {
    setLayers(reorderedLayers);
    
    // Broadcast to Yjs
    if (provider) {
      reorderedLayers.forEach(layer => {
        provider.broadcastUpdate(`layers/${layer.id}`, layer);
      });
    }
  };
  
  // Toggle all layers visibility at once
  const handleToggleAllLayers = (visible: boolean) => {
    const updatedLayers = layers.map(layer => ({ ...layer, visible }));
    setLayers(updatedLayers);
    
    // Broadcast to Yjs
    if (provider) {
      updatedLayers.forEach(layer => {
        provider.broadcastUpdate(`layers/${layer.id}`, layer);
      });
    }
  };
  
  // Zoom controls
  const handleZoomIn = () => {
    setScale(prevScale => Math.min(5, prevScale * 1.2));
  };
  
  const handleZoomOut = () => {
    setScale(prevScale => Math.max(0.1, prevScale / 1.2));
  };
  
  const handleZoomReset = () => {
    setScale(1);
    setPosition({ x: 0, y: 0 });
  };
  
  // Wheel event for zooming
  const handleWheel = (e: KonvaEventObject<WheelEvent>) => {
    e.evt.preventDefault();
    
    // Apply zoom
    const scaleBy = 1.1;
    const oldScale = scale;
    
    // Calculate new scale
    const newScale = e.evt.deltaY < 0 ? oldScale * scaleBy : oldScale / scaleBy;
    const limitedScale = Math.max(0.1, Math.min(5, newScale));
    
    // Get pointer position
    const pointer = stageRef.current?.getPointerPosition() || { x: stageSize.width / 2, y: stageSize.height / 2 };
    
    // Calculate new position
    const mousePointTo = {
      x: (pointer.x - position.x) / oldScale,
      y: (pointer.y - position.y) / oldScale,
    };
    
    const newPos = {
      x: pointer.x - mousePointTo.x * limitedScale,
      y: pointer.y - mousePointTo.y * limitedScale,
    };
    
    setScale(limitedScale);
    setPosition(newPos);
  };
  
  // Stage drag handlers
  const handleStageDragStart = () => {
    setIsDraggingStage(true);
  };
  
  const handleStageDragEnd = (e: KonvaEventObject<DragEvent>) => {
    setIsDraggingStage(false);
    setPosition({
      x: e.target.x(),
      y: e.target.y(),
    });
  };
  
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

  // Render
  canvasPerformance.startMetric('render', { shapeCount: visibleShapes.length });
  
  // Performance impact of rendering cursor indicators
  const renderCursors = showCollaborationPanel && connectedUsers.length > 0;
  
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
      onWheel={handleWheel}
      scaleX={scale}
      scaleY={scale}
      x={position.x}
      y={position.y}
      draggable={!readonly && tool === 'select' && !selectedId}
      onDragStart={handleStageDragStart}
      onDragEnd={handleStageDragEnd}
    >
      {layers.map((layer, index) => {
        // Get shapes for this layer
        const layerShapes = visibleShapes.filter(shape => shape.layerId === layer.id);
        
        // Skip rendering if layer is not visible
        if (!layer.visible) return null;
        
        // Set opacity based on layer settings
        const opacity = layer.opacity !== undefined ? layer.opacity / 100 : 1;
        
        return (
          <Layer 
            key={layer.id} 
            opacity={opacity}
            visible={layer.visible}
            listening={!layer.locked}
          >
            {layerShapes.map((shape) => {
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
                    draggable={!readonly && !layer.locked}
                    onClick={(e) => {
                      e.evt.stopPropagation();
                      handleSelect(shape.id, e.evt.shiftKey);
                    }}
                    onDragStart={() => handleDragStart(shape.id)}
                    onDragEnd={(e) => handleDragEnd(shape.id, e)}
                    onTap={() => handleSelect(shape.id)}
                    stroke={shape.isSelected ? '#3366FF' : undefined}
                    strokeWidth={shape.isSelected ? 2 : 0}
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
                    draggable={!readonly && !layer.locked}
                    onClick={(e) => {
                      e.evt.stopPropagation();
                      handleSelect(shape.id, e.evt.shiftKey);
                    }}
                    onDragStart={() => handleDragStart(shape.id)}
                    onDragEnd={(e) => handleDragEnd(shape.id, e)}
                    onTap={() => handleSelect(shape.id)}
                    stroke={shape.isSelected ? '#3366FF' : undefined}
                    strokeWidth={shape.isSelected ? 2 : 0}
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
                    draggable={!readonly && !layer.locked}
                    onClick={(e) => {
                      e.evt.stopPropagation();
                      handleSelect(shape.id, e.evt.shiftKey);
                    }}
                    onDragStart={() => handleDragStart(shape.id)}
                    onDragEnd={(e) => handleDragEnd(shape.id, e)}
                    onTap={() => handleSelect(shape.id)}
                    stroke={shape.isSelected ? '#3366FF' : undefined}
                    strokeWidth={shape.isSelected ? 1 : 0}
                    onDblClick={(e) => {
                      if (readonly || layer.locked) return;
                      
                      const textNode = e.target;
                      const textPosition = textNode.getAbsolutePosition();
                      const stageBox = stageRef.current!.container().getBoundingClientRect();
                      
                      // Calculate position accounting for scale and position
                      const areaPosition = {
                        x: stageBox.left + textPosition.x * scale + position.x,
                        y: stageBox.top + textPosition.y * scale + position.y,
                      };

                      const textarea = document.createElement('textarea');
                      document.body.appendChild(textarea);

                      textarea.value = textNode.text();
                      textarea.style.position = 'absolute';
                      textarea.style.top = `${areaPosition.y}px`;
                      textarea.style.left = `${areaPosition.x}px`;
                      textarea.style.width = `${textNode.width() * scale}px`;
                      textarea.style.height = `${textNode.height() * scale}px`;
                      textarea.style.fontSize = `${textNode.fontSize() * scale}px`;
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
                        if (e.key === 'Enter' && !e.shiftKey) {
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
          </Layer>
        );
      })}
      
      {/* User cursors */}
      {renderCursors && (
        <Layer>
          {connectedUsers
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
        </Layer>
      )}
      
      {/* Transformer for selections */}
      {!readonly && selectedId && (
        <Layer>
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
        </Layer>
      )}
      
      {/* Add verification overlay if enabled */}
      {renderVerificationLayer()}
    </Stage>
  );
  
  canvasPerformance.endMetric('render');

  return (
    <DndContext>
      <div 
        className="flex flex-col space-y-4" 
        aria-label="Interactive canvas editor"
      >
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
                  disabled={selectedIds.length === 0}
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
          
          {/* Zoom controls */}
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleZoomOut}
              aria-label="Zoom out"
            >
              <ZoomOut className="h-4 w-4" />
            </Button>
            <span className="text-xs">{Math.round(scale * 100)}%</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleZoomIn}
              aria-label="Zoom in"
            >
              <ZoomIn className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleZoomReset}
              aria-label="Reset zoom"
            >
              <Maximize className="h-4 w-4" />
            </Button>
            <div className="h-6 w-px bg-gray-200 dark:bg-gray-700" role="separator" />
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
            ref={drop}
            className={`relative h-[600px] flex-grow overflow-hidden rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800 ${
              canDrop && isOver ? 'border-blue-500 border-2' : ''
            }`}
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
            
            {/* Drop overlay */}
            {canDrop && isOver && (
              <div className="absolute inset-0 bg-blue-100 bg-opacity-30 flex items-center justify-center">
                <p className="text-blue-700 text-lg font-medium">Drop to add to canvas</p>
              </div>
            )}
          </div>
          
          {/* Layers panel */}
          {showLayersPanel && (
            <LayersPanel
              layers={layers}
              activeLayerId={activeLayerId}
              selectedLayerIds={selectedIds.map(id => {
                const shape = history.present.find(s => s.id === id);
                return shape?.layerId || '';
              }).filter(Boolean)}
              onLayerClick={(id) => {
                setActiveLayerId(id);
              }}
              onLayerSelect={(id) => {
                setActiveLayerId(id);
                // Select all shapes in this layer
                const layerShapes = history.present.filter(s => s.layerId === id);
                const shapeIds = layerShapes.map(s => s.id);
                setSelectedIds(shapeIds);
                setSelectedId(shapeIds.length > 0 ? shapeIds[0] : null);
                
                const updatedShapes = history.present.map(shape => ({
                  ...shape,
                  isSelected: shape.layerId === id,
                }));
                setHistory({ ...history, present: updatedShapes });
              }}
              onToggleVisibility={toggleLayerVisibility}
              onToggleLock={toggleLayerLock}
              onDeleteLayer={deleteLayer}
              onAddLayer={addLayer}
              onOpacityChange={handleLayerOpacityChange}
              onReorderLayers={handleReorderLayers}
              onToggleAllLayers={handleToggleAllLayers}
              showPanel={showLayersPanel}
              onTogglePanel={() => setShowLayersPanel(!showLayersPanel)}
              readOnly={readonly}
              canvasRef={stageRef}
              className="ml-4"
            />
          )}
          
          {/* Performance Metrics Panel */}
          <PerformanceMetricsPanel
            showPanel={showPerformanceMetrics}
            onTogglePanel={() => setShowPerformanceMetrics(!showPerformanceMetrics)}
            connectedUsers={connectedUsers.length}
            shapeCount={history.present.length}
            layerCount={layers.length}
            className="ml-4"
          />
          
          {/* Collaboration Panel */}
          {showCollaborationPanel && connectedUsers.length > 0 && (
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
    </DndContext>
  );
}