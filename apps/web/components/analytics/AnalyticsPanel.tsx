"use client"

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { 
  BarChart, PieChart, LineChart, ArrowUp, ArrowDown, 
  ChevronUp, ChevronDown, Maximize2, Minimize2, 
  RefreshCw, Download, Filter, Calendar
} from 'lucide-react';

// Types
interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon?: React.ReactNode;
  className?: string;
}

interface InsightProps {
  id: string;
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  actionable: boolean;
  action?: string;
}

interface AnalyticsPanelProps {
  className?: string;
  metrics?: {
    opens: number;
    clicks: number;
    conversions: number;
    unsubscribes: number;
  };
  insights?: InsightProps[];
  isLoading?: boolean;
  dateRange?: {
    start: Date;
    end: Date;
  };
  onDateRangeChange?: (range: { start: Date; end: Date }) => void;
  onRefresh?: () => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

// MetricCard Component
function MetricCard({ title, value, change, changeLabel, icon, className }: MetricCardProps) {
  return (
    <div className={cn("bg-card rounded-lg p-4 shadow-sm", className)}>
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
        {icon && <div className="text-muted-foreground">{icon}</div>}
      </div>
      
      <div className="text-2xl font-bold mb-1">{value}</div>
      
      {typeof change !== 'undefined' && (
        <div className="flex items-center text-xs">
          <span className={cn(
            "flex items-center font-medium",
            change > 0 ? "text-green-600" : change < 0 ? "text-red-600" : "text-muted-foreground"
          )}>
            {change > 0 ? (
              <ArrowUp className="w-3 h-3 mr-1" />
            ) : change < 0 ? (
              <ArrowDown className="w-3 h-3 mr-1" />
            ) : null}
            {Math.abs(change)}%
          </span>
          
          {changeLabel && (
            <span className="text-muted-foreground ml-1">
              {changeLabel}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

// InsightItem Component
function InsightItem({ insight, onActionClick }: { 
  insight: InsightProps; 
  onActionClick?: (id: string) => void;
}) {
  return (
    <div className="border-b border-border last:border-0 py-3">
      <div className="flex items-start gap-3">
        <div className={cn(
          "w-2 h-2 rounded-full mt-1.5",
          insight.priority === 'high' ? "bg-red-500" : 
          insight.priority === 'medium' ? "bg-yellow-500" : 
          "bg-blue-500"
        )} />
        
        <div className="flex-1">
          <h4 className="font-medium text-sm mb-1">{insight.title}</h4>
          <p className="text-sm text-muted-foreground mb-2">{insight.description}</p>
          
          {insight.actionable && insight.action && (
            <button 
              className="text-xs text-primary font-medium hover:underline"
              onClick={() => onActionClick?.(insight.id)}
            >
              {insight.action}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export function AnalyticsPanel({
  className,
  metrics = { opens: 0, clicks: 0, conversions: 0, unsubscribes: 0 },
  insights = [],
  isLoading = false,
  dateRange = { start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), end: new Date() },
  onDateRangeChange,
  onRefresh,
  isCollapsed = false,
  onToggleCollapse,
}: AnalyticsPanelProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'insights' | 'comparison'>('overview');
  
  // Toggle collapse state
  const handleToggleCollapse = () => {
    onToggleCollapse?.();
  };
  
  // Handle refresh
  const handleRefresh = () => {
    onRefresh?.();
  };
  
  // Format date for display
  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Header */}
      <div className="px-4 py-2 border-b border-border flex items-center justify-between">
        <div className="flex items-center">
          <h2 className="font-medium text-sm">Analytics</h2>
          
          <div className="ml-4 flex space-x-1 bg-muted/30 p-0.5 rounded-md">
            <button 
              className={cn(
                "px-3 py-1 text-xs rounded",
                activeTab === 'overview' ? "bg-background shadow-sm" : "text-muted-foreground"
              )}
              onClick={() => setActiveTab('overview')}
            >
              Overview
            </button>
            
            <button 
              className={cn(
                "px-3 py-1 text-xs rounded",
                activeTab === 'insights' ? "bg-background shadow-sm" : "text-muted-foreground"
              )}
              onClick={() => setActiveTab('insights')}
            >
              Insights
            </button>
            
            <button 
              className={cn(
                "px-3 py-1 text-xs rounded",
                activeTab === 'comparison' ? "bg-background shadow-sm" : "text-muted-foreground"
              )}
              onClick={() => setActiveTab('comparison')}
            >
              Comparison
            </button>
          </div>
          
          <div className="ml-4 flex items-center text-xs text-muted-foreground">
            <Calendar className="w-3.5 h-3.5 mr-1" />
            <span>{formatDate(dateRange.start)} - {formatDate(dateRange.end)}</span>
          </div>
        </div>
        
        <div className="flex items-center space-x-1">
          <button 
            className="p-1 rounded hover:bg-muted"
            onClick={handleRefresh}
            title="Refresh data"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          
          <button 
            className="p-1 rounded hover:bg-muted"
            title="Download report"
          >
            <Download className="w-4 h-4" />
          </button>
          
          <button 
            className="p-1 rounded hover:bg-muted"
            title="Filter data"
          >
            <Filter className="w-4 h-4" />
          </button>
          
          <button 
            className="p-1 rounded hover:bg-muted"
            onClick={handleToggleCollapse}
            title={isCollapsed ? "Expand" : "Collapse"}
          >
            {isCollapsed ? (
              <Maximize2 className="w-4 h-4" />
            ) : (
              <Minimize2 className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>
      
      {/* Content */}
      {!isCollapsed && (
        <div className="flex-1 overflow-auto p-4">
          {activeTab === 'overview' && (
            <div className="space-y-4">
              {/* Metrics Cards */}
              <div className="grid grid-cols-4 gap-4">
                <MetricCard 
                  title="Opens" 
                  value={metrics.opens.toLocaleString()}
                  change={12.5}
                  changeLabel="vs last period"
                  icon={<BarChart className="w-4 h-4" />}
                />
                
                <MetricCard 
                  title="Clicks" 
                  value={metrics.clicks.toLocaleString()}
                  change={8.3}
                  changeLabel="vs last period"
                  icon={<LineChart className="w-4 h-4" />}
                />
                
                <MetricCard 
                  title="Conversions" 
                  value={metrics.conversions.toLocaleString()}
                  change={-2.1}
                  changeLabel="vs last period"
                  icon={<PieChart className="w-4 h-4" />}
                />
                
                <MetricCard 
                  title="Unsubscribes" 
                  value={metrics.unsubscribes.toLocaleString()}
                  change={-5.7}
                  changeLabel="vs last period"
                  icon={<BarChart className="w-4 h-4" />}
                />
              </div>
              
              {/* Charts Placeholder */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-card rounded-lg p-4 shadow-sm h-48 flex items-center justify-center">
                  <div className="text-center text-muted-foreground">
                    <BarChart className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">Opens & Clicks Over Time</p>
                  </div>
                </div>
                
                <div className="bg-card rounded-lg p-4 shadow-sm h-48 flex items-center justify-center">
                  <div className="text-center text-muted-foreground">
                    <PieChart className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">Engagement by Device</p>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {activeTab === 'insights' && (
            <div className="bg-card rounded-lg shadow-sm">
              <div className="p-3 border-b border-border">
                <h3 className="font-medium text-sm">AI-Generated Insights</h3>
              </div>
              
              <div className="divide-y divide-border">
                {insights.length > 0 ? (
                  insights.map(insight => (
                    <InsightItem 
                      key={insight.id} 
                      insight={insight} 
                      onActionClick={(id) => console.log('Action clicked for insight:', id)}
                    />
                  ))
                ) : (
                  <div className="p-6 text-center text-muted-foreground">
                    <p>No insights available for the current data.</p>
                  </div>
                )}
              </div>
            </div>
          )}
          
          {activeTab === 'comparison' && (
            <div className="bg-card rounded-lg p-4 shadow-sm h-64 flex items-center justify-center">
              <div className="text-center text-muted-foreground">
                <LineChart className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm mb-1">Campaign Performance Comparison</p>
                <p className="text-xs">Select campaigns to compare their performance metrics</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
