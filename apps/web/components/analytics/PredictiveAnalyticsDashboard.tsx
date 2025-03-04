"use client"

import React, { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { 
  TrendingUp, BarChart, PieChart, LineChart, ArrowUp, ArrowDown, 
  ChevronUp, ChevronDown, Zap, Filter, Calendar, ThumbsUp, ThumbsDown
} from 'lucide-react';
import { RealTimeAnalyticsDashboard } from './RealTimeAnalyticsDashboard';

// Types
interface PredictiveMetricProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  confidence?: number;
  trend?: 'up' | 'down' | 'stable';
}

interface RecommendationProps {
  id: string;
  title: string;
  description: string;
  confidenceScore: number;
  confidenceLevel: 'very_high' | 'high' | 'medium' | 'low' | 'very_low';
  confidenceExplanation: string;
  tags: string[];
  applied: boolean;
  onApply: (id: string) => void;
  onDismiss: (id: string) => void;
  onFeedback: (id: string, isPositive: boolean) => void;
}

interface PredictiveInsightProps {
  id: string;
  title: string;
  description: string;
  metric: string;
  prediction: number;
  confidence: number;
  timeframe: string;
}

interface PredictiveAnalyticsDashboardProps {
  className?: string;
  campaignId?: number;
  isLoading?: boolean;
  showRealTime?: boolean;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

// Helper function to get confidence level label
function getConfidenceLevelLabel(level: string): string {
  switch (level) {
    case 'very_high': return 'Very High Confidence';
    case 'high': return 'High Confidence';
    case 'medium': return 'Medium Confidence';
    case 'low': return 'Low Confidence';
    case 'very_low': return 'Very Low Confidence';
    default: return 'Unknown Confidence';
  }
}

// Helper function to get confidence level color classes
function getConfidenceLevelClasses(level: string): string {
  switch (level) {
    case 'very_high': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
    case 'high': return 'bg-green-50 text-green-700 dark:bg-green-900/70 dark:text-green-300';
    case 'medium': return 'bg-blue-50 text-blue-700 dark:bg-blue-900/70 dark:text-blue-300';
    case 'low': return 'bg-yellow-50 text-yellow-700 dark:bg-yellow-900/70 dark:text-yellow-300';
    case 'very_low': return 'bg-red-50 text-red-700 dark:bg-red-900/70 dark:text-red-300';
    default: return 'bg-gray-50 text-gray-700 dark:bg-gray-800 dark:text-gray-300';
  }
}

// Metric Card Component
function PredictiveMetric({ title, value, change, changeLabel, confidence, trend }: PredictiveMetricProps) {
  return (
    <div className="bg-card rounded-lg p-4 shadow-sm">
      <div className="flex justify-between items-start mb-3">
        <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
      </div>
      
      <div className="text-2xl font-bold mb-2">{value}</div>
      
      {typeof change !== 'undefined' && (
        <div className="flex items-center text-xs mb-1">
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
      
      {typeof confidence !== 'undefined' && (
        <div className="flex items-center mt-2">
          <div className="w-full bg-muted/50 rounded-full h-1.5">
            <div 
              className={cn(
                "h-1.5 rounded-full",
                confidence >= 80 ? "bg-green-500" :
                confidence >= 60 ? "bg-blue-500" :
                confidence >= 40 ? "bg-yellow-500" :
                "bg-red-500"
              )}
              style={{ width: `${confidence}%` }}
            ></div>
          </div>
          <span className="text-xs ml-2 text-muted-foreground">{confidence}% confidence</span>
        </div>
      )}
    </div>
  );
}

// Recommendation Item Component
function RecommendationItem({ 
  id, 
  title, 
  description, 
  confidenceScore, 
  confidenceLevel, 
  confidenceExplanation,
  tags,
  applied,
  onApply,
  onDismiss,
  onFeedback
}: RecommendationProps) {
  const [expanded, setExpanded] = useState(false);
  const [isApplied, setIsApplied] = useState(applied);
  
  // Apply the recommendation
  const handleApply = () => {
    setIsApplied(true);
    onApply(id);
  };
  
  // Dismiss the recommendation
  const handleDismiss = () => {
    onDismiss(id);
  };
  
  return (
    <div className={cn(
      "bg-card rounded-lg p-4 shadow-sm mb-4 border border-border",
      isApplied && "border-l-4 border-l-green-500"
    )}>
      <div className="flex justify-between">
        <div className="flex-1">
          <div className="flex items-start mb-2">
            <span className={cn(
              "text-xs px-2 py-0.5 rounded-full mr-2",
              getConfidenceLevelClasses(confidenceLevel)
            )}>
              {getConfidenceLevelLabel(confidenceLevel)}
            </span>
            
            {tags.map(tag => (
              <span key={tag} className="text-xs bg-muted/50 px-2 py-0.5 rounded-full mr-2">
                {tag}
              </span>
            ))}
          </div>
          
          <h3 className="font-medium text-base mb-1">{title}</h3>
          <p className="text-sm text-muted-foreground mb-3">{description}</p>
          
          <div className="flex items-center mb-2">
            <div className="w-full bg-muted/50 rounded-full h-1.5 mr-3">
              <div 
                className={cn(
                  "h-1.5 rounded-full",
                  confidenceScore >= 0.9 ? "bg-green-500" :
                  confidenceScore >= 0.7 ? "bg-blue-500" :
                  confidenceScore >= 0.5 ? "bg-yellow-500" :
                  confidenceScore >= 0.3 ? "bg-orange-500" :
                  "bg-red-500"
                )}
                style={{ width: `${confidenceScore * 100}%` }}
              ></div>
            </div>
            <span className="text-xs text-muted-foreground whitespace-nowrap">
              {Math.round(confidenceScore * 100)}% confidence
            </span>
          </div>
          
          <button 
            className="text-xs text-primary flex items-center"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? (
              <>
                <ChevronUp className="w-3 h-3 mr-1" /> Hide details
              </>
            ) : (
              <>
                <ChevronDown className="w-3 h-3 mr-1" /> Show explanation
              </>
            )}
          </button>
          
          {expanded && (
            <div className="mt-3 p-3 bg-muted/30 rounded-md text-xs text-muted-foreground">
              {confidenceExplanation}
            </div>
          )}
        </div>
        
        <div className="ml-4 flex flex-col space-y-2">
          {!isApplied ? (
            <>
              <button 
                className="px-3 py-1.5 bg-primary text-primary-foreground rounded-md text-xs font-medium"
                onClick={handleApply}
              >
                Apply
              </button>
              
              <button 
                className="px-3 py-1.5 bg-muted hover:bg-muted/80 rounded-md text-xs font-medium"
                onClick={handleDismiss}
              >
                Dismiss
              </button>
            </>
          ) : (
            <div className="px-3 py-1.5 bg-green-100 text-green-700 rounded-md text-xs font-medium dark:bg-green-900/30 dark:text-green-300">
              Applied
            </div>
          )}
          
          <div className="flex justify-center mt-2 space-x-1">
            <button 
              className="p-1 rounded hover:bg-muted"
              onClick={() => onFeedback(id, true)}
              title="This was helpful"
            >
              <ThumbsUp className="w-3.5 h-3.5 text-muted-foreground" />
            </button>
            
            <button 
              className="p-1 rounded hover:bg-muted"
              onClick={() => onFeedback(id, false)}
              title="This wasn't helpful"
            >
              <ThumbsDown className="w-3.5 h-3.5 text-muted-foreground" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Predictive Insight Item Component
function PredictiveInsightItem({ insight }: { insight: PredictiveInsightProps }) {
  return (
    <div className="bg-card rounded-lg p-4 shadow-sm mb-4">
      <h3 className="font-medium text-base mb-1">{insight.title}</h3>
      <p className="text-sm text-muted-foreground mb-3">{insight.description}</p>
      
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-baseline">
          <span className="text-lg font-bold">{insight.prediction}%</span>
          <span className="text-xs text-muted-foreground ml-1">{insight.metric}</span>
        </div>
        
        <span className="text-xs text-muted-foreground">{insight.timeframe}</span>
      </div>
      
      <div className="flex items-center">
        <div className="w-full bg-muted/50 rounded-full h-1.5 mr-3">
          <div 
            className={cn(
              "h-1.5 rounded-full",
              insight.confidence >= 80 ? "bg-green-500" :
              insight.confidence >= 60 ? "bg-blue-500" :
              insight.confidence >= 40 ? "bg-yellow-500" :
              "bg-red-500"
            )}
            style={{ width: `${insight.confidence}%` }}
          ></div>
        </div>
        <span className="text-xs text-muted-foreground whitespace-nowrap">
          {insight.confidence}% confidence
        </span>
      </div>
    </div>
  );
}

// Main Component
export function PredictiveAnalyticsDashboard({
  className,
  campaignId,
  isLoading = false,
  showRealTime = true,
  isCollapsed = false,
  onToggleCollapse
}: PredictiveAnalyticsDashboardProps) {
  // State
  const [activeTab, setActiveTab] = useState<'predictions' | 'recommendations' | 'realtime'>('predictions');
  const [recommendations, setRecommendations] = useState<RecommendationProps[]>([]);
  const [insights, setInsights] = useState<PredictiveInsightProps[]>([]);
  const [predictiveMetrics, setPredictiveMetrics] = useState<PredictiveMetricProps[]>([]);
  
  // Fetch data from API
  useEffect(() => {
    // In production, fetch from API instead of using mock data
    const fetchData = async () => {
      // For demonstration, use mock data
      const mockRecommendations: RecommendationProps[] = [
        {
          id: "rec1",
          title: "Optimize Email Send Time",
          description: "Sending emails at 2:00 PM on Tuesdays shows 15% higher open rates for your target audience.",
          confidenceScore: 0.92,
          confidenceLevel: "very_high",
          confidenceExplanation: "Based on 1,245 data points with 92% statistical confidence. Analysis of your previous campaigns shows clear engagement patterns during this time window.",
          tags: ["timing", "engagement"],
          applied: false,
          onApply: (id) => console.log("Applied recommendation:", id),
          onDismiss: (id) => console.log("Dismissed recommendation:", id),
          onFeedback: (id, isPositive) => console.log("Feedback for recommendation:", id, isPositive)
        },
        {
          id: "rec2",
          title: "Adjust Subject Line Length",
          description: "Using subject lines between 5-7 words has increased open rates by 8% for similar campaigns.",
          confidenceScore: 0.76,
          confidenceLevel: "high",
          confidenceExplanation: "Comparative analysis with 76% confidence across 52 similar campaigns. Your subject lines are currently averaging 10.3 words.",
          tags: ["subject", "open-rate"],
          applied: false,
          onApply: (id) => console.log("Applied recommendation:", id),
          onDismiss: (id) => console.log("Dismissed recommendation:", id),
          onFeedback: (id, isPositive) => console.log("Feedback for recommendation:", id, isPositive)
        },
        {
          id: "rec3",
          title: "Segment Inactive Subscribers",
          description: "Create a re-engagement campaign for subscribers who haven't opened emails in 60+ days.",
          confidenceScore: 0.65,
          confidenceLevel: "medium",
          confidenceExplanation: "Based on trend analysis with 65% confidence. You have 428 subscribers (18% of your list) who haven't engaged in 60+ days.",
          tags: ["segmentation", "re-engagement"],
          applied: true,
          onApply: (id) => console.log("Applied recommendation:", id),
          onDismiss: (id) => console.log("Dismissed recommendation:", id),
          onFeedback: (id, isPositive) => console.log("Feedback for recommendation:", id, isPositive)
        }
      ];
      
      const mockInsights: PredictiveInsightProps[] = [
        {
          id: "insight1",
          title: "Expected Open Rate",
          description: "Based on your recent campaigns and current engagement trends",
          metric: "open rate",
          prediction: 24,
          confidence: 85,
          timeframe: "Next 7 days"
        },
        {
          id: "insight2",
          title: "Expected Click-Through Rate",
          description: "Projected engagement based on content and audience analysis",
          metric: "CTR",
          prediction: 3.8,
          confidence: 72,
          timeframe: "Next 7 days"
        },
        {
          id: "insight3",
          title: "Conversion Rate Forecast",
          description: "Estimated based on current trends and seasonal patterns",
          metric: "conversion",
          prediction: 1.9,
          confidence: 67,
          timeframe: "Next 30 days"
        }
      ];
      
      const mockMetrics: PredictiveMetricProps[] = [
        {
          title: "Predicted Open Rate",
          value: "24%",
          change: 3.5,
          changeLabel: "vs. last campaign",
          confidence: 85
        },
        {
          title: "Projected CTR",
          value: "3.8%",
          change: -0.7,
          changeLabel: "vs. last campaign",
          confidence: 72
        },
        {
          title: "Expected Engagement",
          value: "High",
          confidence: 89
        },
        {
          title: "Optimal Send Time",
          value: "Tue, 2:00 PM",
          confidence: 92
        }
      ];
      
      // Set state
      setRecommendations(mockRecommendations);
      setInsights(mockInsights);
      setPredictiveMetrics(mockMetrics);
    };
    
    fetchData();
  }, [campaignId]);
  
  // Handle recommendation actions
  const handleApplyRecommendation = (id: string) => {
    // In production, call API to apply recommendation
    const updatedRecommendations = recommendations.map(rec => 
      rec.id === id ? { ...rec, applied: true } : rec
    );
    setRecommendations(updatedRecommendations);
  };
  
  const handleDismissRecommendation = (id: string) => {
    // In production, call API to dismiss recommendation
    const updatedRecommendations = recommendations.filter(rec => rec.id !== id);
    setRecommendations(updatedRecommendations);
  };
  
  const handleFeedback = (id: string, isPositive: boolean) => {
    // In production, call API to send feedback
    console.log(`Feedback for recommendation ${id}: ${isPositive ? 'positive' : 'negative'}`);
  };
  
  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Header */}
      <div className="px-4 py-2 border-b border-border flex items-center justify-between">
        <div className="flex items-center">
          <h2 className="font-medium text-sm">Predictive Analytics</h2>
          
          <div className="ml-4 flex space-x-1 bg-muted/30 p-0.5 rounded-md">
            <button 
              className={cn(
                "px-3 py-1 text-xs rounded",
                activeTab === 'predictions' ? "bg-background shadow-sm" : "text-muted-foreground"
              )}
              onClick={() => setActiveTab('predictions')}
            >
              Predictions
            </button>
            
            <button 
              className={cn(
                "px-3 py-1 text-xs rounded",
                activeTab === 'recommendations' ? "bg-background shadow-sm" : "text-muted-foreground"
              )}
              onClick={() => setActiveTab('recommendations')}
            >
              Recommendations
            </button>
            
            {showRealTime && (
              <button 
                className={cn(
                  "px-3 py-1 text-xs rounded flex items-center",
                  activeTab === 'realtime' ? "bg-background shadow-sm" : "text-muted-foreground"
                )}
                onClick={() => setActiveTab('realtime')}
              >
                <Zap className="w-3 h-3 mr-1" /> Real-time
              </button>
            )}
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button 
            className="p-1 rounded hover:bg-muted"
            title="Filter"
          >
            <Filter className="w-4 h-4" />
          </button>
          
          <button 
            className="p-1 rounded hover:bg-muted"
            title="Date range"
          >
            <Calendar className="w-4 h-4" />
          </button>
          
          {onToggleCollapse && (
            <button 
              className="p-1 rounded hover:bg-muted"
              onClick={onToggleCollapse}
              title={isCollapsed ? "Expand" : "Collapse"}
            >
              {isCollapsed ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
            </button>
          )}
        </div>
      </div>
      
      {/* Content */}
      {!isCollapsed && (
        <div className="flex-1 overflow-auto p-4">
          {activeTab === 'predictions' && (
            <div className="space-y-6">
              <div className="grid grid-cols-4 gap-4">
                {predictiveMetrics.map((metric, index) => (
                  <PredictiveMetric 
                    key={index}
                    title={metric.title}
                    value={metric.value}
                    change={metric.change}
                    changeLabel={metric.changeLabel}
                    confidence={metric.confidence}
                    trend={metric.trend}
                  />
                ))}
              </div>
              
              <div>
                <h3 className="text-sm font-medium mb-3">Future Performance Insights</h3>
                <div className="space-y-4">
                  {insights.map(insight => (
                    <PredictiveInsightItem key={insight.id} insight={insight} />
                  ))}
                </div>
              </div>
            </div>
          )}
          
          {activeTab === 'recommendations' && (
            <div>
              <h3 className="text-sm font-medium mb-3">Personalized Recommendations</h3>
              <div>
                {recommendations.map(recommendation => (
                  <RecommendationItem 
                    key={recommendation.id}
                    {...recommendation}
                    onApply={handleApplyRecommendation}
                    onDismiss={handleDismissRecommendation}
                    onFeedback={handleFeedback}
                  />
                ))}
                
                {recommendations.length === 0 && (
                  <div className="bg-card rounded-lg p-6 text-center">
                    <p className="text-muted-foreground">No recommendations available at this time.</p>
                  </div>
                )}
              </div>
            </div>
          )}
          
          {activeTab === 'realtime' && (
            <RealTimeAnalyticsDashboard 
              campaignId={campaignId}
              className="mt-2"
            />
          )}
        </div>
      )}
    </div>
  );
}