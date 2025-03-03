"use client"

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface SplitScreenLayoutProps {
  leftPanel: React.ReactNode;
  mainCanvas: React.ReactNode;
  topNavigation?: React.ReactNode;
  bottomPanel?: React.ReactNode;
  className?: string;
  defaultLeftPanelWidth?: number;
  defaultBottomPanelHeight?: number;
}

export function SplitScreenLayout({
  leftPanel,
  mainCanvas,
  topNavigation,
  bottomPanel,
  className,
  defaultLeftPanelWidth = 400,
  defaultBottomPanelHeight = 300,
}: SplitScreenLayoutProps) {
  const [leftPanelWidth, setLeftPanelWidth] = useState(defaultLeftPanelWidth);
  const [bottomPanelHeight, setBottomPanelHeight] = useState(defaultBottomPanelHeight);
  const [isResizingLeft, setIsResizingLeft] = useState(false);
  const [isResizingBottom, setIsResizingBottom] = useState(false);
  const [isLeftPanelCollapsed, setIsLeftPanelCollapsed] = useState(false);
  
  // Handle left panel resize
  const handleLeftPanelResize = (e: React.MouseEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsResizingLeft(true);
    
    const startX = e.clientX;
    const startWidth = leftPanelWidth;
    
    const handleMouseMove = (moveEvent: MouseEvent) => {
      const newWidth = Math.max(250, Math.min(600, startWidth + moveEvent.clientX - startX));
      setLeftPanelWidth(newWidth);
    };
    
    const handleMouseUp = () => {
      setIsResizingLeft(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };
  
  // Handle bottom panel resize
  const handleBottomPanelResize = (e: React.MouseEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsResizingBottom(true);
    
    const startY = e.clientY;
    const startHeight = bottomPanelHeight;
    
    const handleMouseMove = (moveEvent: MouseEvent) => {
      const newHeight = Math.max(150, Math.min(500, startHeight - (moveEvent.clientY - startY)));
      setBottomPanelHeight(newHeight);
    };
    
    const handleMouseUp = () => {
      setIsResizingBottom(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };
  
  // Toggle left panel collapse
  const toggleLeftPanel = () => {
    setIsLeftPanelCollapsed(!isLeftPanelCollapsed);
  };

  return (
    <div className={cn("flex flex-col h-full overflow-hidden", className)}>
      {/* Top Navigation */}
      {topNavigation && (
        <div className="flex-none border-b border-border">
          {topNavigation}
        </div>
      )}
      
      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel */}
        <div 
          className={cn(
            "flex-none relative border-r border-border transition-all duration-300 ease-in-out",
            isLeftPanelCollapsed ? "w-0" : "overflow-hidden"
          )}
          style={{ width: isLeftPanelCollapsed ? 0 : leftPanelWidth }}
        >
          {!isLeftPanelCollapsed && (
            <div className="h-full overflow-auto p-4">
              {leftPanel}
            </div>
          )}
          
          {/* Resize Handle */}
          {!isLeftPanelCollapsed && (
            <div 
              className={cn(
                "absolute top-0 right-0 w-1 h-full cursor-col-resize hover:bg-primary/20",
                isResizingLeft && "bg-primary/40"
              )}
              onMouseDown={handleLeftPanelResize}
            />
          )}
        </div>
        
        {/* Toggle Button */}
        <div 
          className="flex-none w-6 flex items-center justify-center border-r border-border hover:bg-muted/50 cursor-pointer"
          onClick={toggleLeftPanel}
        >
          {isLeftPanelCollapsed ? (
            <ChevronRight className="w-4 h-4 text-muted-foreground" />
          ) : (
            <ChevronLeft className="w-4 h-4 text-muted-foreground" />
          )}
        </div>
        
        {/* Main Content Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Main Canvas */}
          <div 
            className="flex-1 overflow-auto"
            style={{ height: bottomPanel ? `calc(100% - ${bottomPanelHeight}px)` : '100%' }}
          >
            {mainCanvas}
          </div>
          
          {/* Bottom Panel */}
          {bottomPanel && (
            <div className="flex-none relative">
              {/* Resize Handle */}
              <div 
                className={cn(
                  "absolute top-0 left-0 w-full h-1 cursor-row-resize hover:bg-primary/20 z-10",
                  isResizingBottom && "bg-primary/40"
                )}
                onMouseDown={handleBottomPanelResize}
              />
              
              <div 
                className="border-t border-border overflow-hidden"
                style={{ height: bottomPanelHeight }}
              >
                {bottomPanel}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
