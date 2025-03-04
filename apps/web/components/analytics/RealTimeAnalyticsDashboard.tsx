"use client"

import React, { useState, useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';
import { 
  Activity, BarChart, LineChart, TrendingUp, ArrowUpRight, 
  RefreshCw, AlertCircle, Clock, Users, Zap, 
  ChevronRight, Settings, PieChart
} from 'lucide-react';

interface RealTimeMetric {
  id: string;
  name: string;
  value: number;
  previousValue: number;
  unit: string;
  change: number;
  trend: 'up' | 'down' | 'stable';
  timestamp: string;
}

interface RealTimeEvent {
  id: string;
  type: string;
  message: string;
  timestamp: string;
  priority: 'high' | 'medium' | 'low';
  metadata?: Record<string, any>;
}

interface RealTimeAnalyticsDashboardProps {
  className?: string;
  campaignId?: number;
  userId?: number;
  refreshInterval?: number; // in seconds
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

// Mock WebSocket class for development
class WebSocketClient {
  private url: string;
  private socket: WebSocket | null = null;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectTimeout: number = 2000; // Start with 2 seconds
  private onMessageCallback: ((data: any) => void) | null = null;
  private onConnectCallback: (() => void) | null = null;
  private onDisconnectCallback: (() => void) | null = null;

  constructor(url: string) {
    this.url = url;
  }

  connect() {
    try {
      this.socket = new WebSocket(this.url);
      
      this.socket.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.reconnectTimeout = 2000; // Reset timeout on successful connection
        if (this.onConnectCallback) this.onConnectCallback();
      };
      
      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (this.onMessageCallback) this.onMessageCallback(data);
        } catch (e) {
          console.error('Error parsing WebSocket message', e);
        }
      };
      
      this.socket.onclose = () => {
        console.log('WebSocket disconnected');
        if (this.onDisconnectCallback) this.onDisconnectCallback();
        this.reconnect();
      };
      
      this.socket.onerror = (error) => {
        console.error('WebSocket error', error);
      };
    } catch (error) {
      console.error('Error connecting to WebSocket', error);
      this.reconnect();
    }
  }

  private reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Reconnecting in ${this.reconnectTimeout / 1000} seconds (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        this.connect();
      }, this.reconnectTimeout);
      
      // Exponential backoff
      this.reconnectTimeout = Math.min(this.reconnectTimeout * 1.5, 30000); // Cap at 30 seconds
    } else {
      console.log('Max reconnect attempts reached');
    }
  }

  send(data: any) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    } else {
      console.error('Cannot send: WebSocket is not open');
    }
  }

  onMessage(callback: (data: any) => void) {
    this.onMessageCallback = callback;
  }

  onConnect(callback: () => void) {
    this.onConnectCallback = callback;
  }

  onDisconnect(callback: () => void) {
    this.onDisconnectCallback = callback;
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }
}

// Real-time metric card component
function RealTimeMetricCard({ metric }: { metric: RealTimeMetric }) {
  return (
    <div className="bg-card rounded-lg p-4 shadow-sm">
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-sm font-medium text-muted-foreground">{metric.name}</h3>
        <span className="text-xs text-muted-foreground">
          {new Date(metric.timestamp).toLocaleTimeString()}
        </span>
      </div>
      
      <div className="flex items-baseline gap-2 mb-1">
        <div className="text-2xl font-bold">
          {metric.value.toLocaleString()}{metric.unit}
        </div>
        
        <div className={cn(
          "flex items-center text-xs font-medium",
          metric.change > 0 ? "text-green-600" : 
          metric.change < 0 ? "text-red-600" : 
          "text-muted-foreground"
        )}>
          {metric.change > 0 ? '+' : ''}{metric.change}%
          {metric.trend === 'up' && <ArrowUpRight className="h-3 w-3 ml-0.5" />}
          {metric.trend === 'down' && <TrendingUp className="h-3 w-3 ml-0.5 transform rotate-180" />}
        </div>
      </div>
      
      <div className="text-xs text-muted-foreground">
        vs previous {metric.value > metric.previousValue ? 'lower' : 'higher'}
      </div>
    </div>
  );
}

// Real-time event log component
function RealTimeEventLog({ events }: { events: RealTimeEvent[] }) {
  return (
    <div className="bg-card rounded-lg shadow-sm overflow-hidden">
      <div className="p-3 border-b border-border flex items-center justify-between">
        <h3 className="font-medium text-sm flex items-center">
          <Activity className="h-4 w-4 mr-2" /> Live Activity
        </h3>
        <span className="text-xs text-muted-foreground flex items-center">
          <Clock className="h-3 w-3 mr-1" /> Real-time
        </span>
      </div>
      
      <div className="max-h-[240px] overflow-y-auto p-0">
        {events.length === 0 ? (
          <div className="p-4 text-center text-muted-foreground">
            No activity recorded yet
          </div>
        ) : (
          <div className="divide-y divide-border">
            {events.map((event) => (
              <div key={event.id} className="p-3 hover:bg-muted/30 transition-colors">
                <div className="flex items-start gap-3">
                  <div className={cn(
                    "rounded-full w-2 h-2 mt-1.5",
                    event.priority === 'high' ? "bg-red-500" :
                    event.priority === 'medium' ? "bg-yellow-500" :
                    "bg-blue-500"
                  )} />
                  
                  <div className="flex-1">
                    <div className="flex justify-between items-start">
                      <span className="text-xs font-medium">
                        {event.type}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-sm mt-0.5">{event.message}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Real-time visualization placeholder
function RealTimeVisualization() {
  return (
    <div className="bg-card rounded-lg shadow-sm overflow-hidden">
      <div className="p-3 border-b border-border">
        <h3 className="font-medium text-sm flex items-center">
          <LineChart className="h-4 w-4 mr-2" /> Live Metrics Visualization
        </h3>
      </div>
      
      <div className="h-[200px] flex items-center justify-center bg-gradient-to-r from-muted/40 to-muted/20">
        <div className="text-center text-muted-foreground">
          <Activity className="h-8 w-8 mx-auto mb-2 animate-pulse" />
          <p className="text-sm">Real-time data visualization</p>
        </div>
      </div>
    </div>
  );
}

// Connection status indicator
function ConnectionStatus({ isConnected }: { isConnected: boolean }) {
  return (
    <div className="flex items-center">
      <div className={cn(
        "w-2 h-2 rounded-full mr-2",
        isConnected ? "bg-green-500" : "bg-red-500"
      )} />
      <span className="text-xs">
        {isConnected ? "Connected" : "Disconnected"}
      </span>
    </div>
  );
}

// Main component
export function RealTimeAnalyticsDashboard({
  className,
  campaignId,
  userId,
  refreshInterval = 5,
  isCollapsed = false,
  onToggleCollapse
}: RealTimeAnalyticsDashboardProps) {
  // State
  const [isConnected, setIsConnected] = useState(false);
  const [metrics, setMetrics] = useState<RealTimeMetric[]>([]);
  const [events, setEvents] = useState<RealTimeEvent[]>([]);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [activeUsers, setActiveUsers] = useState(0);
  const wsRef = useRef<WebSocketClient | null>(null);
  
  // Initialize WebSocket when component mounts
  useEffect(() => {
    // Generate WebSocket URL from the current host
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/analytics/ws`;
    
    // Create WebSocket client
    const ws = new WebSocketClient(wsUrl);
    wsRef.current = ws;
    
    // Setup callbacks
    ws.onConnect(() => {
      setIsConnected(true);
      
      // Send initialization data
      ws.send({
        type: 'subscribe',
        data: {
          userId,
          campaignId,
          metrics: ['opens', 'clicks', 'conversions', 'engagements']
        }
      });
    });
    
    ws.onDisconnect(() => {
      setIsConnected(false);
    });
    
    ws.onMessage((data) => {
      if (data.type === 'metrics') {
        setMetrics(data.metrics);
      } else if (data.type === 'event') {
        setEvents((prev) => [data.event, ...prev].slice(0, 50)); // Keep last 50 events
      } else if (data.type === 'users') {
        setActiveUsers(data.count);
      }
      
      setLastUpdated(new Date());
    });
    
    // Connect
    ws.connect();
    
    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.disconnect();
      }
    };
  }, [campaignId, userId]);
  
  // For development: generate mock data if no metrics
  useEffect(() => {
    if (metrics.length === 0) {
      const mockMetrics: RealTimeMetric[] = [
        {
          id: '1',
          name: 'Active Sessions',
          value: 157,
          previousValue: 142,
          unit: '',
          change: 10.6,
          trend: 'up',
          timestamp: new Date().toISOString()
        },
        {
          id: '2',
          name: 'Engagement Rate',
          value: 3.8,
          previousValue: 4.2,
          unit: '%',
          change: -9.5,
          trend: 'down',
          timestamp: new Date().toISOString()
        },
        {
          id: '3',
          name: 'Conversion Rate',
          value: 2.4,
          previousValue: 2.3,
          unit: '%',
          change: 4.3,
          trend: 'up',
          timestamp: new Date().toISOString()
        },
        {
          id: '4',
          name: 'Response Time',
          value: 284,
          previousValue: 310,
          unit: 'ms',
          change: -8.4,
          trend: 'down',
          timestamp: new Date().toISOString()
        },
      ];
      
      setMetrics(mockMetrics);
    }
    
    if (events.length === 0) {
      const mockEvents: RealTimeEvent[] = [
        {
          id: '1',
          type: 'Campaign Interaction',
          message: 'User clicked on promotional link in email campaign #1245',
          timestamp: new Date().toISOString(),
          priority: 'medium'
        },
        {
          id: '2',
          type: 'Recommendation Applied',
          message: 'Subject line optimization recommendation applied to campaign #1245',
          timestamp: new Date(Date.now() - 35000).toISOString(),
          priority: 'high'
        },
        {
          id: '3',
          type: 'Subscriber Activity',
          message: 'New subscriber joined mailing list from landing page',
          timestamp: new Date(Date.now() - 120000).toISOString(),
          priority: 'low'
        }
      ];
      
      setEvents(mockEvents);
      setActiveUsers(42);
    }
  }, [metrics.length, events.length]);
  
  // Manually refresh connection
  const handleRefresh = () => {
    if (wsRef.current) {
      wsRef.current.disconnect();
      setTimeout(() => {
        if (wsRef.current) wsRef.current.connect();
      }, 500);
    }
  };
  
  return (
    <div className={cn("flex flex-col h-full bg-background border border-border rounded-lg shadow-sm", className)}>
      {/* Header */}
      <div className="px-4 py-2 border-b border-border flex items-center justify-between">
        <div className="flex items-center">
          <h2 className="font-medium text-sm flex items-center">
            <Zap className="h-4 w-4 mr-2" /> Real-Time Analytics
          </h2>
          
          <div className="ml-4 text-xs text-muted-foreground">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <ConnectionStatus isConnected={isConnected} />
          
          <div className="flex items-center text-xs">
            <Users className="h-3.5 w-3.5 mr-1.5" />
            <span>{activeUsers} active</span>
          </div>
          
          <div className="flex items-center space-x-1">
            <button 
              onClick={handleRefresh}
              className="p-1.5 rounded hover:bg-muted"
              title="Refresh connection"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
            
            <button 
              className="p-1.5 rounded hover:bg-muted"
              title="Settings"
            >
              <Settings className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
      
      {/* Content */}
      {!isCollapsed && (
        <div className="flex-1 overflow-auto p-4 space-y-4">
          {/* Alert if disconnected */}
          {!isConnected && (
            <div className="bg-yellow-50 border border-yellow-200 p-3 rounded-lg flex items-center text-sm text-yellow-800 dark:bg-yellow-900/20 dark:border-yellow-800 dark:text-yellow-300">
              <AlertCircle className="h-5 w-5 mr-2 flex-shrink-0" />
              <div className="flex-1">
                Connection to real-time analytics stream lost. Attempting to reconnect...
              </div>
              <button 
                onClick={handleRefresh}
                className="ml-2 px-2 py-1 bg-yellow-100 hover:bg-yellow-200 rounded text-xs font-medium dark:bg-yellow-800 dark:hover:bg-yellow-700"
              >
                Reconnect
              </button>
            </div>
          )}
          
          {/* Metrics */}
          <div className="grid grid-cols-4 gap-4">
            {metrics.map((metric) => (
              <RealTimeMetricCard key={metric.id} metric={metric} />
            ))}
          </div>
          
          {/* Visualization and Activity Log */}
          <div className="grid grid-cols-3 gap-4">
            <div className="col-span-2">
              <RealTimeVisualization />
            </div>
            <div className="col-span-1">
              <RealTimeEventLog events={events} />
            </div>
          </div>
          
          {/* Recommendations */}
          <div className="bg-primary/5 border border-primary/10 rounded-lg p-4">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-sm font-medium flex items-center">
                <PieChart className="h-4 w-4 mr-2" /> Real-Time Recommendations
              </h3>
              <a href="#" className="text-xs text-primary flex items-center hover:underline">
                View all <ChevronRight className="h-3.5 w-3.5 ml-0.5" />
              </a>
            </div>
            
            <div className="space-y-3">
              <div className="bg-card rounded-md p-3">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-xs bg-primary/10 text-primary px-1.5 py-0.5 rounded-full">
                      High Confidence
                    </span>
                    <h4 className="text-sm font-medium mt-1.5">Adjust Send Time for Optimal Engagement</h4>
                    <p className="text-xs text-muted-foreground mt-1">
                      Based on real-time engagement patterns, sending at 2:00 PM could increase open rates by 15%.
                    </p>
                  </div>
                  <button className="text-xs bg-primary text-primary-foreground px-2.5 py-1 rounded hover:bg-primary/90">
                    Apply
                  </button>
                </div>
              </div>
              
              <div className="bg-card rounded-md p-3">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-xs bg-yellow-100 text-yellow-800 px-1.5 py-0.5 rounded-full dark:bg-yellow-900 dark:text-yellow-300">
                      Medium Confidence
                    </span>
                    <h4 className="text-sm font-medium mt-1.5">Optimize Subject Line</h4>
                    <p className="text-xs text-muted-foreground mt-1">
                      Current engagement suggests adding action-oriented words could improve click-through rate.
                    </p>
                  </div>
                  <button className="text-xs bg-primary text-primary-foreground px-2.5 py-1 rounded hover:bg-primary/90">
                    Apply
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}