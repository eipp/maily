import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { CollaborativeCanvas } from '../CollaborativeCanvas';
import { canvasPerformance } from '@/utils/canvasPerformance';
import { useOptimizedCollaboration } from '@/hooks/useOptimizedCollaboration';

// Mock the dependencies
jest.mock('@/utils/canvasPerformance', () => ({
  canvasPerformance: {
    startMetric: jest.fn(),
    endMetric: jest.fn(),
    getReport: jest.fn().mockReturnValue({
      metrics: {},
      averages: {},
      counts: {},
    }),
  },
}));

jest.mock('@/hooks/useOptimizedCollaboration', () => ({
  useOptimizedCollaboration: jest.fn(),
  useThrottledCursorUpdate: jest.fn().mockReturnValue(jest.fn()),
}));

jest.mock('next-auth/react', () => ({
  useSession: jest.fn().mockReturnValue({
    data: {
      user: {
        id: 'test-user-id',
        name: 'Test User',
      },
    },
  }),
}));

jest.mock('nanoid', () => ({
  nanoid: jest.fn().mockReturnValue('test-id'),
}));

// Mock Konva and react-konva
jest.mock('react-konva', () => ({
  Stage: ({ children, ...props }) => (
    <div data-testid="mock-stage" {...props}>
      {children}
    </div>
  ),
  Layer: ({ children, ...props }) => (
    <div data-testid="mock-layer" {...props}>
      {children}
    </div>
  ),
  Group: ({ children, ...props }) => (
    <div data-testid="mock-group" {...props}>
      {children}
    </div>
  ),
  Rect: props => <div data-testid="mock-rect" {...props} />,
  Circle: props => <div data-testid="mock-circle" {...props} />,
  Line: props => <div data-testid="mock-line" {...props} />,
  Text: props => <div data-testid="mock-text" {...props} />,
}));

// Mock the Canvas and Shapes components
jest.mock('../Canvas', () => ({
  Canvas: ({ children, onViewportChange }) => {
    React.useEffect(() => {
      // Simulate viewport change
      onViewportChange({
        visibleRect: { x: 0, y: 0, width: 800, height: 600 },
        scale: 1,
        pointerPosition: { x: 100, y: 100 },
      });
    }, [onViewportChange]);

    return (
      <div data-testid="virtualized-canvas">
        {children}
      </div>
    );
  },
}));

jest.mock('../Shapes', () => ({
  Shapes: ({ shapes, onShapeClick, onShapeDragStart, onShapeDragEnd }) => (
    <div data-testid="virtualized-shapes">
      {shapes.map(shape => (
        <div
          key={shape.id}
          data-testid={`shape-${shape.type}`}
          onClick={() => onShapeClick(shape.id)}
          onMouseDown={() => onShapeDragStart(shape.id)}
          onMouseUp={() => onShapeDragEnd(shape.id, 100, 100)}
        >
          {shape.type}
        </div>
      ))}
    </div>
  ),
}));

describe('CollaborativeCanvas', () => {
  beforeEach(() => {
    // Setup mock for useOptimizedCollaboration
    const mockBroadcastUpdate = jest.fn();
    const mockUpdateCursor = jest.fn();
    const mockGetData = jest.fn().mockReturnValue({ shapes: [] });
    const mockOnUpdate = jest.fn().mockReturnValue(jest.fn());

    (useOptimizedCollaboration as jest.Mock).mockReturnValue([
      {
        isConnected: true,
        isConnecting: false,
        connectedUsers: [
          { clientId: 'user1', name: 'User 1', color: '#FF5733', cursor: { x: 100, y: 100 } },
        ],
      },
      {
        connect: jest.fn(),
        disconnect: jest.fn(),
        broadcastUpdate: mockBroadcastUpdate,
        getData: mockGetData,
        updateCursor: mockUpdateCursor,
        updateAwareness: jest.fn(),
        onUpdate: mockOnUpdate,
        onConnectionChange: jest.fn().mockReturnValue(jest.fn()),
        onAwarenessChange: jest.fn().mockReturnValue(jest.fn()),
      },
    ]);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders the canvas with toolbar', () => {
    render(<CollaborativeCanvas canvasId="test-canvas" />);

    // Check if toolbar buttons are rendered
    expect(screen.getByText('Select')).toBeInTheDocument();
    expect(screen.getByText('Rectangle')).toBeInTheDocument();
    expect(screen.getByText('Circle')).toBeInTheDocument();
    expect(screen.getByText('Line')).toBeInTheDocument();
    expect(screen.getByText('Freehand')).toBeInTheDocument();
    expect(screen.getByText('Text')).toBeInTheDocument();
    expect(screen.getByText('Eraser')).toBeInTheDocument();

    // Check if canvas is rendered
    expect(screen.getByTestId('virtualized-canvas')).toBeInTheDocument();
    expect(screen.getByTestId('virtualized-shapes')).toBeInTheDocument();
  });

  it('loads initial state correctly', async () => {
    const initialState = JSON.stringify([
      {
        id: 'shape1',
        type: 'rect',
        x: 100,
        y: 100,
        width: 100,
        height: 100,
        fill: '#FF5733',
      },
    ]);

    render(<CollaborativeCanvas canvasId="test-canvas" initialState={initialState} />);

    // Wait for the shapes to be rendered
    await waitFor(() => {
      expect(screen.getByTestId('shape-rect')).toBeInTheDocument();
    });
  });

  it('handles tool selection', () => {
    render(<CollaborativeCanvas canvasId="test-canvas" />);

    // Click on rectangle tool
    fireEvent.click(screen.getByText('Rectangle'));

    // Click on circle tool
    fireEvent.click(screen.getByText('Circle'));

    // Click on line tool
    fireEvent.click(screen.getByText('Line'));

    // Click on freehand tool
    fireEvent.click(screen.getByText('Freehand'));

    // Click on text tool
    fireEvent.click(screen.getByText('Text'));

    // Click on eraser tool
    fireEvent.click(screen.getByText('Eraser'));

    // Click on select tool
    fireEvent.click(screen.getByText('Select'));
  });

  it('shows connected users', () => {
    render(<CollaborativeCanvas canvasId="test-canvas" />);

    // Check if user cursor is rendered
    const userCursors = screen.getAllByText('User 1');
    expect(userCursors.length).toBeGreaterThan(0);
  });

  it('handles save functionality', async () => {
    const mockOnSave = jest.fn();
    render(<CollaborativeCanvas canvasId="test-canvas" onSave={mockOnSave} />);

    // Click on save button
    fireEvent.click(screen.getByText('Save'));

    // Check if onSave was called
    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalled();
    });
  });

  it('respects readOnly mode', () => {
    render(<CollaborativeCanvas canvasId="test-canvas" readOnly={true} />);

    // Check if toolbar buttons are disabled
    const selectButton = screen.getByText('Select').closest('button');
    expect(selectButton).toBeDisabled();

    const rectangleButton = screen.getByText('Rectangle').closest('button');
    expect(rectangleButton).toBeDisabled();
  });

  it('measures performance', async () => {
    render(<CollaborativeCanvas canvasId="test-canvas" />);

    // Check if performance metrics are being tracked
    await waitFor(() => {
      expect(canvasPerformance.startMetric).toHaveBeenCalled();
      expect(canvasPerformance.endMetric).toHaveBeenCalled();
    });
  });
});
