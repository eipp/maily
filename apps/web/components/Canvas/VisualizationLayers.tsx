import React, { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { InfoIcon, EyeIcon, EyeOffIcon, BarChart2Icon, ShieldIcon, BrainIcon } from 'lucide-react';
import axios from 'axios';

interface VisualizationLayersProps {
  canvasId: string;
  campaignId?: string;
}

interface Layer {
  id: string;
  name: string;
  type: string;
  data: Record<string, any>;
  opacity: number;
  visible: boolean;
  created_at: string;
  updated_at: string;
}

interface AIReasoningLayer extends Layer {
  confidence_scores: Record<string, number>;
  reasoning_steps: Array<Record<string, any>>;
  model_info: Record<string, any>;
}

interface PerformanceLayer extends Layer {
  metrics: Record<string, any>;
  historical_data: Array<Record<string, any>>;
  benchmarks: Record<string, any>;
}

interface TrustVerificationLayer extends Layer {
  verification_status: string;
  certificate_data?: Record<string, any>;
  blockchain_info?: Record<string, any>;
}

const VisualizationLayers: React.FC<VisualizationLayersProps> = ({ canvasId, campaignId }) => {
  const [activeTab, setActiveTab] = useState('ai-reasoning');

  // Fetch visualization layers
  const { data: layers, isLoading, error, refetch } = useQuery({
    queryKey: ['visualization-layers', canvasId],
    queryFn: async () => {
      const response = await axios.get(`/api/v1/canvas/${canvasId}/visualization/layers`);
      return response.data;
    }
  });

  // Fetch performance metrics if campaign ID is provided
  const { data: performanceMetrics } = useQuery({
    queryKey: ['performance-metrics', canvasId, campaignId],
    queryFn: async () => {
      const url = campaignId 
        ? `/api/v1/canvas/${canvasId}/performance/metrics?campaign_id=${campaignId}`
        : `/api/v1/canvas/${canvasId}/performance/metrics`;
      const response = await axios.get(url);
      return response.data;
    },
    enabled: activeTab === 'performance'
  });

  // Fetch verification data
  const { data: verificationData } = useQuery({
    queryKey: ['verification-data', canvasId],
    queryFn: async () => {
      const response = await axios.get(`/api/v1/canvas/${canvasId}/verification`);
      return response.data;
    },
    enabled: activeTab === 'trust-verification'
  });

  // Update layer visibility mutation
  const updateVisibilityMutation = useMutation({
    mutationFn: async ({ layerId, visible, opacity }: { layerId: string; visible: boolean; opacity?: number }) => {
      const response = await axios.put(`/api/v1/canvas/${canvasId}/visualization/layers/${layerId}/visibility`, {
        visible,
        opacity
      });
      return response.data;
    },
    onSuccess: () => {
      refetch();
    }
  });

  // Handle layer visibility toggle
  const handleVisibilityToggle = (layerId: string, visible: boolean) => {
    updateVisibilityMutation.mutate({ layerId, visible });
  };

  // Handle layer opacity change
  const handleOpacityChange = (layerId: string, opacity: number) => {
    updateVisibilityMutation.mutate({ layerId, visible: true, opacity });
  };

  if (isLoading) {
    return <div className="flex items-center justify-center p-6">Loading visualization layers...</div>;
  }

  if (error) {
    return <div className="text-red-500 p-6">Error loading visualization layers</div>;
  }

  const aiReasoningLayer = layers?.ai_reasoning as AIReasoningLayer;
  const performanceLayer = layers?.performance as PerformanceLayer;
  const trustVerificationLayer = layers?.trust_verification as TrustVerificationLayer;

  return (
    <div className="visualization-layers">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Visualization Layers</h3>
        <div className="flex space-x-2">
          {/* Layer quick toggles */}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant={aiReasoningLayer?.visible ? "default" : "outline"}
                  size="sm"
                  onClick={() => handleVisibilityToggle('ai_reasoning', !aiReasoningLayer?.visible)}
                >
                  <BrainIcon className="h-4 w-4 mr-1" />
                  AI
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Toggle AI Reasoning Layer</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant={performanceLayer?.visible ? "default" : "outline"}
                  size="sm"
                  onClick={() => handleVisibilityToggle('performance', !performanceLayer?.visible)}
                >
                  <BarChart2Icon className="h-4 w-4 mr-1" />
                  Perf
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Toggle Performance Layer</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant={trustVerificationLayer?.visible ? "default" : "outline"}
                  size="sm"
                  onClick={() => handleVisibilityToggle('trust_verification', !trustVerificationLayer?.visible)}
                >
                  <ShieldIcon className="h-4 w-4 mr-1" />
                  Trust
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Toggle Trust Verification Layer</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid grid-cols-3 mb-4">
          <TabsTrigger value="ai-reasoning">AI Reasoning</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="trust-verification">Trust Verification</TabsTrigger>
        </TabsList>

        {/* AI Reasoning Tab */}
        <TabsContent value="ai-reasoning">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>AI Reasoning Layer</CardTitle>
                <Switch
                  checked={aiReasoningLayer?.visible}
                  onCheckedChange={(checked) => handleVisibilityToggle('ai_reasoning', checked)}
                />
              </div>
              <CardDescription>
                Visualize AI reasoning and confidence scores
              </CardDescription>
            </CardHeader>
            <CardContent>
              {aiReasoningLayer?.visible ? (
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium mb-1 block">Layer Opacity</label>
                    <Slider
                      value={[aiReasoningLayer?.opacity * 100]}
                      min={0}
                      max={100}
                      step={1}
                      onValueChange={(value) => handleOpacityChange('ai_reasoning', value[0] / 100)}
                    />
                  </div>

                  {/* Confidence Scores */}
                  <div>
                    <h4 className="text-sm font-medium mb-2">Confidence Scores</h4>
                    <div className="grid grid-cols-2 gap-2">
                      {Object.entries(aiReasoningLayer?.confidence_scores || {}).map(([key, value]) => (
                        <div key={key} className="flex items-center justify-between">
                          <span className="text-sm">{key}</span>
                          <Badge variant={value > 0.8 ? "success" : value > 0.5 ? "warning" : "destructive"}>
                            {(value * 100).toFixed(0)}%
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Reasoning Steps */}
                  <div>
                    <h4 className="text-sm font-medium mb-2">Reasoning Steps</h4>
                    <div className="space-y-2">
                      {(aiReasoningLayer?.reasoning_steps || []).map((step, index) => (
                        <div key={index} className="bg-muted p-2 rounded-md">
                          <div className="flex items-center">
                            <Badge className="mr-2">{index + 1}</Badge>
                            <span className="text-sm font-medium">{step.title}</span>
                          </div>
                          <p className="text-sm mt-1">{step.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Model Info */}
                  <div>
                    <h4 className="text-sm font-medium mb-2">Model Information</h4>
                    <div className="bg-muted p-2 rounded-md">
                      <div className="grid grid-cols-2 gap-2">
                        <div className="text-sm">Model:</div>
                        <div className="text-sm font-medium">{aiReasoningLayer?.model_info?.name || 'N/A'}</div>
                        
                        <div className="text-sm">Provider:</div>
                        <div className="text-sm font-medium">{aiReasoningLayer?.model_info?.provider || 'N/A'}</div>
                        
                        <div className="text-sm">Version:</div>
                        <div className="text-sm font-medium">{aiReasoningLayer?.model_info?.version || 'N/A'}</div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-6">
                  <EyeOffIcon className="h-12 w-12 text-muted-foreground mb-2" />
                  <p className="text-muted-foreground">AI Reasoning layer is currently hidden</p>
                  <Button 
                    variant="outline" 
                    className="mt-4"
                    onClick={() => handleVisibilityToggle('ai_reasoning', true)}
                  >
                    Show Layer
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Performance Insights Layer</CardTitle>
                <Switch
                  checked={performanceLayer?.visible}
                  onCheckedChange={(checked) => handleVisibilityToggle('performance', checked)}
                />
              </div>
              <CardDescription>
                Visualize performance metrics and insights
              </CardDescription>
            </CardHeader>
            <CardContent>
              {performanceLayer?.visible ? (
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium mb-1 block">Layer Opacity</label>
                    <Slider
                      value={[performanceLayer?.opacity * 100]}
                      min={0}
                      max={100}
                      step={1}
                      onValueChange={(value) => handleOpacityChange('performance', value[0] / 100)}
                    />
                  </div>

                  {/* Performance Metrics */}
                  <div>
                    <h4 className="text-sm font-medium mb-2">Key Metrics</h4>
                    <div className="grid grid-cols-2 gap-4">
                      {performanceMetrics && Object.entries(performanceMetrics.metrics || {}).map(([key, value]: [string, any]) => (
                        <div key={key} className="bg-muted p-3 rounded-md">
                          <div className="text-xs uppercase text-muted-foreground">{key.replace(/_/g, ' ')}</div>
                          <div className="text-2xl font-bold mt-1">
                            {typeof value.value === 'number' && value.unit === 'percentage' 
                              ? `${(value.value * 100).toFixed(1)}%` 
                              : value.value}
                          </div>
                          {value.trend && (
                            <div className={`text-xs mt-1 ${value.trend === 'up' ? 'text-green-500' : value.trend === 'down' ? 'text-red-500' : ''}`}>
                              {value.trend === 'up' ? '↑' : value.trend === 'down' ? '↓' : '→'} 
                              {value.benchmark && `vs ${value.unit === 'percentage' ? `${(value.benchmark * 100).toFixed(1)}%` : value.benchmark} benchmark`}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Insights */}
                  {performanceMetrics?.insights && (
                    <div>
                      <h4 className="text-sm font-medium mb-2">Insights</h4>
                      <div className="space-y-2">
                        {performanceMetrics.insights.map((insight: any, index: number) => (
                          <div 
                            key={index} 
                            className={`p-3 rounded-md border ${
                              insight.type === 'positive' 
                                ? 'border-green-200 bg-green-50' 
                                : insight.type === 'negative' 
                                  ? 'border-red-200 bg-red-50' 
                                  : 'border-gray-200 bg-gray-50'
                            }`}
                          >
                            <div className="flex items-start">
                              <InfoIcon className={`h-5 w-5 mr-2 flex-shrink-0 ${
                                insight.type === 'positive' 
                                  ? 'text-green-500' 
                                  : insight.type === 'negative' 
                                    ? 'text-red-500' 
                                    : 'text-gray-500'
                              }`} />
                              <div>
                                <p className="text-sm">{insight.message}</p>
                                {insight.related_metrics && insight.related_metrics.length > 0 && (
                                  <div className="flex mt-1 gap-1">
                                    {insight.related_metrics.map((metric: string) => (
                                      <Badge key={metric} variant="outline" className="text-xs">
                                        {metric.replace(/_/g, ' ')}
                                      </Badge>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Benchmarks */}
                  {performanceMetrics?.benchmarks && (
                    <div>
                      <h4 className="text-sm font-medium mb-2">Benchmarks</h4>
                      <div className="bg-muted p-3 rounded-md">
                        <div className="grid grid-cols-4 gap-2 text-xs font-medium border-b pb-2 mb-2">
                          <div>Metric</div>
                          <div>Industry Avg</div>
                          <div>Your Avg</div>
                          <div>Top Performers</div>
                        </div>
                        {Object.entries(performanceMetrics.benchmarks.industry || {}).map(([key, value]: [string, any]) => (
                          <div key={key} className="grid grid-cols-4 gap-2 text-xs py-1">
                            <div>{key.replace(/_/g, ' ')}</div>
                            <div>{typeof value === 'number' && key.includes('rate') ? `${(value * 100).toFixed(1)}%` : value}</div>
                            <div>
                              {typeof performanceMetrics.benchmarks.your_average[key] === 'number' && key.includes('rate') 
                                ? `${(performanceMetrics.benchmarks.your_average[key] * 100).toFixed(1)}%` 
                                : performanceMetrics.benchmarks.your_average[key]}
                            </div>
                            <div>
                              {typeof performanceMetrics.benchmarks.top_performers[key] === 'number' && key.includes('rate') 
                                ? `${(performanceMetrics.benchmarks.top_performers[key] * 100).toFixed(1)}%` 
                                : performanceMetrics.benchmarks.top_performers[key]}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-6">
                  <EyeOffIcon className="h-12 w-12 text-muted-foreground mb-2" />
                  <p className="text-muted-foreground">Performance layer is currently hidden</p>
                  <Button 
                    variant="outline" 
                    className="mt-4"
                    onClick={() => handleVisibilityToggle('performance', true)}
                  >
                    Show Layer
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Trust Verification Tab */}
        <TabsContent value="trust-verification">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Trust Verification Layer</CardTitle>
                <Switch
                  checked={trustVerificationLayer?.visible}
                  onCheckedChange={(checked) => handleVisibilityToggle('trust_verification', checked)}
                />
              </div>
              <CardDescription>
                Visualize blockchain verification and certificates
              </CardDescription>
            </CardHeader>
            <CardContent>
              {trustVerificationLayer?.visible ? (
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium mb-1 block">Layer Opacity</label>
                    <Slider
                      value={[trustVerificationLayer?.opacity * 100]}
                      min={0}
                      max={100}
                      step={1}
                      onValueChange={(value) => handleOpacityChange('trust_verification', value[0] / 100)}
                    />
                  </div>

                  {/* Verification Status */}
                  <div>
                    <h4 className="text-sm font-medium mb-2">Verification Status</h4>
                    <div className="bg-muted p-3 rounded-md">
                      <div className="flex items-center">
                        <Badge 
                          className={
                            verificationData?.status?.status === 'verified' 
                              ? 'bg-green-100 text-green-800 hover:bg-green-100' 
                              : verificationData?.status?.status === 'pending' 
                                ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-100' 
                                : 'bg-red-100 text-red-800 hover:bg-red-100'
                          }
                        >
                          {verificationData?.status?.status || 'unverified'}
                        </Badge>
                        <span className="text-sm ml-2">
                          {verificationData?.status?.message || 'Content has not been verified yet.'}
                        </span>
                      </div>
                      {verificationData?.status?.timestamp && (
                        <div className="text-xs text-muted-foreground mt-2">
                          Last updated: {new Date(verificationData.status.timestamp).toLocaleString()}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Certificate */}
                  {verificationData?.certificate && (
                    <div>
                      <h4 className="text-sm font-medium mb-2">Certificate</h4>
                      <div className="bg-muted p-3 rounded-md">
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div className="font-medium">Certificate ID:</div>
                          <div>{verificationData.certificate.id}</div>
                          
                          <div className="font-medium">Issuer:</div>
                          <div>{verificationData.certificate.issuer}</div>
                          
                          <div className="font-medium">Subject:</div>
                          <div>{verificationData.certificate.subject}</div>
                          
                          <div className="font-medium">Issued At:</div>
                          <div>{new Date(verificationData.certificate.issued_at).toLocaleString()}</div>
                          
                          <div className="font-medium">Content Hash:</div>
                          <div className="truncate">{verificationData.certificate.content_hash}</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Blockchain Record */}
                  {verificationData?.blockchain && (
                    <div>
                      <h4 className="text-sm font-medium mb-2">Blockchain Record</h4>
                      <div className="bg-muted p-3 rounded-md">
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div className="font-medium">Transaction ID:</div>
                          <div className="truncate">{verificationData.blockchain.transaction_id}</div>
                          
                          <div className="font-medium">Block Number:</div>
                          <div>{verificationData.blockchain.block_number}</div>
                          
                          <div className="font-medium">Network:</div>
                          <div>{verificationData.blockchain.network}</div>
                          
                          <div className="font-medium">Timestamp:</div>
                          <div>{verificationData.blockchain.timestamp ? new Date(verificationData.blockchain.timestamp).toLocaleString() : 'N/A'}</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* QR Code */}
                  {verificationData?.qr_code && (
                    <div>
                      <h4 className="text-sm font-medium mb-2">Verification QR Code</h4>
                      <div className="flex justify-center bg-white p-4 rounded-md">
                        <img 
                          src={verificationData.qr_code} 
                          alt="Verification QR Code" 
                          className="w-32 h-32"
                        />
                      </div>
                    </div>
                  )}

                  {/* Verification Actions */}
                  <div className="flex justify-end space-x-2 pt-2">
                    <Button variant="outline" size="sm">
                      View Certificate
                    </Button>
                    <Button variant="outline" size="sm">
                      Verify on Blockchain
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-6">
                  <EyeOffIcon className="h-12 w-12 text-muted-foreground mb-2" />
                  <p className="text-muted-foreground">Trust verification layer is currently hidden</p>
                  <Button 
                    variant="outline" 
                    className="mt-4"
                    onClick={() => handleVisibilityToggle('trust_verification', true)}
                  >
                    Show Layer
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default VisualizationLayers;
