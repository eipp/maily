'use client';

import React, { useState } from 'react';
import { Plus, Layers, X, FolderPlus, Eye, EyeOff } from 'lucide-react';
import { Button } from '@/components/Button';
import { DraggableLayer, Layer } from '@/components/DraggableLayer';
import { generateThumbnailForLayer } from '@/utils/canvas';

interface LayersPanelProps {
  layers: Layer[];
  activeLayerId: string;
  selectedLayerIds: string[];
  onLayerClick: (id: string) => void;
  onLayerSelect: (id: string, isMultiSelect?: boolean) => void;
  onToggleVisibility: (id: string) => void;
  onToggleLock: (id: string) => void;
  onDeleteLayer: (id: string) => void;
  onAddLayer: () => void;
  onAddLayerGroup?: () => void;
  onOpacityChange: (id: string, value: number) => void;
  onReorderLayers: (layers: Layer[]) => void;
  onToggleAllLayers?: (visible: boolean) => void;
  showPanel: boolean;
  onTogglePanel: () => void;
  readOnly?: boolean;
  canvasRef?: React.RefObject<any>;
  className?: string;
}

export function LayersPanel({
  layers,
  activeLayerId,
  selectedLayerIds,
  onLayerClick,
  onLayerSelect,
  onToggleVisibility,
  onToggleLock,
  onDeleteLayer,
  onAddLayer,
  onAddLayerGroup,
  onOpacityChange,
  onReorderLayers,
  onToggleAllLayers,
  showPanel,
  onTogglePanel,
  readOnly = false,
  canvasRef,
  className = '',
}: LayersPanelProps) {
  const [draggedLayerId, setDraggedLayerId] = useState<string | null>(null);
  
  // Function to move layer (used by drag and drop)
  const moveLayer = (dragIndex: number, hoverIndex: number) => {
    const newLayers = [...layers];
    const draggedLayer = newLayers[dragIndex];
    
    // Remove the dragged layer
    newLayers.splice(dragIndex, 1);
    // Insert at the new position
    newLayers.splice(hoverIndex, 0, draggedLayer);
    
    // Update the state
    onReorderLayers(newLayers);
  };
  
  // Shortcut functions for moving layers up/down
  const moveLayerUp = (id: string) => {
    const index = layers.findIndex(layer => layer.id === id);
    if (index > 0) {
      moveLayer(index, index - 1);
    }
  };
  
  const moveLayerDown = (id: string) => {
    const index = layers.findIndex(layer => layer.id === id);
    if (index < layers.length - 1) {
      moveLayer(index, index + 1);
    }
  };
  
  // Check if no layers are visible
  const areAllLayersHidden = layers.every(layer => !layer.visible);
  
  // Function to toggle visibility of all layers at once
  const handleToggleAllLayers = () => {
    if (onToggleAllLayers) {
      onToggleAllLayers(areAllLayersHidden);
    }
  };
  
  // If panel is not shown, render only the toggle button
  if (!showPanel) {
    return (
      <Button
        variant="ghost"
        size="sm"
        onClick={onTogglePanel}
        className={`flex h-10 w-10 items-center justify-center rounded-full bg-white/80 shadow-md backdrop-blur-sm dark:bg-gray-800/80 ${className}`}
        aria-label="Show layers panel"
      >
        <Layers className="h-5 w-5" />
      </Button>
    );
  }
  
  return (
    <div
      className={`flex h-full w-72 flex-col rounded-lg border border-gray-200 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-800 ${className}`}
      data-testid="layers-panel"
    >
      {/* Panel header */}
      <div className="flex items-center justify-between border-b border-gray-200 p-3 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <Layers className="h-5 w-5" />
          <h3 className="text-sm font-semibold">Layers</h3>
          
          {/* Toggle all layers visibility */}
          {onToggleAllLayers && (
            <Button
              variant="ghost"
              size="sm"
              className="ml-2 p-1"
              onClick={handleToggleAllLayers}
              aria-label={`${areAllLayersHidden ? 'Show' : 'Hide'} all layers`}
            >
              {areAllLayersHidden ? (
                <Eye className="h-4 w-4" />
              ) : (
                <EyeOff className="h-4 w-4" />
              )}
            </Button>
          )}
        </div>
        
        <div className="flex items-center gap-1">
          {/* Add layer buttons */}
          {!readOnly && (
            <>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={onAddLayer}
                className="p-1"
                aria-label="Add new layer"
              >
                <Plus className="h-4 w-4" />
              </Button>
              
              {onAddLayerGroup && (
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={onAddLayerGroup}
                  className="p-1"
                  aria-label="Add layer group"
                >
                  <FolderPlus className="h-4 w-4" />
                </Button>
              )}
            </>
          )}
          
          {/* Close panel button */}
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={onTogglePanel}
            className="p-1"
            aria-label="Close layers panel"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>
      
      {/* Layers list */}
      <div className="flex-grow overflow-y-auto p-2">
        {layers.length === 0 ? (
          <div className="flex h-full items-center justify-center text-center text-sm text-gray-500">
            <div>
              <p>No layers available</p>
              {!readOnly && (
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={onAddLayer}
                  className="mt-2"
                >
                  <Plus className="mr-1 h-4 w-4" />
                  Add a layer
                </Button>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            {layers.map((layer, index) => {
              // If we have a canvas ref and the layer doesn't have a thumbnail,
              // generate one on first render
              if (canvasRef && !layer.thumbnail) {
                layer.thumbnail = generateThumbnailForLayer(canvasRef, layer.id);
              }
              
              return (
                <DraggableLayer
                  key={layer.id}
                  layer={layer}
                  index={index}
                  isActive={activeLayerId === layer.id}
                  isSelected={selectedLayerIds.includes(layer.id)}
                  moveLayer={moveLayer}
                  onLayerClick={(id) => onLayerSelect(id, false)} // Single select
                  onToggleVisibility={onToggleVisibility}
                  onToggleLock={onToggleLock}
                  onDeleteLayer={onDeleteLayer}
                  onOpacityChange={onOpacityChange}
                  canMoveUp={index > 0}
                  canMoveDown={index < layers.length - 1}
                  onMoveUp={moveLayerUp}
                  onMoveDown={moveLayerDown}
                  disabled={readOnly}
                />
              );
            })}
          </div>
        )}
      </div>
      
      {/* Panel footer with info */}
      <div className="border-t border-gray-200 p-2 text-xs text-gray-500 dark:border-gray-700">
        <p>Drag layers to reorder</p>
        <p>Active layer: {layers.find(l => l.id === activeLayerId)?.name || 'None'}</p>
        <p>Visible layers: {layers.filter(l => l.visible).length}/{layers.length}</p>
      </div>
    </div>
  );
}