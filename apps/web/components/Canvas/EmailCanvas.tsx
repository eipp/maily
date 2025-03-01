import React, { useState, useEffect, useRef, useCallback } from 'react'
import { Tldraw, TldrawApp, TDDocument, TDShape, TDShapeType } from '@tldraw/tldraw'
import * as Y from 'yjs'
import { WebsocketProvider } from 'y-websocket'
import { useToast } from '../../hooks/useToast'
import { useEmailCanvasStore } from '../../stores/emailCanvasStore'
import { AiAssistantPanel } from './AiAssistantPanel'
import { EmailCardRegistry } from './cards/EmailCardRegistry'
import { apiHelpers } from '../../lib/api'
import { Button, IconButton, Spinner } from '../../components/ui'
import {
  ArrowUturnLeftIcon,
  ArrowUturnRightIcon,
  EyeIcon,
  ArrowDownTrayIcon,
  LightBulbIcon,
  XMarkIcon,
  PlusIcon,
  ChatBubbleLeftRightIcon
} from '@heroicons/react/24/outline'

interface EmailCanvasProps {
  campaignId: string
  userId: string
  initialContent?: any
  readOnly?: boolean
  onChange?: (content: any) => void
  onExport?: (htmlContent: string) => void
}

/**
 * Email Canvas component for creating and editing email campaigns
 * Uses tldraw for canvas editing and Yjs for real-time collaboration
 */
export const EmailCanvas: React.FC<EmailCanvasProps> = ({
  campaignId,
  userId,
  initialContent,
  readOnly = false,
  onChange,
  onExport
}) => {
  // Ref for tldraw app instance
  const tldrawAppRef = useRef<TldrawApp | null>(null)

  // State for Yjs document and provider
  const [ydoc] = useState(() => new Y.Doc())
  const [provider, setProvider] = useState<WebsocketProvider | null>(null)
  const [isConnecting, setIsConnecting] = useState<boolean>(true)
  const [isSaving, setIsSaving] = useState<boolean>(false)
  const [isExporting, setIsExporting] = useState<boolean>(false)
  const [showAiPanel, setShowAiPanel] = useState<boolean>(false)
  const [cursorPosition, setCursorPosition] = useState<{ x: number; y: number }>({ x: 0, y: 0 })
  const [activeUsers, setActiveUsers] = useState<any[]>([])
  const [previewMode, setPreviewMode] = useState<boolean>(false)

  // Toast notifications
  const { toast } = useToast()

  // Get email canvas store
  const {
    aiSuggestions,
    designSuggestions,
    isGenerating,
    requestAiSuggestion,
    applyAiSuggestion,
    clearSuggestions,
    pushToHistory,
    undo,
    redo
  } = useEmailCanvasStore()

  // Initialize WebSocket provider for real-time collaboration
  useEffect(() => {
    if (!campaignId) return

    // Set up WebSocket provider
    const wsProvider = new WebsocketProvider(
      process.env.NEXT_PUBLIC_CANVAS_WS_URL || process.env.CANVAS_WS_URL || 'wss://canvas-ws.justmaily.com',
      `email-canvas-${campaignId}`,
      ydoc
    )

    // Set user info for awareness
    wsProvider.awareness.setLocalStateField('user', {
      id: userId,
      name: 'User', // Would normally get from user profile
      color: `#${Math.floor(Math.random() * 16777215).toString(16)}`
    })

    // Handle connection status
    wsProvider.on('status', (event: { status: string }) => {
      if (event.status === 'connected') {
        setIsConnecting(false)
        toast({
          title: 'Connected to collaboration server',
          type: 'success',
          duration: 3000
        })
      } else if (event.status === 'disconnected') {
        setIsConnecting(true)
        toast({
          title: 'Disconnected from collaboration server',
          description: 'Attempting to reconnect...',
          type: 'warning'
        })
      }
    })

    // Update awareness when other users connect/disconnect
    wsProvider.awareness.on('change', () => {
      const states = wsProvider.awareness.getStates()
      const users: any[] = []

      states.forEach((state, clientId) => {
        if (state.user && clientId !== wsProvider.awareness.clientID) {
          users.push({
            id: state.user.id,
            name: state.user.name,
            color: state.user.color,
            clientId
          })
        }
      })

      setActiveUsers(users)
    })

    setProvider(wsProvider)

    return () => {
      wsProvider.disconnect()
    }
  }, [campaignId, userId, ydoc, toast])

  // Load initial content
  useEffect(() => {
    const loadCanvasContent = async () => {
      if (!campaignId) return

      try {
        // Either use provided initial content or fetch from API
        const content = initialContent || await apiHelpers.fetchCanvasContent(campaignId)

        if (content && tldrawAppRef.current) {
          tldrawAppRef.current.loadDocument(content)
          pushToHistory(content)
        }
      } catch (error) {
        console.error('Failed to load canvas content:', error)
        toast({
          title: 'Failed to load content',
          description: 'There was an error loading the email content.',
          type: 'error'
        })
      }
    }

    if (tldrawAppRef.current) {
      loadCanvasContent()
    }
  }, [campaignId, initialContent, pushToHistory, toast, tldrawAppRef.current])

  // Register email card shapes when the app is mounted
  const handleMount = useCallback((app: TldrawApp) => {
    tldrawAppRef.current = app

    // Register email-specific shapes
    EmailCardRegistry.registerShapes(app)

    // Initialize the app with empty email document if needed
    if (!initialContent) {
      // Create initial document structure with proper page settings
      const pageId = 'page';

      // Set page properties
      app.setPageState(pageId, {
        id: pageId,
        selectedIds: [],
        size: [800, 1200],
        backgroundColor: '#f8f9fa'
      })
    }
  }, [initialContent])

  // Handle canvas changes
  const handleChange = useCallback((state: any) => {
    if (!tldrawAppRef.current || readOnly) return

    // Update cursor position for AI suggestions
    const point = tldrawAppRef.current.inputs.currentPoint
    if (point) {
      setCursorPosition({ x: point[0], y: point[1] })
    }

    // Save changes and notify parent
    const doc = state.document
    if (onChange && doc) {
      onChange(doc)
    }

    // Push to history for undo/redo
    pushToHistory(doc)
  }, [onChange, pushToHistory, readOnly])

  // Save the current canvas state
  const handleSave = async () => {
    if (!tldrawAppRef.current || readOnly) return

    setIsSaving(true)
    try {
      const doc = tldrawAppRef.current.document
      await apiHelpers.saveCanvasContent(campaignId, doc)

      toast({
        title: 'Email saved',
        type: 'success',
        duration: 2000
      })
    } catch (error) {
      console.error('Failed to save canvas content:', error)
      toast({
        title: 'Save failed',
        description: 'There was an error saving the email content.',
        type: 'error'
      })
    } finally {
      setIsSaving(false)
    }
  }

  // Export canvas to HTML
  const handleExport = async () => {
    if (!tldrawAppRef.current) return

    setIsExporting(true)
    try {
      const result = await apiHelpers.exportCanvasToHtml(campaignId)

      if (onExport && result?.html) {
        onExport(result.html)
      }

      toast({
        title: 'Email exported',
        type: 'success',
        duration: 2000
      })
    } catch (error) {
      console.error('Failed to export canvas to HTML:', error)
      toast({
        title: 'Export failed',
        description: 'There was an error exporting the email content.',
        type: 'error'
      })
    } finally {
      setIsExporting(false)
    }
  }

  // Request AI suggestions
  const handleRequestSuggestion = async () => {
    if (!tldrawAppRef.current) return

    try {
      const canvasState = tldrawAppRef.current.document

      // Safe way to work with shapes that might be undefined
      const documentShapes = canvasState.shapes || {};
      const shapesCount = Object.keys(documentShapes).length;

      // Extract text content from canvas for better suggestions
      const textContent = Object.entries(documentShapes)
        .map(([_, shape]) => shape)
        .filter((shape) =>
          shape.type === 'email-text'
        )
        .map((shape: any) =>
          shape.props?.content?.text || ''
        ).join('\n\n');

      // Request suggestions
      await requestAiSuggestion({
        canvasState,
        contentText: textContent,
        campaignId,
        shapes: shapesCount,
        suggestionType: 'content'
      })
    } catch (error) {
      console.error('Failed to request AI suggestion:', error)
      toast({
        title: 'AI suggestion failed',
        description: 'There was an error generating AI suggestions.',
        type: 'error'
      })
    }
  }

  // Apply AI suggestion to canvas
  const handleApplySuggestion = (suggestion: any) => {
    if (!tldrawAppRef.current || readOnly) return

    try {
      const app = tldrawAppRef.current

      if (suggestion.type === 'content') {
        // Create a new text shape with the suggestion content
        const id = app.createShapeId()

        app.createShape({
          id,
          type: 'email-text',
          point: suggestion.position || [100, 100],
          size: [400, 200],
          props: {
            content: { text: suggestion.content },
            styles: { fontSize: 16, color: '#000000' }
          }
        })

        app.select(id)
      } else if (suggestion.type === 'design' && suggestion.changes) {
        // Apply design changes
        suggestion.changes.forEach((change: any) => {
          if (change.operation === 'update' && change.shapeId) {
            app.updateShape({
              id: change.shapeId,
              ...change.properties
            })
          } else if (change.operation === 'create') {
            const id = app.createShapeId()
            app.createShape({
              id,
              ...change.shape
            })
          }
        })
      }

      // Track that the suggestion was applied
      applyAiSuggestion(suggestion)

      toast({
        title: 'Applied suggestion',
        type: 'success',
        duration: 2000
      })
    } catch (error) {
      console.error('Failed to apply AI suggestion:', error)
      toast({
        title: 'Failed to apply suggestion',
        description: 'There was an error applying the AI suggestion.',
        type: 'error'
      })
    }
  }

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Skip if input or text area is focused
      if (
        ['INPUT', 'TEXTAREA', 'SELECT'].includes(
          (document.activeElement?.tagName || '').toUpperCase()
        )
      ) {
        return
      }

      // CMD/CTRL + S: Save
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault()
        handleSave()
      }

      // CMD/CTRL + Z: Undo
      if ((e.metaKey || e.ctrlKey) && !e.shiftKey && e.key === 'z') {
        e.preventDefault()
        const previousState = undo()
        if (previousState && tldrawAppRef.current) {
          tldrawAppRef.current.loadDocument(previousState)
        }
      }

      // CMD/CTRL + SHIFT + Z or CMD/CTRL + Y: Redo
      if (((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'z') ||
          ((e.metaKey || e.ctrlKey) && e.key === 'y')) {
        e.preventDefault()
        const nextState = redo()
        if (nextState && tldrawAppRef.current) {
          tldrawAppRef.current.loadDocument(nextState)
        }
      }

      // P key: Toggle preview mode
      if (e.key === 'p' && !e.metaKey && !e.ctrlKey && !e.altKey) {
        e.preventDefault()
        setPreviewMode(!previewMode)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleSave, undo, redo, previewMode])

  // Add a new shape to the canvas
  const addShape = (shapeType: string) => {
    if (!tldrawAppRef.current || readOnly) return

    const app = tldrawAppRef.current
    const id = app.createShapeId()
    const point = app.inputs.currentPoint || [100, 100]

    switch (shapeType) {
      case 'text':
        app.createShape({
          id,
          type: 'email-text',
          point,
          size: [300, 100],
          props: {
            content: { text: 'Enter your text here' },
            styles: { fontSize: 16, color: '#000000' }
          }
        })
        break

      case 'image':
        app.createShape({
          id,
          type: 'email-image',
          point,
          size: [300, 200],
          props: {
            content: {
              src: 'https://placehold.co/600x400?text=Select+Image',
              alt: 'Placeholder image'
            },
            styles: { borderRadius: 0, objectFit: 'contain' }
          }
        })
        break

      case 'button':
        app.createShape({
          id,
          type: 'email-button',
          point,
          size: [200, 50],
          props: {
            content: {
              text: 'Click here',
              href: '#'
            },
            styles: {
              backgroundColor: '#0070f3',
              color: '#ffffff',
              fontSize: 16,
              borderRadius: 4,
              textAlign: 'center',
              fontWeight: 'bold'
            }
          }
        })
        break

      case 'divider':
        app.createShape({
          id,
          type: 'email-divider',
          point,
          size: [400, 10],
          props: {
            content: { type: 'solid' },
            styles: {
              color: '#e0e0e0',
              thickness: 1,
              margin: { top: 0, bottom: 0 }
            }
          }
        })
        break

      case 'spacer':
        app.createShape({
          id,
          type: 'email-spacer',
          point,
          size: [400, 50],
          props: {
            content: { height: 50 },
            styles: {}
          }
        })
        break

      case 'product':
        app.createShape({
          id,
          type: 'email-product',
          point,
          size: [400, 300],
          props: {
            content: {
              title: 'Product Name',
              description: 'Product description',
              price: 99.99,
              currency: 'USD',
              imageSrc: 'https://placehold.co/600x400?text=Product+Image',
              productUrl: '#'
            },
            styles: {
              layout: 'vertical',
              borderRadius: 4,
              padding: 16,
              backgroundColor: '#ffffff',
              titleColor: '#000000',
              descriptionColor: '#666666',
              priceColor: '#000000'
            }
          }
        })
        break

      case 'dynamic':
        app.createShape({
          id,
          type: 'email-dynamic',
          point,
          size: [400, 100],
          props: {
            content: {
              type: 'personalization',
              variable: 'user.firstName',
              defaultContent: 'Hello there'
            },
            styles: {
              backgroundColor: '#f0f9ff',
              border: '1px dashed #0070f3',
              borderRadius: 4,
              padding: 8
            }
          }
        })
        break
    }

    // Select the new shape
    app.select(id)
  }

  // Render loading state
  if (isConnecting) {
    return (
      <div className="flex items-center justify-center h-full w-full bg-background/50">
        <div className="text-center">
          <Spinner size="lg" className="mx-auto mb-4" />
          <p className="text-muted-foreground">Connecting to collaboration server...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="relative h-full flex">
      {/* Main canvas */}
      <div className={`flex-1 relative ${previewMode ? 'overflow-auto' : ''}`}>
        {previewMode ? (
          <div className="max-w-[800px] mx-auto my-8 shadow-xl rounded-lg overflow-hidden">
            <div className="bg-primary text-primary-foreground p-4">
              <div className="flex justify-between items-center">
                <h3 className="font-medium">Email Preview</h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setPreviewMode(false)}
                >
                  <XMarkIcon className="w-4 h-4 mr-1" />
                  Close Preview
                </Button>
              </div>
            </div>
            <div className="bg-white p-4">
              {/* This would be replaced by actual preview HTML in production */}
              <div className="preview-placeholder bg-gray-50 h-[600px] flex items-center justify-center">
                <p className="text-muted-foreground">Email preview will appear here</p>
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* Toolbar */}
            <div className="absolute top-4 left-4 z-10 flex gap-2">
              <IconButton
                onClick={() => { const prevState = undo(); if (prevState && tldrawAppRef.current) tldrawAppRef.current.loadDocument(prevState); }}
                disabled={readOnly}
                title="Undo"
                variant="ghost"
              >
                <ArrowUturnLeftIcon className="w-4 h-4" />
              </IconButton>
              <IconButton
                onClick={() => { const nextState = redo(); if (nextState && tldrawAppRef.current) tldrawAppRef.current.loadDocument(nextState); }}
                disabled={readOnly}
                title="Redo"
                variant="ghost"
              >
                <ArrowUturnRightIcon className="w-4 h-4" />
              </IconButton>
              <div className="w-px h-6 bg-border mx-1" />
              <IconButton
                onClick={() => setPreviewMode(true)}
                title="Preview Email"
                variant="ghost"
              >
                <EyeIcon className="w-4 h-4" />
              </IconButton>
              <IconButton
                onClick={handleSave}
                disabled={readOnly || isSaving}
                title="Save Email"
                variant="ghost"
              >
                {isSaving ? (
                  <Spinner size="sm" />
                ) : (
                  <ArrowDownTrayIcon className="w-4 h-4" />
                )}
              </IconButton>
              <div className="w-px h-6 bg-border mx-1" />
              <IconButton
                onClick={handleExport}
                disabled={isExporting}
                title="Export to HTML"
                variant="ghost"
              >
                {isExporting ? (
                  <Spinner size="sm" />
                ) : (
                  <ArrowDownTrayIcon className="w-4 h-4" />
                )}
              </IconButton>
            </div>

            {/* Element adder */}
            <div className="absolute top-4 right-4 z-10">
              <div className="relative group">
                <Button
                  size="sm"
                  variant="outline"
                  className="gap-1"
                  disabled={readOnly}
                >
                  <PlusIcon className="w-4 h-4" />
                  Add Element
                </Button>
                <div className="absolute right-0 mt-1 hidden group-hover:block bg-card shadow-lg rounded-md border p-2 w-48">
                  <ul className="space-y-1 text-sm">
                    <li>
                      <button
                        onClick={() => addShape('text')}
                        className="w-full px-2 py-1 text-left rounded hover:bg-accent flex items-center"
                      >
                        <span className="w-4 h-4 mr-2 text-primary">T</span>
                        Text
                      </button>
                    </li>
                    <li>
                      <button
                        onClick={() => addShape('image')}
                        className="w-full px-2 py-1 text-left rounded hover:bg-accent flex items-center"
                      >
                        <span className="w-4 h-4 mr-2 text-primary">📷</span>
                        Image
                      </button>
                    </li>
                    <li>
                      <button
                        onClick={() => addShape('button')}
                        className="w-full px-2 py-1 text-left rounded hover:bg-accent flex items-center"
                      >
                        <span className="w-4 h-4 mr-2 text-primary">🔘</span>
                        Button
                      </button>
                    </li>
                    <li>
                      <button
                        onClick={() => addShape('divider')}
                        className="w-full px-2 py-1 text-left rounded hover:bg-accent flex items-center"
                      >
                        <span className="w-4 h-4 mr-2 text-primary">―</span>
                        Divider
                      </button>
                    </li>
                    <li>
                      <button
                        onClick={() => addShape('spacer')}
                        className="w-full px-2 py-1 text-left rounded hover:bg-accent flex items-center"
                      >
                        <span className="w-4 h-4 mr-2 text-primary">⎯</span>
                        Spacer
                      </button>
                    </li>
                    <li>
                      <button
                        onClick={() => addShape('product')}
                        className="w-full px-2 py-1 text-left rounded hover:bg-accent flex items-center"
                      >
                        <span className="w-4 h-4 mr-2 text-primary">🛍️</span>
                        Product
                      </button>
                    </li>
                    <li>
                      <button
                        onClick={() => addShape('dynamic')}
                        className="w-full px-2 py-1 text-left rounded hover:bg-accent flex items-center"
                      >
                        <span className="w-4 h-4 mr-2 text-primary">✨</span>
                        Dynamic Content
                      </button>
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            {/* AI Assistant toggle */}
            <div className="absolute bottom-4 right-4 z-10">
              <Button
                onClick={() => setShowAiPanel(!showAiPanel)}
                className="gap-1"
                variant={showAiPanel ? "default" : "outline"}
              >
                {showAiPanel ? (
                  <XMarkIcon className="w-4 h-4" />
                ) : (
                  <LightBulbIcon className="w-4 h-4" />
                )}
                {showAiPanel ? "Close Assistant" : "AI Assistant"}
              </Button>
            </div>

            {/* Active users indicator */}
            {activeUsers.length > 0 && (
              <div className="absolute bottom-4 left-4 z-10">
                <div className="flex items-center gap-1 bg-black/10 rounded-full px-3 py-1">
                  <ChatBubbleLeftRightIcon className="w-4 h-4 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">{activeUsers.length} active</span>
                  <div className="flex -space-x-2 ml-1">
                    {activeUsers.slice(0, 3).map((user) => (
                      <div
                        key={user.clientId}
                        className="w-6 h-6 rounded-full flex items-center justify-center text-xs text-white"
                        style={{ backgroundColor: user.color }}
                        title={user.name}
                      >
                        {user.name.charAt(0)}
                      </div>
                    ))}
                    {activeUsers.length > 3 && (
                      <div className="w-6 h-6 rounded-full bg-muted flex items-center justify-center text-xs">
                        +{activeUsers.length - 3}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* tldraw canvas */}
            <Tldraw
              showMenu={false}
              showPages={false}
              showStyles={!readOnly}
              showTools={!readOnly}
              showUI={!readOnly}
              readOnly={readOnly}
              onMount={handleMount}
              onChange={handleChange}
            />
          </>
        )}
      </div>

      {/* AI Assistant panel */}
      {showAiPanel && !previewMode && (
        <div className="w-80 h-full border-l bg-background shadow-xl overflow-hidden">
          <AiAssistantPanel
            contentSuggestions={aiSuggestions}
            designSuggestions={designSuggestions}
            isGenerating={isGenerating}
            onRequestSuggestion={handleRequestSuggestion}
            onApplySuggestion={handleApplySuggestion}
            campaignId={campaignId}
          />
        </div>
      )}
    </div>
  )
}
