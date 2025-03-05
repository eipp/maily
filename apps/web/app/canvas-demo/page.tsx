'use client';

import React, { useState } from 'react';
import { EnhancedCanvas } from '@/components/EnhancedCanvas';
import { DndContext } from '@/components/DndContext';
import { Shield, Square, Circle as CircleIcon, Type, Image } from 'lucide-react';
import { useDrag } from 'react-dnd';

// Create draggable shape component
function DraggableShape({ type, children }: { type: string, children: React.ReactNode }) {
  const [{ isDragging }, drag] = useDrag(() => ({
    type: 'shape',
    item: { type: 'shape', shapeType: type },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  }));
  
  return (
    <div
      ref={drag}
      className={`flex h-20 w-20 cursor-move flex-col items-center justify-center rounded-lg border border-gray-200 bg-white p-2 shadow-sm transition-all hover:shadow-md dark:border-gray-700 dark:bg-gray-800 ${
        isDragging ? 'opacity-50' : 'opacity-100'
      }`}
    >
      {children}
      <span className="mt-2 text-xs">{type}</span>
    </div>
  );
}

export default function CanvasDemoPage() {
  const [verificationStatus, setVerificationStatus] = useState({
    isVerified: true,
    showVerificationLayer: false,
    certificateData: {
      id: 'cert-' + Math.random().toString(36).substring(2, 9),
      issuer: 'Maily Trust Verification',
      timestamp: new Date().toISOString(),
    },
  });
  
  const handleToggleVerificationLayer = () => {
    setVerificationStatus((prev) => ({
      ...prev,
      showVerificationLayer: !prev.showVerificationLayer,
    }));
  };
  
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="mb-8 text-center text-3xl font-bold">Cognitive Canvas Demo</h1>
      
      <div className="mb-6 rounded-lg bg-blue-50 p-4 dark:bg-blue-900/20">
        <h2 className="mb-2 text-xl font-semibold">Instructions</h2>
        <ul className="list-inside list-disc space-y-1">
          <li>Drag shapes from the palette below onto the canvas</li>
          <li>Use the toolbar to add, delete, and manipulate shapes</li>
          <li>Click the layers icon to manage layers</li>
          <li>Click the performance metrics icon to view canvas performance</li>
          <li>Use mouse wheel to zoom in/out</li>
        </ul>
      </div>
      
      <div className="mb-4 flex items-center justify-center space-x-4">
        <DndContext>
          <div className="flex space-x-4">
            <DraggableShape type="rect">
              <Square className="h-8 w-8 text-blue-500" />
            </DraggableShape>
            
            <DraggableShape type="circle">
              <CircleIcon className="h-8 w-8 text-green-500" />
            </DraggableShape>
            
            <DraggableShape type="text">
              <Type className="h-8 w-8 text-purple-500" />
            </DraggableShape>
          </div>
        </DndContext>
      </div>
      
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800">
        <EnhancedCanvas
          roomId="demo-room"
          userId={`user-${Math.floor(Math.random() * 100000)}`}
          verificationStatus={verificationStatus}
          onToggleVerificationLayer={handleToggleVerificationLayer}
        />
      </div>
      
      <div className="mt-8 rounded-lg bg-gray-50 p-4 dark:bg-gray-800">
        <h2 className="mb-2 text-xl font-semibold">Features Implemented</h2>
        <ul className="list-inside list-disc space-y-1 text-sm">
          <li>React DnD Integration for dragging shapes onto the canvas</li>
          <li>Enhanced layer management with drag-and-drop reordering</li>
          <li>Layer opacity controls and thumbnails</li>
          <li>Comprehensive performance metrics visualization</li>
          <li>Real-time collaboration with cursor position sharing</li>
          <li>Multiple selection with shift-click</li>
          <li>Pan and zoom controls for canvas navigation</li>
          <li>Trust verification overlay visualization</li>
        </ul>
      </div>
    </div>
  );
}