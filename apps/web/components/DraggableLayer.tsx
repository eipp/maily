'use client';

import React, { useRef } from 'react';
import { useDrag, useDrop } from 'react-dnd';
import { Eye, EyeOff, Lock, Unlock, Trash2, Image, ArrowUp, ArrowDown } from 'lucide-react';
import { Button } from '@/components/Button';

// Define the layer item type for React DnD
const LAYER_ITEM_TYPE = 'LAYER';

// Interface for Layer type
export interface Layer {
  id: string;
  name: string;
  visible: boolean;
  locked: boolean;
  opacity?: number;
  thumbnail?: string; // Base64 encoded or URL
}

interface DraggableLayerProps {
  layer: Layer;
  index: number;
  isActive: boolean;
  isSelected: boolean;
  moveLayer: (dragIndex: number, hoverIndex: number) => void;
  onLayerClick: (id: string) => void;
  onToggleVisibility: (id: string) => void;
  onToggleLock: (id: string) => void;
  onDeleteLayer: (id: string) => void;
  onOpacityChange?: (id: string, value: number) => void;
  canMoveUp: boolean;
  canMoveDown: boolean;
  onMoveUp?: (id: string) => void;
  onMoveDown?: (id: string) => void;
  disabled?: boolean;
}

/**
 * DraggableLayer - A draggable layer component for layer management
 */
export function DraggableLayer({
  layer,
  index,
  isActive,
  isSelected,
  moveLayer,
  onLayerClick,
  onToggleVisibility,
  onToggleLock,
  onDeleteLayer,
  onOpacityChange,
  canMoveUp,
  canMoveDown,
  onMoveUp,
  onMoveDown,
  disabled = false,
}: DraggableLayerProps) {
  const ref = useRef<HTMLDivElement>(null);
  
  // Set up drop functionality
  const [{ handlerId }, drop] = useDrop({
    accept: LAYER_ITEM_TYPE,
    collect(monitor) {
      return {
        handlerId: monitor.getHandlerId(),
      };
    },
    hover(item: any, monitor) {
      if (!ref.current) {
        return;
      }
      
      const dragIndex = item.index;
      const hoverIndex = index;
      
      // Don't replace items with themselves
      if (dragIndex === hoverIndex) {
        return;
      }
      
      // Get the rectangle on screen
      const hoverBoundingRect = ref.current.getBoundingClientRect();
      
      // Get vertical middle
      const hoverMiddleY = 
        (hoverBoundingRect.bottom - hoverBoundingRect.top) / 2;
      
      // Determine mouse position
      const clientOffset = monitor.getClientOffset();
      
      // Get pixels to the top
      const hoverClientY = (clientOffset?.y || 0) - hoverBoundingRect.top;
      
      // Dragging downwards
      if (dragIndex < hoverIndex && hoverClientY < hoverMiddleY) {
        return;
      }
      
      // Dragging upwards
      if (dragIndex > hoverIndex && hoverClientY > hoverMiddleY) {
        return;
      }
      
      // Actually perform the action
      moveLayer(dragIndex, hoverIndex);
      
      // Update the index for the dragged item
      item.index = hoverIndex;
    },
  });
  
  // Set up drag functionality
  const [{ isDragging }, drag] = useDrag({
    type: LAYER_ITEM_TYPE,
    item: () => ({ id: layer.id, index }),
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
    canDrag: !disabled && !layer.locked,
  });
  
  // Connect drag and drop refs
  drag(drop(ref));
  
  // Style adjustments
  const opacity = isDragging ? 0.5 : 1;
  
  // Handle opacity change
  const handleOpacityChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (onOpacityChange) {
      onOpacityChange(layer.id, parseInt(e.target.value, 10));
    }
  };
  
  return (
    <div
      ref={ref}
      data-handler-id={handlerId}
      className={`flex flex-col space-y-1 rounded-md p-2 transition-colors ${
        isSelected ? 'bg-blue-100 dark:bg-blue-900' : 
        isActive ? 'bg-blue-50 dark:bg-blue-950' : ''
      } ${isDragging ? 'opacity-50' : 'opacity-100'}`}
      style={{ opacity }}
      onClick={() => onLayerClick(layer.id)}
      data-testid={`layer-${layer.id}`}
      aria-selected={isSelected}
    >
      {/* Layer header with controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {/* Visibility toggle */}
          <Button
            variant="ghost"
            size="sm"
            className="p-1"
            onClick={(e) => {
              e.stopPropagation();
              onToggleVisibility(layer.id);
            }}
            aria-label={`${layer.visible ? 'Hide' : 'Show'} layer ${layer.name}`}
            disabled={disabled}
          >
            {layer.visible ? (
              <Eye className="h-4 w-4" />
            ) : (
              <EyeOff className="h-4 w-4" />
            )}
          </Button>
          
          {/* Layer name */}
          <span className={`text-sm font-medium ${
            !layer.visible ? 'text-gray-400 dark:text-gray-500' : ''
          }`}>
            {layer.name}
          </span>
        </div>
        
        <div className="flex space-x-1">
          {/* Lock toggle */}
          <Button
            variant="ghost"
            size="sm"
            className="p-1"
            onClick={(e) => {
              e.stopPropagation();
              onToggleLock(layer.id);
            }}
            aria-label={`${layer.locked ? 'Unlock' : 'Lock'} layer ${layer.name}`}
            disabled={disabled}
          >
            {layer.locked ? (
              <Lock className="h-4 w-4" />
            ) : (
              <Unlock className="h-4 w-4" />
            )}
          </Button>
          
          {/* Delete button */}
          <Button
            variant="ghost"
            size="sm"
            className="p-1 text-red-500 hover:text-red-700"
            onClick={(e) => {
              e.stopPropagation();
              onDeleteLayer(layer.id);
            }}
            aria-label={`Delete layer ${layer.name}`}
            disabled={disabled}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>
      
      {/* Thumbnail and additional controls */}
      <div className="flex items-center gap-2">
        {/* Layer thumbnail */}
        <div className="h-10 w-10 flex-shrink-0 overflow-hidden rounded border border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800">
          {layer.thumbnail ? (
            <img 
              src={layer.thumbnail} 
              alt={`${layer.name} thumbnail`} 
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-gray-400">
              <Image className="h-5 w-5" />
            </div>
          )}
        </div>
        
        <div className="flex flex-grow flex-col gap-1">
          {/* Opacity slider */}
          {onOpacityChange && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Opacity:</span>
              <input
                type="range"
                min="0"
                max="100"
                value={layer.opacity ?? 100}
                onChange={handleOpacityChange}
                className="h-2 flex-grow appearance-none rounded-lg bg-gray-200 dark:bg-gray-700"
                onClick={(e) => e.stopPropagation()}
                disabled={disabled || !layer.visible}
                aria-label={`Layer ${layer.name} opacity`}
              />
              <span className="w-8 text-right text-xs text-gray-500">
                {layer.opacity ?? 100}%
              </span>
            </div>
          )}
          
          {/* Up/Down controls */}
          <div className="flex justify-end gap-1">
            <Button
              variant="ghost"
              size="sm"
              className="p-1"
              onClick={(e) => {
                e.stopPropagation();
                if (onMoveUp) onMoveUp(layer.id);
              }}
              disabled={!canMoveUp || disabled || layer.locked}
              aria-label={`Move ${layer.name} up`}
            >
              <ArrowUp className="h-3 w-3" />
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              className="p-1"
              onClick={(e) => {
                e.stopPropagation();
                if (onMoveDown) onMoveDown(layer.id);
              }}
              disabled={!canMoveDown || disabled || layer.locked}
              aria-label={`Move ${layer.name} down`}
            >
              <ArrowDown className="h-3 w-3" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}