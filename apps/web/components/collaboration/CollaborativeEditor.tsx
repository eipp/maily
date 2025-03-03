/**
 * CollaborativeEditor Component
 * 
 * This component provides a collaborative rich text editor using Yjs and TipTap.
 * It includes real-time collaboration, presence awareness, and conflict resolution.
 */

import React, { useEffect, useState, useCallback } from 'react';
import { useEditor, EditorContent, Editor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Collaboration from '@tiptap/extension-collaboration';
import CollaborationCursor from '@tiptap/extension-collaboration-cursor';
import Placeholder from '@tiptap/extension-placeholder';
import { useYjs } from './YjsProvider';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, Users } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

// Define the props
export interface CollaborativeEditorProps {
  documentId: string;
  placeholder?: string;
  className?: string;
  readOnly?: boolean;
  onUpdate?: (editor: Editor) => void;
  onSave?: (content: string) => void;
  autoSave?: boolean;
  autoSaveInterval?: number;
}

/**
 * CollaborativeEditor component
 * 
 * @param props Component props
 * @returns CollaborativeEditor component
 */
export const CollaborativeEditor: React.FC<CollaborativeEditorProps> = ({
  documentId,
  placeholder = 'Start typing...',
  className = '',
  readOnly = false,
  onUpdate,
  onSave,
  autoSave = true,
  autoSaveInterval = 5000,
}) => {
  const { doc, awareness, isConnected, isLoading, error } = useYjs();
  const [activeUsers, setActiveUsers] = useState<any[]>([]);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  
  // Initialize the editor
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        history: false, // Disable history as it's handled by Yjs
      }),
      Placeholder.configure({
        placeholder,
      }),
      // Add collaboration extension
      doc && Collaboration.configure({
        document: doc,
        field: documentId,
      }),
      // Add collaboration cursor extension
      awareness && CollaborationCursor.configure({
        provider: awareness,
        user: awareness.getLocalState()?.user || {
          name: 'Anonymous',
          color: '#f783ac',
        },
      }),
    ],
    editable: !readOnly,
    onUpdate: ({ editor }) => {
      onUpdate?.(editor);
    },
  }, [doc, awareness, documentId, readOnly, onUpdate]);
  
  // Update active users when awareness changes
  useEffect(() => {
    if (!awareness) return;
    
    const updateActiveUsers = () => {
      const states = Array.from(awareness.getStates().entries())
        .map(([clientId, state]) => ({
          clientId,
          user: state.user,
        }))
        .filter(({ user }) => user !== undefined);
      
      setActiveUsers(states);
    };
    
    awareness.on('change', updateActiveUsers);
    updateActiveUsers();
    
    return () => {
      awareness.off('change', updateActiveUsers);
    };
  }, [awareness]);
  
  // Auto-save functionality
  useEffect(() => {
    if (!editor || !autoSave || !onSave) return;
    
    const interval = setInterval(() => {
      const content = editor.getHTML();
      setIsSaving(true);
      
      Promise.resolve(onSave(content))
        .then(() => {
          setLastSaved(new Date());
        })
        .catch((err) => {
          console.error('Failed to auto-save:', err);
        })
        .finally(() => {
          setIsSaving(false);
        });
    }, autoSaveInterval);
    
    return () => {
      clearInterval(interval);
    };
  }, [editor, autoSave, autoSaveInterval, onSave]);
  
  // Handle manual save
  const handleSave = useCallback(() => {
    if (!editor || !onSave) return;
    
    const content = editor.getHTML();
    setIsSaving(true);
    
    Promise.resolve(onSave(content))
      .then(() => {
        setLastSaved(new Date());
      })
      .catch((err) => {
        console.error('Failed to save:', err);
      })
      .finally(() => {
        setIsSaving(false);
      });
  }, [editor, onSave]);
  
  // Render loading state
  if (isLoading) {
    return (
      <div className={`border rounded-md p-4 ${className}`}>
        <div className="flex items-center justify-between mb-4">
          <Skeleton className="h-8 w-32" />
          <Skeleton className="h-8 w-24" />
        </div>
        <Skeleton className="h-24 w-full mb-4" />
        <Skeleton className="h-24 w-full" />
      </div>
    );
  }
  
  // Render error state
  if (error) {
    return (
      <Alert variant="destructive" className={className}>
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>
          Failed to initialize collaborative editor: {error.message}
        </AlertDescription>
      </Alert>
    );
  }
  
  return (
    <div className={`border rounded-md p-4 ${className}`}>
      {/* Editor header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex -space-x-2">
                  {activeUsers.slice(0, 3).map(({ clientId, user }) => (
                    <Avatar key={clientId} className="border-2 border-background w-8 h-8">
                      {user.image ? (
                        <AvatarImage src={user.image} alt={user.name} />
                      ) : (
                        <AvatarFallback style={{ backgroundColor: user.color }}>
                          {user.name.substring(0, 2).toUpperCase()}
                        </AvatarFallback>
                      )}
                    </Avatar>
                  ))}
                  {activeUsers.length > 3 && (
                    <Avatar className="border-2 border-background w-8 h-8">
                      <AvatarFallback>+{activeUsers.length - 3}</AvatarFallback>
                    </Avatar>
                  )}
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <div className="space-y-1">
                  <p className="font-semibold">Active users</p>
                  <ul>
                    {activeUsers.map(({ clientId, user }) => (
                      <li key={clientId} className="flex items-center space-x-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: user.color }}
                        />
                        <span>{user.name}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          
          <Badge variant={isConnected ? 'default' : 'outline'} className="ml-2">
            <Users className="w-3 h-3 mr-1" />
            {isConnected ? 'Connected' : 'Offline'}
          </Badge>
        </div>
        
        {onSave && !readOnly && (
          <div className="flex items-center space-x-2">
            {lastSaved && (
              <span className="text-xs text-muted-foreground">
                Last saved: {lastSaved.toLocaleTimeString()}
              </span>
            )}
            <Button
              size="sm"
              onClick={handleSave}
              disabled={isSaving}
            >
              {isSaving ? 'Saving...' : 'Save'}
            </Button>
          </div>
        )}
      </div>
      
      {/* Editor content */}
      <EditorContent
        editor={editor}
        className="prose prose-sm max-w-none min-h-[200px] focus:outline-none"
      />
      
      {/* Conflict resolution UI */}
      {editor?.storage.collaborationCursor.conflicts?.length > 0 && (
        <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-md">
          <h4 className="text-sm font-medium text-amber-900">Conflicts detected</h4>
          <p className="text-xs text-amber-700 mt-1">
            There are conflicting changes. The system has automatically merged them,
            but you may want to review the content.
          </p>
        </div>
      )}
    </div>
  );
};

export default CollaborativeEditor;
