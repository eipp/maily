'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Stage, Layer, Rect, Circle, Text, Transformer } from 'react-konva';
import type { KonvaEventObject } from 'konva/lib/Node';
import type Konva from 'konva';
import { Undo2, Redo2, Download, Square, Circle as CircleIcon, Type, Trash2 } from 'lucide-react';
import { Button } from '@/components/Button';

// Types
interface Shape {
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
}

interface HistoryState {
  past: Shape[][];
  present: Shape[];
  future: Shape[][];
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
  },
];

export function Canvas() {
  // Refs
  const stageRef = useRef<Konva.Stage>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const transformerRef = useRef<Konva.Transformer>(null);

  // State
  const [stageSize, setStageSize] = useState({ width: 800, height: 600 });
  const [history, setHistory] = useState<HistoryState>({
    past: [],
    present: INITIAL_SHAPES,
    future: [],
  });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [tool, setTool] = useState<'select' | 'rect' | 'circle' | 'text'>('select');

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

  // History management
  const pushToHistory = useCallback((shapes: Shape[]) => {
    setHistory((prev) => ({
      past: [...prev.past, prev.present],
      present: shapes,
      future: [],
    }));
  }, []);

  const undo = () => {
    setHistory((prev) => {
      if (prev.past.length === 0) return prev;
      const newPast = [...prev.past];
      const newPresent = newPast.pop()!;
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
    setSelectedId(id);
    const shapes = history.present.map((shape) => ({
      ...shape,
      isSelected: shape.id === id,
    }));
    setHistory({ ...history, present: shapes });
  };

  const handleDelete = () => {
    if (selectedId) {
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

  return (
    <div className="flex flex-col space-y-4" aria-label="Interactive canvas editor">
      {/* Toolbar */}
      <div className="flex items-center space-x-2" role="toolbar" aria-label="Canvas tools">
        <Button
          variant="ghost"
          size="sm"
          onClick={undo}
          disabled={history.past.length === 0}
          aria-label="Undo"
        >
          <Undo2 className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={redo}
          disabled={history.future.length === 0}
          aria-label="Redo"
        >
          <Redo2 className="h-4 w-4" />
        </Button>
        <div className="h-6 w-px bg-gray-200 dark:bg-gray-700" role="separator" />
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
        <Button
          variant="ghost"
          size="sm"
          onClick={handleExport}
          aria-label="Export canvas"
        >
          <Download className="h-4 w-4" />
        </Button>
      </div>

      {/* Canvas */}
      <div
        ref={containerRef}
        className="relative h-[600px] w-full overflow-hidden rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800"
        role="region"
        aria-label="Canvas workspace"
      >
        <Stage
          ref={stageRef}
          width={stageSize.width}
          height={stageSize.height}
          onClick={(e) => {
            const clickedOnEmpty = e.target === e.target.getStage();
            if (clickedOnEmpty) {
              handleSelect(null);
            }
          }}
        >
          <Layer>
            {history.present.map((shape) => {
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
                    draggable
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
                    draggable
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
                    draggable
                    onClick={() => handleSelect(shape.id)}
                    onDragStart={() => handleDragStart(shape.id)}
                    onDragEnd={(e) => handleDragEnd(shape.id, e)}
                    onTap={() => handleSelect(shape.id)}
                    onDblClick={(e) => {
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
                        }
                      });

                      textarea.addEventListener('blur', function () {
                        textNode.text(textarea.value);
                        document.body.removeChild(textarea);
                      });
                    }}
                  />
                );
              }
              return null;
            })}
            {selectedId && (
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
              />
            )}
          </Layer>
        </Stage>
      </div>
    </div>
  );
}
