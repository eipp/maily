'use client';

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useSession } from 'next-auth/react';
import { nanoid } from 'nanoid';
import {
  Square,
  Circle as CircleIcon,
  Type,
  Pencil,
  Hand,
  Eraser,
  Move,
  Users,
  Download,
  Share2,
  Save
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Slider } from '@/components/ui/slider';
import { HexColorPicker } from 'react-colorful';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useTheme } from 'next-themes';

import { Canvas } from './Canvas';
import { Shapes, Shape } from './Shapes';
import { useOptimizedCollaboration, useThrottledCursorUpdate } from '@/hooks/useOptimizedCollaboration';
import { canvasPerformance } from '@/utils/canvasPerformance';

// Define tool types
type ToolType = 'select' | 'rectangle' | 'circle' | 'line' | 'text' | 'freehand' | 'eraser' | 'hand';

interface CollaborativeCanvasProps {
  canvasId: string;
  initialState?: string;
  onSave?: (state: string) => void;
  readOnly?: boolean;
  highContrastMode?: boolean;
}

// Define color options
const COLORS = [
  '#FF5733', // Red
  '#33FF57', // Green
  '#3357FF', // Blue
  '#F3FF33', // Yellow
  '#FF33F3', // Pink
  '#33FFF3', // Cyan
  '#FF8C33', // Orange
  '#8C33FF', // Purple
];

// User cursor component
const UserCursor: React.FC<{
  user: any;
  scale: number;
}> = ({ user, scale }) => {
  if (!user.cursor) return null;

  return (
    <div
      className="absolute pointer-events-none z-50 flex flex-col items-center"
      style={{
        left: user.cursor.x,
        top: user.cursor.y,
        transform: 'translate(-50%, -50%)'
      }}
    >
      <div
        className="w-3 h-3 rounded-full mb-1"
        style={{ backgroundColor: user.color || '#FF5733' }}
      />
      <div
        className="px-2 py-1 text-xs rounded-md text-white"
        style={{
          backgroundColor: user.color || '#FF5733',
          transform: `scale(${1 / Math.max(0.5, scale)})`,
          transformOrigin: 'top center'
        }}
      >
        {user.name || 'Anonymous'}
      </div>
    </div>
  );
};

// Presence list component
const PresenceList: React.FC<{
  users: any[];
}> = ({ users }) => {
  return (
    <Popover>
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <PopoverTrigger asChild>
              <Button variant="outline" size="icon" className="relative">
                <Users className="h-4 w-4" />
                {users.length > 0 && (
                  <span className="absolute -top-1 -right-1 bg-primary text-primary-foreground text-xs rounded-full w-4 h-4 flex items-center justify-center">
                    {users.length}
                  </span>
                )}
              </Button>
            </PopoverTrigger>
          </TooltipTrigger>
          <TooltipContent side="bottom">
            <p>Connected Users</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      <PopoverContent className="w-80">
        <h3 className="font-medium mb-2">Connected Users</h3>
        <ScrollArea className="h-60">
          <div className="space-y-2">
            {users.length === 0 ? (
              <div className="text-sm text-muted-foreground">No other users connected</div>
            ) : (
              users.map(user => (
                <div key={user.clientId} className="flex items-center gap-2 p-2 rounded-md hover:bg-muted">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback style={{ backgroundColor: user.color || '#FF5733' }}>
                      {user.name?.charAt(0) || 'A'}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <div className="text-sm font-medium">{user.name || 'Anonymous'}</div>
                    <div className="text-xs text-muted-foreground">Active</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </PopoverContent>
    </Popover>
  );
};

/**
 * CollaborativeCanvas component
 *
 * An optimized version of the CollaborativeCanvas component that uses:
 * - Virtualization for large canvas documents
 * - Efficient Yjs implementation for real-time collaboration
 * - Throttling for high-frequency collaborative updates
 * - Performance monitoring
 */
export const CollaborativeCanvas: React.FC<CollaborativeCanvasProps> = ({
  canvasId,
  initialState,
  onSave,
  readOnly = false,
  highContrastMode = false,
}) => {
  const { data: session } = useSession();
  const userId = session?.user?.id || 'anonymous';
  const userName = session?.user?.name || 'Anonymous';

  // Canvas state
  const [shapes, setShapes] = useState<Shape[]>([]);
  const [selectedShapeIds, setSelectedShapeIds] = useState<string[]>([]);
  const [tool, setTool] = useState<ToolType>('select');
  const [color, setColor] = useState('#000000');
  const [strokeWidth, setStrokeWidth] = useState(2);
  const [isDrawing, setIsDrawing] = useState(false);
  const [scale, setScale] = useState(1);
  const [viewportData, setViewportData] = useState<any>(null);
  const [textEditingId, setTextEditingId] = useState<string | null>(null);
  const [pendingText, setPendingText] = useState('');
  const [textPosition, setTextPosition] = useState({ x: 0, y: 0 });
  const [isSaving, setIsSaving] = useState(false);

  // Refs
  const textInputRef = useRef<HTMLTextAreaElement>(null);
  const drawingPointsRef = useRef<number[]>([]);

  // Initialize collaboration
  const [collaborationState, collaborationActions] = useOptimizedCollaboration({
    serverUrl: process.env.NEXT_PUBLIC_CANVAS_WS_URL || process.env.CANVAS_WS_URL || 'wss://canvas-ws.justmaily.com',
    roomId: canvasId,
    userId,
    userName,
    updateThrottleMs: 50,
    updateDebounceMs: 200,
  });

  // Create throttled cursor update function
  const throttledUpdateCursor = useThrottledCursorUpdate(collaborationActions.updateCursor);

  // Load initial state
  useEffect(() => {
    if (initialState) {
      try {
        const parsedState = JSON.parse(initialState);
        if (Array.isArray(parsedState)) {
          setShapes(parsedState);

          // Broadcast initial state
          collaborationActions.broadcastUpdate('canvas', { shapes: parsedState });
        }
      } catch (error) {
        console.error('Failed to parse initial state:', error);
      }
    } else {
      // Try to get state from collaboration
      const collaborativeState = collaborationActions.getData('canvas');
      if (collaborativeState?.shapes) {
        setShapes(collaborativeState.shapes);
      }
    }
  }, [initialState, collaborationActions]);

  // Subscribe to shape updates
  useEffect(() => {
    const handleShapesUpdate = () => {
      const data = collaborationActions.getData('canvas');
      if (data?.shapes) {
        canvasPerformance.startMetric('collaboration.updateShapes');
        setShapes(data.shapes);
        canvasPerformance.endMetric('collaboration.updateShapes');
      }
    };

    // Set up subscription
    const unsubscribe = collaborationActions.onUpdate(handleShapesUpdate);

    return () => {
      unsubscribe();
    };
  }, [collaborationActions]);

  // Handle viewport change
  const handleViewportChange = useCallback((viewport: any) => {
    setViewportData(viewport);
    setScale(viewport.scale);

    // Update cursor position for collaboration
    if (viewport.pointerPosition) {
      throttledUpdateCursor(viewport.pointerPosition.x, viewport.pointerPosition.y);
    }
  }, [throttledUpdateCursor]);

  // Handle stage pointer move
  const handlePointerMove = useCallback((x: number, y: number) => {
    // Update cursor position for collaboration
    throttledUpdateCursor(x, y);

    // Handle drawing if in drawing mode
    if (isDrawing && (tool === 'freehand' || tool === 'line')) {
      canvasPerformance.startMetric('interaction.draw');

      // Add point to drawing
      drawingPointsRef.current.push(x, y);

      // Update the last shape with new points
      setShapes(prevShapes => {
        const newShapes = [...prevShapes];
        const lastShape = newShapes[newShapes.length - 1];

        if (lastShape && (lastShape.type === 'freehand' || lastShape.type === 'line')) {
          lastShape.points = [...drawingPointsRef.current];
        }

        return newShapes;
      });

      canvasPerformance.endMetric('interaction.draw');
    }
  }, [isDrawing, tool, throttledUpdateCursor]);

  // Handle stage pointer down
  const handlePointerDown = useCallback((x: number, y: number) => {
    if (readOnly) return;

    canvasPerformance.startMetric('interaction.pointerDown');

    // Clear selection if not in select mode
    if (tool !== 'select' && selectedShapeIds.length > 0) {
      setSelectedShapeIds([]);
    }

    // Handle different tools
    switch (tool) {
      case 'rectangle':
        // Create new rectangle
        const newRect: Shape = {
          id: nanoid(),
          type: 'rect',
          x,
          y,
          width: 1,
          height: 1,
          fill: color,
          stroke: '#000000',
          strokeWidth,
        };

        setShapes(prev => [...prev, newRect]);
        setIsDrawing(true);
        break;

      case 'circle':
        // Create new circle
        const newCircle: Shape = {
          id: nanoid(),
          type: 'circle',
          x,
          y,
          radius: 1,
          fill: color,
          stroke: '#000000',
          strokeWidth,
        };

        setShapes(prev => [...prev, newCircle]);
        setIsDrawing(true);
        break;

      case 'line':
      case 'freehand':
        // Start new line or freehand drawing
        drawingPointsRef.current = [x, y];

        const newLine: Shape = {
          id: nanoid(),
          type: tool === 'freehand' ? 'freehand' : 'line',
          x: 0,
          y: 0,
          points: [...drawingPointsRef.current],
          stroke: color,
          strokeWidth,
        };

        setShapes(prev => [...prev, newLine]);
        setIsDrawing(true);
        break;

      case 'text':
        // Create new text and start editing
        const newText: Shape = {
          id: nanoid(),
          type: 'text',
          x,
          y,
          text: '',
          fontSize: 16,
          fill: color,
        };

        setShapes(prev => [...prev, newText]);
        setTextEditingId(newText.id);
        setTextPosition({ x, y });
        setPendingText('');

        // Focus text input
        setTimeout(() => {
          if (textInputRef.current) {
            textInputRef.current.focus();
          }
        }, 10);
        break;

      case 'select':
        // Will be handled by shape click
        break;

      case 'eraser':
        // Will be handled by shape click
        break;
    }

    canvasPerformance.endMetric('interaction.pointerDown');
  }, [tool, color, strokeWidth, selectedShapeIds, readOnly]);

  // Handle stage pointer up
  const handlePointerUp = useCallback(() => {
    if (!isDrawing) return;

    canvasPerformance.startMetric('interaction.pointerUp');

    setIsDrawing(false);

    // Broadcast shapes update
    collaborationActions.broadcastUpdate('canvas', { shapes });

    canvasPerformance.endMetric('interaction.pointerUp');
  }, [isDrawing, shapes, collaborationActions]);

  // Handle shape click
  const handleShapeClick = useCallback((id: string) => {
    if (readOnly) return;

    canvasPerformance.startMetric('interaction.shapeClick');

    if (tool === 'select') {
      // Select shape
      setSelectedShapeIds([id]);
    } else if (tool === 'eraser') {
      // Erase shape
      setShapes(prev => {
        const newShapes = prev.filter(shape => shape.id !== id);

        // Broadcast shapes update
        collaborationActions.broadcastUpdate('canvas', { shapes: newShapes });

        return newShapes;
      });
    }

    canvasPerformance.endMetric('interaction.shapeClick');
  }, [tool, readOnly, collaborationActions]);

  // Handle shape drag
  const handleShapeDragStart = useCallback((id: string) => {
    if (readOnly || tool !== 'select') return;

    canvasPerformance.startMetric('interaction.shapeDrag');

    // Select shape if not already selected
    if (!selectedShapeIds.includes(id)) {
      setSelectedShapeIds([id]);
    }
  }, [selectedShapeIds, tool, readOnly]);

  // Handle shape drag end
  const handleShapeDragEnd = useCallback((id: string, x: number, y: number) => {
    if (readOnly || tool !== 'select') return;

    // Update shape position
    setShapes(prev => {
      const newShapes = prev.map(shape => {
        if (shape.id === id) {
          return { ...shape, x, y };
        }
        return shape;
      });

      // Broadcast shapes update
      collaborationActions.broadcastUpdate('canvas', { shapes: newShapes });

      return newShapes;
    });

    canvasPerformance.endMetric('interaction.shapeDrag');
  }, [tool, readOnly, collaborationActions]);

  // Handle text editing
  const handleTextEdit = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setPendingText(e.target.value);
  }, []);

  // Handle text editing key down
  const handleTextareaKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      finishTextEditing();
    }
  }, []);

  // Finish text editing
  const finishTextEditing = useCallback(() => {
    if (!textEditingId) return;

    // Update text shape
    setShapes(prev => {
      const newShapes = prev.map(shape => {
        if (shape.id === textEditingId) {
          return { ...shape, text: pendingText };
        }
        return shape;
      });

      // Broadcast shapes update
      collaborationActions.broadcastUpdate('canvas', { shapes: newShapes });

      return newShapes;
    });

    // Clear text editing state
    setTextEditingId(null);
    setPendingText('');
  }, [textEditingId, pendingText, collaborationActions]);

  // Handle save
  const handleSave = useCallback(() => {
    if (!onSave) return;

    setIsSaving(true);

    try {
      const stateJson = JSON.stringify(shapes);
      onSave(stateJson);
    } catch (error) {
      console.error('Failed to save canvas state:', error);
    } finally {
      setIsSaving(false);
    }
  }, [shapes, onSave]);

  // Handle export
  const handleExport = useCallback(() => {
    // Implementation for exporting canvas as image
    // This would typically use a canvas ref to export
    console.log('Export functionality to be implemented');
  }, []);

  // Filter shapes for virtualization
  const visibleShapes = useMemo(() => {
    if (!viewportData?.visibleRect) return shapes;

    return shapes;
  }, [shapes, viewportData]);

  // Render text editing overlay
  const renderTextEditor = () => {
    if (!textEditingId) return null;

    return (
      <div
        className="absolute z-50"
        style={{
          left: textPosition.x,
          top: textPosition.y,
          transform: 'translate(-50%, -50%)',
        }}
      >
        <textarea
          ref={textInputRef}
          value={pendingText}
          onChange={handleTextEdit}
          onKeyDown={handleTextareaKeyDown}
          onBlur={finishTextEditing}
          className="border border-primary p-2 bg-background"
          style={{
            minWidth: '100px',
            minHeight: '50px',
          }}
          autoFocus
        />
      </div>
    );
  };

  // Apply high contrast mode when it changes
  const { theme } = useTheme();
  useEffect(() => {
    // Set CSS custom properties based on high contrast mode
    const root = document.documentElement;
    if (highContrastMode) {
      root.style.setProperty('--canvas-bg-color', '#000000');
      root.style.setProperty('--canvas-text-color', '#ffffff');
    } else {
      const isDarkTheme = theme === 'dark';
      root.style.setProperty('--canvas-bg-color', isDarkTheme ? '#1a1a1a' : '#ffffff');
      root.style.setProperty('--canvas-text-color', isDarkTheme ? '#ffffff' : '#000000');
    }

    // Update existing shapes to use the new colors
    setShapes(prevShapes =>
      prevShapes.map(shape => {
        if (shape.type === 'text') {
          return {
            ...shape,
            fill: highContrastMode ? '#ffffff' : (theme === 'dark' ? '#ffffff' : '#000000')
          };
        }
        return shape;
      })
    );
  }, [highContrastMode, theme]);

  // Add keyboard navigation for accessibility
  useEffect(() => {
    const handleKeyboardNavigation = (e: KeyboardEvent) => {
      if (selectedShapeIds.length === 0) return;

      // Handle arrow keys for moving selected objects
      if (e.key.startsWith('Arrow')) {
        e.preventDefault();

        const MOVE_DISTANCE = 10;
        let deltaX = 0;
        let deltaY = 0;

        switch (e.key) {
          case 'ArrowUp':
            deltaY = -MOVE_DISTANCE;
            break;
          case 'ArrowDown':
            deltaY = MOVE_DISTANCE;
            break;
          case 'ArrowLeft':
            deltaX = -MOVE_DISTANCE;
            break;
          case 'ArrowRight':
            deltaX = MOVE_DISTANCE;
            break;
        }

        // Update shape positions
        setShapes(prevShapes => {
          const newShapes = prevShapes.map(shape => {
            if (selectedShapeIds.includes(shape.id)) {
              return {
                ...shape,
                x: shape.x + deltaX,
                y: shape.y + deltaY
              };
            }
            return shape;
          });

          // Broadcast updated shapes
          collaborationActions.broadcastUpdate('canvas', { shapes: newShapes });

          return newShapes;
        });
      }
    };

    window.addEventListener('keydown', handleKeyboardNavigation);

    return () => {
      window.removeEventListener('keydown', handleKeyboardNavigation);
    };
  }, [selectedShapeIds, collaborationActions]);

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-2 border-b">
        <div className="flex items-center space-x-1">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant={tool === 'select' ? 'default' : 'outline'}
                  size="icon"
                  onClick={() => setTool('select')}
                  disabled={readOnly}
                >
                  <Hand className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">Select</TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant={tool === 'rectangle' ? 'default' : 'outline'}
                  size="icon"
                  onClick={() => setTool('rectangle')}
                  disabled={readOnly}
                >
                  <Square className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">Rectangle</TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant={tool === 'circle' ? 'default' : 'outline'}
                  size="icon"
                  onClick={() => setTool('circle')}
                  disabled={readOnly}
                >
                  <CircleIcon className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">Circle</TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant={tool === 'line' ? 'default' : 'outline'}
                  size="icon"
                  onClick={() => setTool('line')}
                  disabled={readOnly}
                >
                  <div className="h-4 w-4 flex items-center justify-center">
                    <div className="h-0.5 w-3 bg-current transform rotate-45" />
                  </div>
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">Line</TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant={tool === 'freehand' ? 'default' : 'outline'}
                  size="icon"
                  onClick={() => setTool('freehand')}
                  disabled={readOnly}
                >
                  <Pencil className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">Freehand</TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant={tool === 'text' ? 'default' : 'outline'}
                  size="icon"
                  onClick={() => setTool('text')}
                  disabled={readOnly}
                >
                  <Type className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">Text</TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant={tool === 'eraser' ? 'default' : 'outline'}
                  size="icon"
                  onClick={() => setTool('eraser')}
                  disabled={readOnly}
                >
                  <Eraser className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">Eraser</TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <div className="h-6 w-px bg-border mx-1" />

          <Popover>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <PopoverTrigger asChild>
                    <Button variant="outline" size="icon" disabled={readOnly}>
                      <div
                        className="h-4 w-4 rounded-full border border-input"
                        style={{ backgroundColor: color }}
                      />
                    </Button>
                  </PopoverTrigger>
                </TooltipTrigger>
                <TooltipContent side="bottom">Color</TooltipContent>
              </Tooltip>
            </TooltipProvider>

            <PopoverContent className="w-auto p-3">
              <HexColorPicker color={color} onChange={setColor} />
              <div className="flex mt-2 gap-1">
                {COLORS.map(c => (
                  <div
                    key={c}
                    className="h-6 w-6 rounded-full cursor-pointer border border-input"
                    style={{ backgroundColor: c }}
                    onClick={() => setColor(c)}
                  />
                ))}
              </div>
            </PopoverContent>
          </Popover>

          <div className="flex items-center space-x-2 ml-2">
            <span className="text-sm">Stroke:</span>
            <Slider
              value={[strokeWidth]}
              min={1}
              max={20}
              step={1}
              className="w-24"
              onValueChange={values => setStrokeWidth(values[0])}
              disabled={readOnly}
            />
          </div>
        </div>

        <div className="flex items-center space-x-1">
          <PresenceList users={collaborationState.connectedUsers} />

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" size="icon" onClick={handleExport}>
                  <Download className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">Export</TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" size="icon" onClick={handleSave} disabled={isSaving || readOnly}>
                  {isSaving ? (
                    <div className="h-4 w-4 border-2 border-t-transparent border-primary rounded-full animate-spin" />
                  ) : (
                    <Save className="h-4 w-4" />
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">Save</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>

      {/* Canvas */}
      <div className="relative flex-grow">
        <Canvas
          width={800}
          height={600}
          onViewportChange={handleViewportChange}
        >
          <Shapes
            shapes={visibleShapes}
            visibleRect={viewportData?.visibleRect || { x: 0, y: 0, width: 800, height: 600 }}
            scale={scale}
            onShapeClick={handleShapeClick}
            onShapeDragStart={handleShapeDragStart}
            onShapeDragEnd={handleShapeDragEnd}
          />
        </Canvas>

        {/* Text editing overlay */}
        {renderTextEditor()}

        {/* User cursors */}
        {collaborationState.connectedUsers.map(user => (
          <UserCursor key={user.clientId} user={user} scale={scale} />
        ))}
      </div>

      <style jsx global>{`
        .canvas-container {
          background-color: var(--canvas-bg-color, #ffffff);
        }
      `}</style>
    </div>
  );
};
