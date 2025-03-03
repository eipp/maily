tter
import React from 'react';
import config from '@/lib/config';

export default function HybridInterfaceLoading() {
  return (
    <div className="h-screen flex flex-col items-center justify-center bg-background">
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-4">{config.meta.name}</h1>
        <p className="text-xl text-muted-foreground mb-8">Loading Hybrid Interface...</p>
        
        <div className="flex flex-col items-center space-y-6">
          {/* Loading spinner */}
          <div className="relative h-16 w-16">
            <div className="absolute inset-0 rounded-full border-4 border-primary/30"></div>
            <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-primary animate-spin"></div>
          </div>
          
          {/* Loading progress */}
          <div className="w-64 h-2 bg-muted rounded-full overflow-hidden">
            <div className="h-full bg-primary animate-pulse"></div>
          </div>
          
          {/* Loading message */}
          <div className="text-sm text-muted-foreground animate-pulse">
            Initializing AI Mesh Network...
          </div>
        </div>
      </div>
      
      {/* Feature highlights */}
      <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto px-4">
        <div className="flex flex-col items-center text-center p-4">
          <div className="h-12 w-12 rounded-full bg-red-100 flex items-center justify-center mb-4">
            <span className="text-red-500 text-xl">✍️</span>
          </div>
          <h3 className="font-medium mb-2">Content Creation</h3>
          <p className="text-sm text-muted-foreground">AI-powered content generation with personalization</p>
        </div>
        
        <div className="flex flex-col items-center text-center p-4">
          <div className="h-12 w-12 rounded-full bg-violet-100 flex items-center justify-center mb-4">
            <span className="text-violet-500 text-xl">🎨</span>
          </div>
          <h3 className="font-medium mb-2">Visual Design</h3>
          <p className="text-sm text-muted-foreground">Beautiful templates with responsive layouts</p>
        </div>
        
        <div className="flex flex-col items-center text-center p-4">
          <div className="h-12 w-12 rounded-full bg-cyan-100 flex items-center justify-center mb-4">
            <span className="text-cyan-500 text-xl">📊</span>
          </div>
          <h3 className="font-medium mb-2">Analytics</h3>
          <p className="text-sm text-muted-foreground">Real-time insights and performance tracking</p>
        </div>
      </div>
    </div>
  );
}
