# Cognitive Canvas Documentation

## Overview

The Cognitive Canvas is an interactive drawing and design environment that supports real-time collaboration, layer management, and performance optimization. It's designed to enable email template creation, collaborative design, and intuitive visual editing of content.

## Key Features

- **Interactive Canvas**: Drag, drop, and manipulate shapes and elements
- **Real-time Collaboration**: Multiple users can edit simultaneously
- **Layer Management**: Organize content with layers, opacity control, and locking
- **Performance Optimization**: Web workers and efficient rendering for smooth experience
- **React DnD Integration**: Drag and drop elements from external sources
- **Trust Verification**: Visual indication of verified content
- **Performance Metrics**: Real-time monitoring of canvas performance

## Components

### EnhancedCanvas

The main canvas component that orchestrates all functionality:

```tsx
<EnhancedCanvas
  roomId="unique-room-id"  // For collaboration
  userId="user-123"        // Current user identifier
  verificationStatus={{    // Optional trust verification
    isVerified: true,
    showVerificationLayer: true,
    certificateData: {
      id: 'cert-123',
      issuer: 'Maily Trust',
      timestamp: '2023-01-01T00:00:00Z'
    }
  }}
  onToggleVerificationLayer={() => {}}  // Handler for toggling
/>
```

### LayersPanel

Manages layers with drag-and-drop reordering:

```tsx
<LayersPanel
  layers={layers}
  activeLayerId={activeLayerId}
  selectedLayerIds={selectedLayerIds}
  onLayerClick={(id) => {}}
  onLayerSelect={(id) => {}}
  onToggleVisibility={(id) => {}}
  onToggleLock={(id) => {}}
  onDeleteLayer={(id) => {}}
  onAddLayer={() => {}}
  onOpacityChange={(id, value) => {}}
  onReorderLayers={(layers) => {}}
  onToggleAllLayers={(visible) => {}}
  showPanel={showLayersPanel}
  onTogglePanel={() => {}}
/>
```

### PerformanceMetricsPanel

Displays real-time performance data:

```tsx
<PerformanceMetricsPanel
  showPanel={showPerformanceMetrics}
  onTogglePanel={() => {}}
  connectedUsers={3}
  shapeCount={25}
  layerCount={4}
/>
```

## Integration with React DnD

The canvas supports drag and drop from external sources through React DnD:

```tsx
// Create a draggable component
function DraggableShape({ type, children }) {
  const [{ isDragging }, drag] = useDrag(() => ({
    type: 'shape',
    item: { type: 'shape', shapeType: type },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  }));
  
  return (
    <div ref={drag}>
      {children}
    </div>
  );
}

// Use in your component
<DndContext>
  <div>
    <DraggableShape type="rect">Rectangle</DraggableShape>
    <EnhancedCanvas />
  </div>
</DndContext>
```

## Real-time Collaboration

The canvas uses Yjs and WebSockets for real-time collaboration:

- User presence awareness
- Cursor position sharing
- Conflict resolution with operational transformation
- Synchronized layer management
- Connection status indication

## Trust Verification System

The Cognitive Canvas includes a comprehensive blockchain-based trust verification system:

### Verification Process

1. **Content Verification**
   - Canvas content is hashed using a secure algorithm
   - The hash is stored on blockchain for immutable verification
   - A verification certificate is generated with metadata

2. **Verification Visualization**
   - Verified content displays a trust badge in the UI
   - Verification layer shows blockchain transaction details
   - QR code provides external verification capability

3. **Certificate Management**
   - Each verified canvas has an associated certificate
   - Certificates include issuer, timestamp, and content hash
   - External verification URL for third-party validation

### Integration API

The backend visualization service provides verification endpoints:

```python
# Verify and visualize canvas content
verification_data = await visualization_service.verify_and_visualize_canvas(
    canvas_id=canvas_id,
    content=canvas_content
)

# Get verification badge
badge_data = await visualization_service.get_trust_verification_badge(canvas_id)

# Generate verification overlay
overlay = await visualization_service.generate_trust_verification_overlay(canvas_id)
```

### Frontend Components

The verification system includes these frontend components:

- **VerificationBadge**: Displays verification status and certificate info
- **VerificationLayer**: Visualization overlay for verified content
- **CertificateViewer**: Detailed view of verification certificate

Example usage:

```tsx
<EnhancedCanvas
  verificationStatus={{
    isVerified: true, 
    showVerificationLayer: true,
    certificateData: {
      id: "cert-12345",
      issuer: "Maily Trust Authority",
      timestamp: "2024-03-01T12:00:00Z"
    }
  }}
  onToggleVerificationLayer={() => {
    // Toggle verification layer visibility
  }}
/>
```

## Performance Optimization

Several strategies are employed for performance:

- Web workers for heavy calculations
- Optimized rendering of visible elements
- Throttled updates to reduce network traffic
- Efficient state management
- Layer-based optimization

## Layer Management

Layers provide organization and control:

- Visibility toggle for each layer
- Layer locking to prevent edits
- Opacity control
- Drag-and-drop reordering
- Layer selection for bulk operations
- Layer thumbnails for visual identification

## Getting Started

To use the Cognitive Canvas in your application:

1. Import the necessary components:
   ```tsx
   import { EnhancedCanvas } from '@/components/EnhancedCanvas';
   import { DndContext } from '@/components/DndContext';
   ```

2. Set up your component:
   ```tsx
   export default function MyCanvasPage() {
     const [verificationStatus, setVerificationStatus] = useState({
       isVerified: true,
       showVerificationLayer: false,
     });
     
     return (
       <DndContext>
         <EnhancedCanvas
           roomId="my-canvas"
           userId="user-123"
           verificationStatus={verificationStatus}
           onToggleVerificationLayer={() => {
             setVerificationStatus(prev => ({
               ...prev,
               showVerificationLayer: !prev.showVerificationLayer
             }));
           }}
         />
       </DndContext>
     );
   }
   ```

3. For a complete working example, see `/apps/web/app/canvas-demo/page.tsx`.

## WebSocket Infrastructure

The WebSocket connection used for real-time collaboration can be configured through:

- Environment variable: `NEXT_PUBLIC_WEBSOCKET_URL`
- Default fallback: `wss://api.maily.app/ws/canvas`

### WebSocket Server

A dedicated WebSocket server handles real-time communication:

```bash
# Run the WebSocket server standalone for development
python scripts/run_websocket_server.py
```

The server provides:

- Connection management with room-based grouping
- Message buffering for disconnected clients
- Cross-service communication via Redis PubSub
- Heartbeat mechanism for connection health
- Standardized message format with type system
- Distributed tracing integration

### Message Types

The WebSocket service uses standardized message types:

- `CANVAS_UPDATE`: Shape/component changes on the canvas
- `STATUS_UPDATE`: User presence and system status changes
- `VISUALIZATION_LAYERS`: Layer updates for AI reasoning, performance, etc.
- `VERIFICATION`: Trust verification results and status
- `PERFORMANCE`: Metrics and analytics updates
- `PING`/`PONG`: Connection health checks

## Advanced Usage

### Custom Shape Types

You can extend the canvas with custom shape types by modifying:

1. The Shape interface in EnhancedCanvas.tsx
2. Adding render logic for your new shape type
3. Adding creation handling for the new shape type

### Backend Integration

The canvas integrates with backend services via WebSockets for:

- Trust verification from the blockchain service
- Real-time analytics from the analytics service
- Template storage and retrieval from the API

### Performance Tuning

For large canvases or complex applications:

- Increase the worker count for parallel processing
- Adjust throttling parameters for update frequency
- Enable layer-specific optimizations
- Use visibility culling for off-screen elements