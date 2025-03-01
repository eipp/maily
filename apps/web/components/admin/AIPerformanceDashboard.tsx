import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import {
  AlertCircle,
  Clock,
  DollarSign,
  BarChart2,
  Zap,
  Database,
  RefreshCw
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { formatDistanceToNow } from 'date-fns';

// Types
interface PerformanceMetric {
  timestamp: string;
  value: number;
}

interface LatencyPercentiles {
  p50: number;
  p90: number;
  p95: number;
  p99?: number;
  avg: number;
}

interface ModelPerformance {
  model_name: string;
  requests: number;
  success_rate: number;
  error_rate: number;
  total_tokens: number;
  total_cost: number;
  avg_tokens_per_request: number;
  avg_cost_per_request: number;
  latency: LatencyPercentiles;
}

interface AlertDetails {
  id: string;
  type: string;
  model_name: string;
  operation_type: string;
  timestamp: string;
  details: Record<string, any>;
}

interface CacheMetrics {
  hits: number;
  misses: number;
  hit_ratio: number;
  estimated_savings: number;
  timestamp: string;
}

interface LatencyDistribution {
  [bucket: string]: number;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82ca9d'];

const AIPerformanceDashboard: React.FC = () => {
  // State
  const [activeTab, setActiveTab] = useState('overview');
  const [timeWindow, setTimeWindow] = useState('60');
  const [metricType, setMetricType] = useState('requests');
  const [operationType, setOperationType] = useState('generation');
  const [selectedModel, setSelectedModel] = useState<string | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [performanceSummary, setPerformanceSummary] = useState<Record<string, any>>({});
  const [activeModels, setActiveModels] = useState<string[]>([]);
  const [timeseriesData, setTimeseriesData] = useState<PerformanceMetric[]>([]);
  const [latencyDistribution, setLatencyDistribution] = useState<LatencyDistribution>({});
  const [recentAlerts, setRecentAlerts] = useState<AlertDetails[]>([]);
  const [cacheMetrics, setCacheMetrics] = useState<CacheMetrics | null>(null);

  // Fetch data
  const fetchData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch performance summary
      const summaryRes = await fetch('/api/ai/monitoring/performance/summary');
      if (!summaryRes.ok) throw new Error('Failed to fetch performance summary');
      const summaryData = await summaryRes.json();
      setPerformanceSummary(summaryData.summary || {});

      // Fetch active models
      const modelsRes = await fetch('/api/ai/monitoring/performance/models');
      if (!modelsRes.ok) throw new Error('Failed to fetch active models');
      const modelsData = await modelsRes.json();
      setActiveModels(modelsData);

      if (modelsData.length > 0 && !selectedModel) {
        setSelectedModel(modelsData[0]);
      }

      // Fetch timeseries data
      const timeseriesRes = await fetch(
        `/api/ai/monitoring/performance/timeseries/${metricType}?operation_type=${operationType}&window=${timeWindow}`
      );
      if (!timeseriesRes.ok) throw new Error('Failed to fetch timeseries data');
      const timeseriesData = await timeseriesRes.json();
      setTimeseriesData(timeseriesData);

      // Fetch latency distribution if a model is selected
      if (selectedModel) {
        const latencyRes = await fetch(`/api/ai/monitoring/performance/latency/${selectedModel}`);
        if (!latencyRes.ok) throw new Error('Failed to fetch latency distribution');
        const latencyData = await latencyRes.json();
        setLatencyDistribution(latencyData);
      }

      // Fetch recent alerts
      const alertsRes = await fetch('/api/ai/monitoring/alerts/recent');
      if (!alertsRes.ok) throw new Error('Failed to fetch recent alerts');
      const alertsData = await alertsRes.json();
      setRecentAlerts(alertsData);

      // Fetch cache metrics
      try {
        const cacheRes = await fetch('/api/ai/monitoring/cache/metrics');
        if (cacheRes.ok) {
          const cacheData = await cacheRes.json();
          setCacheMetrics(cacheData);
        }
      } catch (e) {
        // Cache metrics might not be available, so we don't throw an error
        console.warn('Cache metrics not available:', e);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
      console.error('Error fetching AI performance data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Initial data fetch
  useEffect(() => {
    fetchData();

    // Set up polling every 30 seconds
    const intervalId = setInterval(fetchData, 30000);

    return () => clearInterval(intervalId);
  }, []);

  // Fetch data when filters change
  useEffect(() => {
    fetchData();
  }, [timeWindow, metricType, operationType, selectedModel]);

  // Format data for charts
  const formatLatencyDistribution = () => {
    return Object.entries(latencyDistribution).map(([bucket, count]) => ({
      bucket,
      count,
    }));
  };

  const formatCacheData = () => {
    if (!cacheMetrics) return [];

    return [
      { name: 'Hits', value: cacheMetrics.hits },
      { name: 'Misses', value: cacheMetrics.misses },
    ];
  };

  // Helper functions
  const formatCost = (cost: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 4,
      maximumFractionDigits: 4,
    }).format(cost);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const formatLatency = (ms: number) => {
    if (ms < 1000) {
      return `${ms.toFixed(0)}ms`;
    }
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const getAlertTypeIcon = (type: string) => {
    switch (type) {
      case 'high_latency':
        return <Clock className="h-4 w-4 text-amber-500" />;
      case 'high_error_rate':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'high_cost':
        return <DollarSign className="h-4 w-4 text-purple-500" />;
      case 'high_token_usage':
        return <BarChart2 className="h-4 w-4 text-blue-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getMetricLabel = (metric: string) => {
    switch (metric) {
      case 'requests':
        return 'Requests';
      case 'latency':
        return 'Latency (ms)';
      case 'tokens':
        return 'Tokens';
      case 'cost':
        return 'Cost (USD)';
      case 'errors':
        return 'Errors';
      case 'success_rate':
        return 'Success Rate';
      default:
        return metric;
    }
  };

  // Render loading state
  if (isLoading && Object.keys(performanceSummary).length === 0) {
    return (
      <div className="space-y-4 p-4">
        <h2 className="text-2xl font-bold">AI Performance Dashboard</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-4 w-1/2" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-16 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
        <Card>
          <CardHeader>
            <Skeleton className="h-4 w-1/3" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-[300px] w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div className="p-4">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>
            Failed to load AI performance data: {error}
            <div className="mt-2">
              <Button onClick={fetchData} variant="outline" size="sm">
                <RefreshCw className="mr-2 h-4 w-4" />
                Retry
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // Get summary data for the 5-minute window
  const summary5m = performanceSummary['5m'] || {};

  return (
    <div className="space-y-4 p-4">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">AI Performance Dashboard</h2>
        <Button onClick={fetchData} variant="outline" size="sm">
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="models">Models</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
          <TabsTrigger value="cache">Cache</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Total Requests (5m)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatNumber(summary5m.requests || 0)}</div>
                <p className="text-xs text-muted-foreground">
                  Success Rate: {formatPercentage(summary5m.success_rate || 0)}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Avg Latency (5m)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatLatency(summary5m.latency_avg || 0)}</div>
                <p className="text-xs text-muted-foreground">
                  P95: {formatLatency(summary5m.latency_p95 || 0)}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Total Cost (5m)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatCost(summary5m.total_cost || 0)}</div>
                <p className="text-xs text-muted-foreground">
                  {formatNumber(summary5m.total_tokens || 0)} tokens
                </p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Performance Metrics</CardTitle>
              <CardDescription>
                <div className="flex flex-wrap gap-2 mt-2">
                  <Select value={metricType} onValueChange={setMetricType}>
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Select metric" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="requests">Requests</SelectItem>
                      <SelectItem value="latency">Latency</SelectItem>
                      <SelectItem value="tokens">Tokens</SelectItem>
                      <SelectItem value="cost">Cost</SelectItem>
                      <SelectItem value="errors">Errors</SelectItem>
                      <SelectItem value="success_rate">Success Rate</SelectItem>
                    </SelectContent>
                  </Select>

                  <Select value={operationType} onValueChange={setOperationType}>
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Operation type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="generation">Generation</SelectItem>
                      <SelectItem value="embedding">Embedding</SelectItem>
                    </SelectContent>
                  </Select>

                  <Select value={timeWindow} onValueChange={setTimeWindow}>
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Time window" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="15">Last 15 minutes</SelectItem>
                      <SelectItem value="30">Last 30 minutes</SelectItem>
                      <SelectItem value="60">Last hour</SelectItem>
                      <SelectItem value="360">Last 6 hours</SelectItem>
                      <SelectItem value="1440">Last 24 hours</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={timeseriesData}
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(timestamp) => {
                        const date = new Date(timestamp);
                        return `${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
                      }}
                    />
                    <YAxis
                      label={{
                        value: getMetricLabel(metricType),
                        angle: -90,
                        position: 'insideLeft'
                      }}
                    />
                    <Tooltip
                      formatter={(value: number) => {
                        if (metricType === 'cost') return formatCost(value);
                        if (metricType === 'latency') return formatLatency(value);
                        if (metricType === 'success_rate') return formatPercentage(value);
                        return formatNumber(value);
                      }}
                      labelFormatter={(timestamp) => new Date(timestamp).toLocaleString()}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="value"
                      name={getMetricLabel(metricType)}
                      stroke="#8884d8"
                      activeDot={{ r: 8 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {recentAlerts.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Recent Alerts</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {recentAlerts.slice(0, 3).map((alert) => (
                    <Alert key={alert.id} variant="outline">
                      <div className="flex items-start">
                        {getAlertTypeIcon(alert.type)}
                        <div className="ml-2">
                          <AlertTitle className="text-sm font-medium">
                            {alert.type.replace(/_/g, ' ')} - {alert.model_name}
                          </AlertTitle>
                          <AlertDescription className="text-xs mt-1">
                            {alert.operation_type} operation - {formatDistanceToNow(new Date(alert.timestamp))} ago
                          </AlertDescription>
                        </div>
                      </div>
                    </Alert>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Models Tab */}
        <TabsContent value="models" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Model Selection</CardTitle>
              <CardDescription>
                <div className="flex flex-wrap gap-2 mt-2">
                  <Select
                    value={selectedModel || ''}
                    onValueChange={(value) => setSelectedModel(value || null)}
                  >
                    <SelectTrigger className="w-[250px]">
                      <SelectValue placeholder="Select model" />
                    </SelectTrigger>
                    <SelectContent>
                      {activeModels.map((model) => (
                        <SelectItem key={model} value={model}>
                          {model}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </CardDescription>
            </CardHeader>
          </Card>

          {selectedModel && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Latency Distribution</CardTitle>
                  <CardDescription>
                    Response time distribution for {selectedModel}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={formatLatencyDistribution()}
                        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="bucket" />
                        <YAxis label={{ value: 'Count', angle: -90, position: 'insideLeft' }} />
                        <Tooltip formatter={(value) => formatNumber(value as number)} />
                        <Legend />
                        <Bar dataKey="count" name="Request Count" fill="#8884d8" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Model Performance Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Time Window</TableHead>
                        <TableHead>Requests</TableHead>
                        <TableHead>Success Rate</TableHead>
                        <TableHead>Avg Latency</TableHead>
                        <TableHead>P95 Latency</TableHead>
                        <TableHead>Total Tokens</TableHead>
                        <TableHead>Total Cost</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {Object.entries(performanceSummary).map(([window, metrics]: [string, any]) => (
                        <TableRow key={window}>
                          <TableCell>{window}</TableCell>
                          <TableCell>{formatNumber(metrics.requests || 0)}</TableCell>
                          <TableCell>{formatPercentage(metrics.success_rate || 0)}</TableCell>
                          <TableCell>{formatLatency(metrics.latency_avg || 0)}</TableCell>
                          <TableCell>{formatLatency(metrics.latency_p95 || 0)}</TableCell>
                          <TableCell>{formatNumber(metrics.total_tokens || 0)}</TableCell>
                          <TableCell>{formatCost(metrics.total_cost || 0)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* Alerts Tab */}
        <TabsContent value="alerts" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Alerts</CardTitle>
              <CardDescription>
                Alerts triggered in the system based on configured thresholds
              </CardDescription>
            </CardHeader>
            <CardContent>
              {recentAlerts.length === 0 ? (
                <div className="text-center py-6 text-muted-foreground">
                  No alerts have been triggered recently.
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Type</TableHead>
                      <TableHead>Model</TableHead>
                      <TableHead>Operation</TableHead>
                      <TableHead>Time</TableHead>
                      <TableHead>Details</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {recentAlerts.map((alert) => (
                      <TableRow key={alert.id}>
                        <TableCell>
                          <div className="flex items-center">
                            {getAlertTypeIcon(alert.type)}
                            <span className="ml-2 capitalize">
                              {alert.type.replace(/_/g, ' ')}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>{alert.model_name}</TableCell>
                        <TableCell>{alert.operation_type}</TableCell>
                        <TableCell>{formatDistanceToNow(new Date(alert.timestamp))} ago</TableCell>
                        <TableCell>
                          {Object.entries(alert.details).map(([key, value]) => (
                            <div key={key} className="text-xs">
                              <span className="font-medium">{key.replace(/_/g, ' ')}:</span>{' '}
                              {typeof value === 'number'
                                ? key.includes('cost')
                                  ? formatCost(value)
                                  : key.includes('latency')
                                    ? formatLatency(value)
                                    : formatNumber(value)
                                : String(value)}
                            </div>
                          ))}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Cache Tab */}
        <TabsContent value="cache" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Cache Performance</CardTitle>
                <CardDescription>
                  Cache hit ratio and estimated cost savings
                </CardDescription>
              </CardHeader>
              <CardContent>
                {cacheMetrics ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <div className="text-sm font-medium text-muted-foreground">Hit Ratio</div>
                        <div className="text-2xl font-bold">{formatPercentage(cacheMetrics.hit_ratio)}</div>
                      </div>
                      <div>
                        <div className="text-sm font-medium text-muted-foreground">Cost Savings</div>
                        <div className="text-2xl font-bold">{formatCost(cacheMetrics.estimated_savings)}</div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <div className="text-sm font-medium text-muted-foreground">Cache Hits</div>
                        <div className="text-2xl font-bold">{formatNumber(cacheMetrics.hits)}</div>
                      </div>
                      <div>
                        <div className="text-sm font-medium text-muted-foreground">Cache Misses</div>
                        <div className="text-2xl font-bold">{formatNumber(cacheMetrics.misses)}</div>
                      </div>
                    </div>

                    <div className="text-xs text-muted-foreground">
                      Last updated: {formatDistanceToNow(new Date(cacheMetrics.timestamp))} ago
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-6 text-muted-foreground">
                    Cache metrics not available.
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Cache Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                {cacheMetrics ? (
                  <div className="h-[250px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={formatCacheData()}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                        >
                          {formatCacheData().map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value) => formatNumber(value as number)} />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="h-[250px] flex items-center justify-center">
                    <Database className="h-16 w-16 text-muted-foreground opacity-20" />
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AIPerformanceDashboard;
