'use client';

import { CognitiveCanvas } from '@/components/CognitiveCanvas';

export default function CognitiveCanvasPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen py-12 bg-gray-50 dark:bg-gray-900">
      <main className="flex flex-col items-center justify-center flex-1 px-4 sm:px-20 w-full max-w-6xl">
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl text-center">
          Cognitive Canvas
        </h1>
        <p className="mt-6 text-xl text-gray-600 dark:text-gray-400 max-w-2xl text-center mb-10">
          Real-time collaborative whiteboard with AI-powered visualization and analysis.
        </p>
        
        <div className="w-full mt-6">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
            <CognitiveCanvas
              documentId="demo-canvas"
              userId={`demo-user-${Math.floor(Math.random() * 10000)}`}
              userName="Demo User"
            />
          </div>
        </div>
      </main>
    </div>
  );
}