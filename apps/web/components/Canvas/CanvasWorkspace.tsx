"use client"

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { 
  Move, ZoomIn, ZoomOut, Grid, Undo, Redo, 
  Plus, Image, Type, Button as ButtonIcon, 
  Columns, Clock, Table, Video, Code, 
  Trash, Copy, Save, Download, Share
} from 'lucide-react';

// Types
interface CardData {
  id: string;
  type: 'text' | 'image' | 'button' | 'divider' | 'spacer' | 'dynamic' | 'countdown' | 'social' | 'product' | 'video' | 'form';
  content: any;
  position: { x: number; y: number };
  size: { width: number; height: number };
  selected?: boolean;
}

interface CanvasWorkspaceProps {
  className?: string;
  cards?: CardData[];
  onCardSelect?: (cardId: string) => void;
  onCardMove?: (cardId: string, position: { x: number; y: number }) => void;
  onCardResize?: (cardId: string, size: { width: number; height: number }) => void;
  onCardDelete?: (cardId: string) => void;
  onCardDuplicate?: (cardId: string) => void;
  onAddCard?: (type: CardData['type'], position: { x: number; y: number }) => void;
  onUndo?: () => void;
  onRedo?: () => void;
  onSave?: () => void;
}

export function CanvasWorkspace({
  className,
  cards = [],
  onCardSelect,
  onCardMove,
  onCardResize,
  onCardDelete,
  onCardDuplicate,
  onAddCard,
  onUndo,
  onRedo,
  onSave,
}: CanvasWorkspaceProps) {
  const [zoom, setZoom] = useState(1);
  const [tool, setTool] = useState<'select' | 'move' | 'text' | 'image' | 'button'>('select');
  const [showGrid, setShowGrid] = useState(true);
  const [selectedCardIds, setSelectedCardIds] = useState<string[]>([]);
  
  // Default cards if none provided
  const defaultCards: CardData[] = [
    {
      id: 'card-1',
      type: 'text',
      content: {
        text: '<h1>Welcome to our Spring Collection</h1><p>Discover the latest trends for the season.</p>',
        color: '#333333',
        fontSize: 16,
        alignment: 'center',
      },
      position: { x: 100, y: 100 },
      size: { width: 400, height: 100 },
      selected: true,
    },
    {
      id: 'card-2',
      type: 'image',
      content: {
        src: 'https://via.placeholder.com/400x200',
        alt: 'Spring Collection',
        caption: 'Our new spring collection is here!',
      },
      position: { x: 100, y: 220 },
      size: { width: 400, height: 200 },
    },
    {
      id: 'card-3',
      type: 'button',
      content: {
        text: 'Shop Now',
        url: '#',
        backgroundColor: '#4F46E5',
        textColor: '#FFFFFF',
        borderRadius: 4,
      },
      position: { x: 250, y: 440 },
      size: { width: 100, height: 40 },
    },
  ];
  
  const displayCards = cards.length > 0 ? cards : defaultCards;
  
  // Zoom in
  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev + 0.1, 2));
  };
  
  // Zoom out
  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev - 0.1, 0.5));
  };
  
  // Toggle grid
  const toggleGrid = () => {
    setShowGrid(!showGrid);
  };
  
  // Select tool
  const selectTool = (selectedTool: typeof tool) => {
    setTool(selectedTool);
  };
  
  // Handle card selection
  const handleCardSelect = (cardId: string, event: React.MouseEvent) => {
    if (event.shiftKey) {
      setSelectedCardIds(prev => 
        prev.includes(cardId)
          ? prev.filter(id => id !== cardId)
          : [...prev, cardId]
      );
    } else {
      setSelectedCardIds([cardId]);
    }
    
    onCardSelect?.(cardId);
  };
  
  // Handle canvas click (deselect all)
  const handleCanvasClick = (event: React.MouseEvent) => {
    if (event.target === event.currentTarget) {
      setSelectedCardIds([]);
    }
  };
  
  // Handle delete selected
  const handleDeleteSelected = () => {
    selectedCardIds.forEach(id => {
      onCardDelete?.(id);
    });
    setSelectedCardIds([]);
  };
  
  // Handle duplicate selected
  const handleDuplicateSelected = () => {
    selectedCardIds.forEach(id => {
      onCardDuplicate?.(id);
    });
  };
  
  // Render card based on type
  const renderCard = (card: CardData) => {
    const isSelected = selectedCardIds.includes(card.id);
    
    const cardStyle = {
      left: `${card.position.x}px`,
      top: `${card.position.y}px`,
      width: `${card.size.width}px`,
      height: `${card.size.height}px`,
    };
    
    const commonProps = {
      className: cn(
        "absolute border border-transparent hover:border-primary/30 cursor-pointer",
        isSelected && "border-primary ring-2 ring-primary/30"
      ),
      style: cardStyle,
      onClick: (e: React.MouseEvent) => handleCardSelect(card.id, e),
    };
    
    switch (card.type) {
      case 'text':
        return (
          <div 
            {...commonProps}
            dangerouslySetInnerHTML={{ __html: card.content.text }}
            style={{
              ...cardStyle,
              color: card.content.color,
              fontSize: `${card.content.fontSize}px`,
              textAlign: card.content.alignment as any,
            }}
          />
        );
      
      case 'image':
        return (
          <div {...commonProps}>
            <img 
              src={card.content.src} 
              alt={card.content.alt} 
              className="w-full h-full object-cover"
            />
            {card.content.caption && (
              <div className="text-xs text-center mt-1">{card.content.caption}</div>
            )}
          </div>
        );
      
      case 'button':
        return (
          <div {...commonProps} className={cn(commonProps.className, "flex items-center justify-center")}>
            <button
              className="px-4 py-2 rounded text-sm font-medium w-full h-full flex items-center justify-center"
              style={{
                backgroundColor: card.content.backgroundColor,
                color: card.content.textColor,
                borderRadius: `${card.content.borderRadius}px`,
              }}
            >
              {card.content.text}
            </button>
          </div>
        );
      
      default:
        return (
          <div {...commonProps}>
            <div className="w-full h-full flex items-center justify-center bg-muted/50">
              Unknown card type: {card.type}
            </div>
          </div>
        );
    }
  };

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Toolbar */}
      <div className="flex items-center justify-between p-2 border-b border-border">
        <div className="flex items-center space-x-1">
          {/* Tools */}
          <button 
            className={cn(
              "p-1.5 rounded",
              tool === 'select' ? "bg-primary/10 text-primary" : "hover:bg-muted"
            )}
            onClick={() => selectTool('select')}
            title="Select Tool"
          >
            <Move className="w-4 h-4" />
          </button>
          
          <button 
            className={cn(
              "p-1.5 rounded",
              tool === 'text' ? "bg-primary/10 text-primary" : "hover:bg-muted"
            )}
            onClick={() => selectTool('text')}
            title="Text Tool"
          >
            <Type className="w-4 h-4" />
          </button>
          
          <button 
            className={cn(
              "p-1.5 rounded",
              tool === 'image' ? "bg-primary/10 text-primary" : "hover:bg-muted"
            )}
            onClick={() => selectTool('image')}
            title="Image Tool"
          >
            <Image className="w-4 h-4" />
          </button>
          
          <button 
            className={cn(
              "p-1.5 rounded",
              tool === 'button' ? "bg-primary/10 text-primary" : "hover:bg-muted"
            )}
            onClick={() => selectTool('button')}
            title="Button Tool"
          >
            <ButtonIcon className="w-4 h-4" />
          </button>
          
          <div className="h-4 w-px bg-border mx-1" />
          
          {/* View Controls */}
          <button 
            className="p-1.5 rounded hover:bg-muted"
            onClick={handleZoomIn}
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          
          <button 
            className="p-1.5 rounded hover:bg-muted"
            onClick={handleZoomOut}
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          
          <button 
            className={cn(
              "p-1.5 rounded",
              showGrid ? "bg-primary/10 text-primary" : "hover:bg-muted"
            )}
            onClick={toggleGrid}
            title="Toggle Grid"
          >
            <Grid className="w-4 h-4" />
          </button>
          
          <div className="h-4 w-px bg-border mx-1" />
          
          {/* History Controls */}
          <button 
            className="p-1.5 rounded hover:bg-muted"
            onClick={onUndo}
            title="Undo"
          >
            <Undo className="w-4 h-4" />
          </button>
          
          <button 
            className="p-1.5 rounded hover:bg-muted"
            onClick={onRedo}
            title="Redo"
          >
            <Redo className="w-4 h-4" />
          </button>
        </div>
        
        <div className="flex items-center space-x-1">
          {/* Selection Actions */}
          {selectedCardIds.length > 0 && (
            <>
              <button 
                className="p-1.5 rounded hover:bg-muted"
                onClick={handleDeleteSelected}
                title="Delete Selected"
              >
                <Trash className="w-4 h-4" />
              </button>
              
              <button 
                className="p-1.5 rounded hover:bg-muted"
                onClick={handleDuplicateSelected}
                title="Duplicate Selected"
              >
                <Copy className="w-4 h-4" />
              </button>
              
              <div className="h-4 w-px bg-border mx-1" />
            </>
          )}
          
          {/* Save/Export */}
          <button 
            className="p-1.5 rounded hover:bg-muted"
            onClick={onSave}
            title="Save"
          >
            <Save className="w-4 h-4" />
          </button>
          
          <button 
            className="p-1.5 rounded hover:bg-muted"
            title="Export"
          >
            <Download className="w-4 h-4" />
          </button>
          
          <button 
            className="p-1.5 rounded hover:bg-muted"
            title="Share"
          >
            <Share className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {/* Canvas */}
      <div 
        className={cn(
          "flex-1 relative overflow-auto",
          showGrid && "bg-grid-pattern"
        )}
        style={{
          backgroundSize: `${20 * zoom}px ${20 * zoom}px`,
        }}
        onClick={handleCanvasClick}
      >
        <div 
          className="relative min-h-full"
          style={{
            transform: `scale(${zoom})`,
            transformOrigin: 'top left',
          }}
        >
          {displayCards.map(card => renderCard(card))}
        </div>
      </div>
      
      {/* Add Component Button */}
      <div className="absolute bottom-4 right-4">
        <button 
          className="w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center shadow-lg hover:bg-primary/90"
          title="Add Component"
        >
          <Plus className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
