/**
 * YjsProvider Component
 * 
 * This component provides real-time collaboration capabilities using Yjs.
 * It sets up the WebRTC provider, awareness, and handles synchronization.
 */

import React, { useEffect, useRef, useState } from 'react';
import * as Y from 'yjs';
import { WebrtcProvider } from 'y-webrtc';
import { IndexeddbPersistence } from 'y-indexeddb';
import { Awareness } from 'y-protocols/awareness';
import { nanoid } from 'nanoid';
import { useSession } from 'next-auth/react';
import { useTheme } from 'next-themes';

// Define the context type
export interface YjsContextType {
  doc: Y.Doc | null;
  provider: WebrtcProvider | null;
  awareness: Awareness | null;
  isConnected: boolean;
  isLoading: boolean;
  error: Error | null;
}

// Create the context
export const YjsContext = React.createContext<YjsContextType>({
  doc: null,
  provider: null,
  awareness: null,
  isConnected: false,
  isLoading: true,
  error: null,
});

// Define the provider props
export interface YjsProviderProps {
  children: React.ReactNode;
  roomName: string;
  signaling?: string[];
  color?: string;
  persistent?: boolean;
}

/**
 * YjsProvider component
 * 
 * @param props Component props
 * @returns YjsProvider component
 */
export const YjsProvider: React.FC<YjsProviderProps> = ({
  children,
  roomName,
  signaling = ['wss://signaling.justmaily.com'],
  color,
  persistent = true,
}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  
  const docRef = useRef<Y.Doc | null>(null);
  const providerRef = useRef<WebrtcProvider | null>(null);
  const persistenceRef = useRef<IndexeddbPersistence | null>(null);
  const awarenessRef = useRef<Awareness | null>(null);
  
  const { data: session } = useSession();
  const { theme } = useTheme();
  
  // Generate a random color if not provided
  const userColor = color || generateRandomColor();
  
  useEffect(() => {
    // Initialize Yjs document
    const doc = new Y.Doc();
    docRef.current = doc;
    
    // Set up WebRTC provider
    const provider = new WebrtcProvider(`maily-${roomName}`, doc, {
      signaling,
      password: null,
      awareness: new Awareness(doc),
      maxConns: 20,
      filterBcConns: true,
      peerOpts: {},
    });
    providerRef.current = provider;
    awarenessRef.current = provider.awareness;
    
    // Set up persistence if enabled
    if (persistent) {
      try {
        const persistence = new IndexeddbPersistence(`maily-${roomName}`, doc);
        persistenceRef.current = persistence;
        
        persistence.on('synced', () => {
          console.log('Content loaded from IndexedDB');
        });
      } catch (err) {
        console.error('Failed to set up IndexedDB persistence:', err);
      }
    }
    
    // Set up awareness
    const awareness = provider.awareness;
    
    // Set local state
    awareness.setLocalState({
      user: {
        id: session?.user?.id || nanoid(),
        name: session?.user?.name || 'Anonymous',
        email: session?.user?.email,
        color: userColor,
        image: session?.user?.image,
      },
      cursor: null,
      selection: null,
      theme,
    });
    
    // Set up connection status
    const handleStatusChange = (event: { status: 'connected' | 'disconnected' }) => {
      setIsConnected(event.status === 'connected');
      setIsLoading(false);
    };
    
    provider.on('status', handleStatusChange);
    
    // Handle errors
    const handleError = (err: Error) => {
      console.error('YjsProvider error:', err);
      setError(err);
      setIsLoading(false);
    };
    
    provider.on('error', handleError);
    
    // Clean up
    return () => {
      provider.off('status', handleStatusChange);
      provider.off('error', handleError);
      
      if (persistenceRef.current) {
        persistenceRef.current.destroy();
        persistenceRef.current = null;
      }
      
      provider.destroy();
      providerRef.current = null;
      
      doc.destroy();
      docRef.current = null;
    };
  }, [roomName, signaling, persistent, session, theme, userColor]);
  
  // Update awareness when user or theme changes
  useEffect(() => {
    if (awarenessRef.current && session) {
      const currentState = awarenessRef.current.getLocalState();
      
      if (currentState) {
        awarenessRef.current.setLocalState({
          ...currentState,
          user: {
            ...currentState.user,
            id: session.user?.id || currentState.user.id,
            name: session.user?.name || currentState.user.name,
            email: session.user?.email || currentState.user.email,
            image: session.user?.image || currentState.user.image,
          },
          theme,
        });
      }
    }
  }, [session, theme]);
  
  return (
    <YjsContext.Provider
      value={{
        doc: docRef.current,
        provider: providerRef.current,
        awareness: awarenessRef.current,
        isConnected,
        isLoading,
        error,
      }}
    >
      {children}
    </YjsContext.Provider>
  );
};

/**
 * Hook to use Yjs context
 * 
 * @returns Yjs context
 */
export const useYjs = () => {
  const context = React.useContext(YjsContext);
  
  if (context === undefined) {
    throw new Error('useYjs must be used within a YjsProvider');
  }
  
  return context;
};

/**
 * Generate a random color
 * 
 * @returns Random color in hex format
 */
function generateRandomColor(): string {
  // Generate pastel colors for better visibility
  const hue = Math.floor(Math.random() * 360);
  const saturation = 70 + Math.floor(Math.random() * 20); // 70-90%
  const lightness = 60 + Math.floor(Math.random() * 10); // 60-70%
  
  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}
