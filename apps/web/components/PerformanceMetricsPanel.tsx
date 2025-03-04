'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Activity,
  X,
  RefreshCw,
  DownloadCloud,
  Cpu,
  Timer,
  Users,
  Layers,
  AlertCircle,
  LineChart,
  Pause,
  Play,
} from 'lucide-react';
import { Button } from '@/components/Button';
import { canvasPerformance } from '@/utils/canvasPerformance';

// Interfaces
interface MetricsSnapshot {
  fps: number;
  renderTime: number;
  collaborationLatency: number;
  memory: number;
  shapeCount: number;
  connectedUsers: number;
  layerCount: number;
  timestamp: number;
  warnings: PerformanceWarning[];
}

interface PerformanceWarning {
  type: 'high-render-time' | 'low-fps' | 'high-latency' | 'high-memory-usage';
  message: string;
  value: number;
  threshold: number;
  timestamp: number;
}

interface ChartData {
  labels: string[];
  datasets: {
    fps: number[];
    renderTime: number[];
    collaborationLatency: number[];
    memory: number[];
  };
}

interface PerformanceMetricsPanelProps {
  showPanel: boolean;
  onTogglePanel: () => void;
  connectedUsers: number;
  shapeCount: number;
  layerCount: number;
  className?: string;
}

const MAX_HISTORY_LENGTH = 60; // 1 minute at 1 reading per second
const WARNING_THRESHOLDS = {
  fps: 30, // Warning if FPS drops below 30
  renderTime: 16, // Warning if render time exceeds 16ms (60fps threshold)
  collaborationLatency: 300, // Warning if latency exceeds 300ms
  memory: 100 * 1024 * 1024, // Warning if memory exceeds 100MB
};

export function PerformanceMetricsPanel({
  showPanel,
  onTogglePanel,
  connectedUsers,
  shapeCount,
  layerCount,
  className = '',
}: PerformanceMetricsPanelProps) {
  // State
  const [isPaused, setIsPaused] = useState(false);
  const [metricsHistory, setMetricsHistory] = useState<MetricsSnapshot[]>([]);
  const [chartData, setChartData] = useState<ChartData>({
    labels: [],
    datasets: {
      fps: [],
      renderTime: [],
      collaborationLatency: [],
      memory: [],
    },
  });
  const [activeMetric, setActiveMetric] = useState<
    'fps' | 'renderTime' | 'collaborationLatency' | 'memory'
  >('fps');
  const [warnings, setWarnings] = useState<PerformanceWarning[]>([]);
  
  // Refs
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const metricsIntervalRef = useRef<NodeJS.Timeout | null>(null);
  
  // Calculate current metrics
  const calculateCurrentMetrics = (): MetricsSnapshot => {
    const performanceReport = canvasPerformance.generateReport();
    
    // Calculate metrics
    const renderTimeMetrics = performanceReport.metrics.filter((m) => m.name.startsWith('render'));
    const avgRenderTime = renderTimeMetrics.length > 0
      ? renderTimeMetrics.reduce((sum, m) => sum + (m.duration || 0), 0) / renderTimeMetrics.length
      : 0;
    
    const collaborationMetrics = performanceReport.metrics.filter((m) => m.name.startsWith('collaboration'));
    const avgCollabLatency = collaborationMetrics.length > 0
      ? collaborationMetrics.reduce((sum, m) => sum + (m.duration || 0), 0) / collaborationMetrics.length
      : 0;
    
    // Calculate FPS based on render time
    const fps = avgRenderTime > 0 ? Math.min(60, Math.round(1000 / avgRenderTime)) : 60;
    
    // Get memory usage
    const memory = window.performance && window.performance.memory
      // @ts-ignore - memory is a non-standard property
      ? window.performance.memory.usedJSHeapSize
      : 0;
    
    // Check for warnings
    const newWarnings: PerformanceWarning[] = [];
    
    if (fps < WARNING_THRESHOLDS.fps) {
      newWarnings.push({
        type: 'low-fps',
        message: `Low FPS: ${fps} (threshold: ${WARNING_THRESHOLDS.fps})`,
        value: fps,
        threshold: WARNING_THRESHOLDS.fps,
        timestamp: Date.now(),
      });
    }
    
    if (avgRenderTime > WARNING_THRESHOLDS.renderTime) {
      newWarnings.push({
        type: 'high-render-time',
        message: `High render time: ${Math.round(avgRenderTime)}ms (threshold: ${WARNING_THRESHOLDS.renderTime}ms)`,
        value: avgRenderTime,
        threshold: WARNING_THRESHOLDS.renderTime,
        timestamp: Date.now(),
      });
    }
    
    if (avgCollabLatency > WARNING_THRESHOLDS.collaborationLatency) {
      newWarnings.push({
        type: 'high-latency',
        message: `High collaboration latency: ${Math.round(avgCollabLatency)}ms (threshold: ${WARNING_THRESHOLDS.collaborationLatency}ms)`,
        value: avgCollabLatency,
        threshold: WARNING_THRESHOLDS.collaborationLatency,
        timestamp: Date.now(),
      });
    }
    
    if (memory > WARNING_THRESHOLDS.memory) {
      newWarnings.push({
        type: 'high-memory-usage',
        message: `High memory usage: ${Math.round(memory / 1024 / 1024)}MB (threshold: ${Math.round(WARNING_THRESHOLDS.memory / 1024 / 1024)}MB)`,
        value: memory,
        threshold: WARNING_THRESHOLDS.memory,
        timestamp: Date.now(),
      });
    }
    
    // Add new warnings to state
    if (newWarnings.length > 0) {
      setWarnings((prev) => [...prev, ...newWarnings]);
    }
    
    // Clear metrics after processing
    canvasPerformance.clearMetrics();
    
    return {
      fps,
      renderTime: Math.round(avgRenderTime),
      collaborationLatency: Math.round(avgCollabLatency),
      memory,
      shapeCount,
      connectedUsers,
      layerCount,
      timestamp: Date.now(),
      warnings: newWarnings,
    };
  };
  
  // Draw chart
  const drawChart = (chartData: ChartData) => {
    if (!canvasRef.current) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Get data for active metric
    const metricData = chartData.datasets[activeMetric];
    
    // Calculate min and max values for scaling
    let min = Math.min(...metricData);
    let max = Math.max(...metricData);
    
    // Ensure min and max are different
    if (min === max) {
      min = Math.max(0, min - min * 0.1);
      max = max + max * 0.1;
    }
    
    // Add padding
    min = Math.max(0, min - (max - min) * 0.1);
    max = max + (max - min) * 0.1;
    
    // Draw background grid
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 0.5;
    
    // Horizontal grid lines
    const gridLines = 5;
    for (let i = 0; i <= gridLines; i++) {
      const y = height - (height * i) / gridLines;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
      
      // Add labels
      if (i > 0 && i < gridLines) {
        const value = min + ((max - min) * i) / gridLines;
        ctx.fillStyle = '#666';
        ctx.font = '10px Arial';
        ctx.textAlign = 'left';
        ctx.fillText(formatValue(value, activeMetric), 2, y - 2);
      }
    }
    
    // Draw data line
    if (metricData.length > 1) {
      ctx.strokeStyle = getColorForMetric(activeMetric);
      ctx.lineWidth = 2;
      ctx.beginPath();
      
      for (let i = 0; i < metricData.length; i++) {
        const x = (width * i) / (metricData.length - 1);
        const normalizedValue = (metricData[i] - min) / (max - min);
        const y = height - normalizedValue * height;
        
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      
      ctx.stroke();
    }
    
    // Add title
    ctx.fillStyle = '#333';
    ctx.font = 'bold 12px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(getMetricTitle(activeMetric), width / 2, 15);
    
    // Add min and max labels
    ctx.fillStyle = '#666';
    ctx.font = '10px Arial';
    ctx.textAlign = 'left';
    ctx.fillText(formatValue(min, activeMetric), 2, height - 2);
    ctx.textAlign = 'right';
    ctx.fillText(formatValue(max, activeMetric), width - 2, 15);
  };
  
  // Format value based on metric
  const formatValue = (value: number, metric: string): string => {
    switch (metric) {
      case 'fps':
        return `${Math.round(value)} fps`;
      case 'renderTime':
        return `${Math.round(value)} ms`;
      case 'collaborationLatency':
        return `${Math.round(value)} ms`;
      case 'memory':
        return `${Math.round(value / 1024 / 1024)} MB`;
      default:
        return `${Math.round(value)}`;
    }
  };
  
  // Get color for metric
  const getColorForMetric = (metric: string): string => {
    switch (metric) {
      case 'fps':
        return '#4CAF50';
      case 'renderTime':
        return '#FF9800';
      case 'collaborationLatency':
        return '#2196F3';
      case 'memory':
        return '#9C27B0';
      default:
        return '#333';
    }
  };
  
  // Get title for metric
  const getMetricTitle = (metric: string): string => {
    switch (metric) {
      case 'fps':
        return 'Frames Per Second';
      case 'renderTime':
        return 'Render Time (ms)';
      case 'collaborationLatency':
        return 'Collaboration Latency (ms)';
      case 'memory':
        return 'Memory Usage (MB)';
      default:
        return metric;
    }
  };
  
  // Start collecting metrics
  useEffect(() => {
    if (showPanel && !isPaused) {
      // Initial collection
      const initialMetrics = calculateCurrentMetrics();
      setMetricsHistory([initialMetrics]);
      
      // Set up interval for collecting metrics
      metricsIntervalRef.current = setInterval(() => {
        const metrics = calculateCurrentMetrics();
        
        setMetricsHistory((prev) => {
          const newHistory = [...prev, metrics];
          // Limit history length
          if (newHistory.length > MAX_HISTORY_LENGTH) {
            return newHistory.slice(newHistory.length - MAX_HISTORY_LENGTH);
          }
          return newHistory;
        });
      }, 1000);
    }
    
    return () => {
      if (metricsIntervalRef.current) {
        clearInterval(metricsIntervalRef.current);
        metricsIntervalRef.current = null;
      }
    };
  }, [showPanel, isPaused, shapeCount, connectedUsers, layerCount]);
  
  // Update chart data when metrics history changes
  useEffect(() => {
    if (metricsHistory.length === 0) return;
    
    const labels = metricsHistory.map((m) => {
      const date = new Date(m.timestamp);
      return `${date.getHours()}:${date.getMinutes()}:${date.getSeconds()}`;
    });
    
    const newChartData: ChartData = {
      labels,
      datasets: {
        fps: metricsHistory.map((m) => m.fps),
        renderTime: metricsHistory.map((m) => m.renderTime),
        collaborationLatency: metricsHistory.map((m) => m.collaborationLatency),
        memory: metricsHistory.map((m) => m.memory / 1024 / 1024), // Convert to MB
      },
    };
    
    setChartData(newChartData);
    drawChart(newChartData);
  }, [metricsHistory, activeMetric]);
  
  // Update chart when window resizes
  useEffect(() => {
    const handleResize = () => {
      if (canvasRef.current && canvasRef.current.parentElement) {
        canvasRef.current.width = canvasRef.current.parentElement.clientWidth;
        drawChart(chartData);
      }
    };
    
    window.addEventListener('resize', handleResize);
    handleResize();
    
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [chartData]);
  
  // Helper to get latest metrics
  const latestMetrics = metricsHistory[metricsHistory.length - 1] || {
    fps: 0,
    renderTime: 0,
    collaborationLatency: 0,
    memory: 0,
    shapeCount: 0,
    connectedUsers: 0,
    layerCount: 0,
    timestamp: Date.now(),
    warnings: [],
  };
  
  // Download performance data as JSON
  const handleDownloadData = () => {
    const data = JSON.stringify(metricsHistory, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `canvas-performance-${new Date().toISOString()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };
  
  // Reset warnings
  const handleResetWarnings = () => {
    setWarnings([]);
  };
  
  // Toggle pause/resume
  const handleTogglePause = () => {
    setIsPaused((prev) => !prev);
  };
  
  // If panel is not shown, render only the toggle button
  if (!showPanel) {
    return (
      <Button
        variant="ghost"
        size="sm"
        onClick={onTogglePanel}
        className={`flex h-10 w-10 items-center justify-center rounded-full bg-white/80 shadow-md backdrop-blur-sm dark:bg-gray-800/80 ${
          warnings.length > 0 ? 'animate-pulse text-amber-500' : ''
        } ${className}`}
        aria-label="Show performance metrics"
      >
        <Activity className="h-5 w-5" />
        {warnings.length > 0 && (
          <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] text-white">
            {warnings.length}
          </span>
        )}
      </Button>
    );
  }
  
  return (
    <div
      className={`flex h-full w-80 flex-col rounded-lg border border-gray-200 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-800 ${className}`}
      data-testid="performance-metrics-panel"
    >
      {/* Panel header */}
      <div className="flex items-center justify-between border-b border-gray-200 p-3 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          <h3 className="text-sm font-semibold">Performance Metrics</h3>
        </div>
        
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            className="p-1"
            onClick={handleTogglePause}
            aria-label={isPaused ? 'Resume' : 'Pause'}
          >
            {isPaused ? <Play className="h-4 w-4" /> : <Pause className="h-4 w-4" />}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="p-1"
            onClick={handleDownloadData}
            aria-label="Download performance data"
          >
            <DownloadCloud className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="p-1"
            onClick={onTogglePanel}
            aria-label="Close performance metrics panel"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>
      
      {/* Current metrics */}
      <div className="grid grid-cols-2 gap-2 p-3">
        <div className="flex items-center gap-2 rounded-md bg-gray-50 p-2 dark:bg-gray-700">
          <Cpu className="h-4 w-4 text-green-500" />
          <div>
            <p className="text-xs text-gray-500">FPS</p>
            <p className="font-medium">{latestMetrics.fps}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2 rounded-md bg-gray-50 p-2 dark:bg-gray-700">
          <Timer className="h-4 w-4 text-orange-500" />
          <div>
            <p className="text-xs text-gray-500">Render Time</p>
            <p className="font-medium">{latestMetrics.renderTime}ms</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2 rounded-md bg-gray-50 p-2 dark:bg-gray-700">
          <LineChart className="h-4 w-4 text-blue-500" />
          <div>
            <p className="text-xs text-gray-500">Latency</p>
            <p className="font-medium">{latestMetrics.collaborationLatency}ms</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2 rounded-md bg-gray-50 p-2 dark:bg-gray-700">
          <RefreshCw className="h-4 w-4 text-purple-500" />
          <div>
            <p className="text-xs text-gray-500">Memory</p>
            <p className="font-medium">
              {Math.round(latestMetrics.memory / 1024 / 1024)}MB
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2 rounded-md bg-gray-50 p-2 dark:bg-gray-700">
          <Layers className="h-4 w-4 text-teal-500" />
          <div>
            <p className="text-xs text-gray-500">Shapes / Layers</p>
            <p className="font-medium">
              {latestMetrics.shapeCount} / {latestMetrics.layerCount}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2 rounded-md bg-gray-50 p-2 dark:bg-gray-700">
          <Users className="h-4 w-4 text-indigo-500" />
          <div>
            <p className="text-xs text-gray-500">Users</p>
            <p className="font-medium">{latestMetrics.connectedUsers}</p>
          </div>
        </div>
      </div>
      
      {/* Chart */}
      <div className="flex-grow p-3">
        <div className="flex justify-between mb-2">
          <h4 className="text-sm font-medium">Performance Chart</h4>
          <div className="flex gap-1">
            <Button
              variant={activeMetric === 'fps' ? 'primary' : 'ghost'}
              size="sm"
              className="h-6 px-2 py-0 text-xs"
              onClick={() => setActiveMetric('fps')}
            >
              FPS
            </Button>
            <Button
              variant={activeMetric === 'renderTime' ? 'primary' : 'ghost'}
              size="sm"
              className="h-6 px-2 py-0 text-xs"
              onClick={() => setActiveMetric('renderTime')}
            >
              Render
            </Button>
            <Button
              variant={activeMetric === 'collaborationLatency' ? 'primary' : 'ghost'}
              size="sm"
              className="h-6 px-2 py-0 text-xs"
              onClick={() => setActiveMetric('collaborationLatency')}
            >
              Latency
            </Button>
            <Button
              variant={activeMetric === 'memory' ? 'primary' : 'ghost'}
              size="sm"
              className="h-6 px-2 py-0 text-xs"
              onClick={() => setActiveMetric('memory')}
            >
              Mem
            </Button>
          </div>
        </div>
        <div className="h-32 w-full relative">
          <canvas
            ref={canvasRef}
            className="absolute inset-0 h-full w-full"
            height={120}
          />
        </div>
      </div>
      
      {/* Warnings */}
      <div className="border-t border-gray-200 p-3 dark:border-gray-700">
        <div className="mb-2 flex items-center justify-between">
          <h4 className="text-sm font-medium">Warnings</h4>
          {warnings.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              className="h-6 px-2 py-0 text-xs"
              onClick={handleResetWarnings}
            >
              Clear
            </Button>
          )}
        </div>
        
        <div className="max-h-40 overflow-y-auto">
          {warnings.length === 0 ? (
            <p className="text-center text-xs text-gray-500">No warnings</p>
          ) : (
            <div className="space-y-2">
              {warnings.slice(-5).map((warning, index) => (
                <div
                  key={index}
                  className="flex items-start gap-2 rounded-md bg-amber-50 p-2 text-xs dark:bg-amber-900/20"
                >
                  <AlertCircle className="h-4 w-4 shrink-0 text-amber-500" />
                  <div>
                    <p className="font-medium">{warning.message}</p>
                    <p className="text-gray-500">
                      {new Date(warning.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}
              {warnings.length > 5 && (
                <p className="text-center text-xs text-gray-500">
                  +{warnings.length - 5} more warnings
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}