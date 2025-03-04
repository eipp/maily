'use client';

import React from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { TouchBackend } from 'react-dnd-touch-backend';
import { isTouchDevice } from '@/utils/device';

/**
 * DndContext - Provides React DnD context with appropriate backend based on device
 * 
 * This component automatically selects between HTML5Backend for desktop devices
 * and TouchBackend for mobile/touch devices
 */
export function DndContext({ children }: { children: React.ReactNode }) {
  // Determine if running on client side
  const [isClient, setIsClient] = React.useState(false);
  
  React.useEffect(() => {
    setIsClient(true);
  }, []);
  
  // Select appropriate backend based on device type
  const backend = React.useMemo(() => {
    // Only check for touch capability on client side
    if (!isClient) return HTML5Backend;
    
    return isTouchDevice() ? TouchBackend : HTML5Backend;
  }, [isClient]);
  
  // Options for touch backend
  const touchOptions = {
    enableMouseEvents: true,
    enableTouchEvents: true,
    delayTouchStart: 50,
  };
  
  // Return children directly during SSR to avoid hydration issues
  if (!isClient) {
    return <>{children}</>;
  }
  
  return (
    <DndProvider 
      backend={backend} 
      options={backend === TouchBackend ? touchOptions : undefined}
    >
      {children}
    </DndProvider>
  );
}