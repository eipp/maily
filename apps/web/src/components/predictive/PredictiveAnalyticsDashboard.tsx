import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, Grid, Typography, Box, Tabs, Tab, CircularProgress, Alert, Button, Chip, Divider, Paper, useTheme } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { TrendingUp, TrendingDown, Warning, CheckCircle, Info, Timeline, ShowChart, Insights, Recommend } from '@mui/icons-material';
import { format } from 'date-fns';
import axios from 'axios';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`predictive-tabpanel-${index}`}
      aria-labelledby={`predictive-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `predictive-tab-${index}`,
    'aria-controls': `predictive-tabpanel-${index}`,
  };
}

interface MetricData {
  timestamp: string;
  value: number;
  source: string;
}

interface PredictionResult {
  modelId: string;
  modelName: string;
  modelType: string;
  modelVersion: string;
  timestamp: string;
  metric: string;
  value: number;
  confidence: number;
  horizon: string;
  metadata: Record<string, any>;
}

interface Recommendation {
  id: string;
  ruleId: string;
  ruleName: string;
  type: string;
  metric: string;
  timestamp: string;
  value: number;
  threshold?: number;
  confidence: number;
  message: string;
  suggestion: string;
  priority: number;
  tags: string[];
  metadata: Record<string, any>;
}

interface PredictiveModel {
  id: string;
  name: string;
  type: string;
  version: string;
  metrics: string[];
  lastTrained: string | null;
  accuracy: number | null;
}

const PredictiveAnalyticsDashboard: React.FC = () => {
  const theme = useTheme();
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<string[]>([]);
  const [selectedMetric, setSelectedMetric] = useState<string>('');
  const [metricData, setMetricData] = useState<MetricData[]>([]);
  const [predictions, setPredictions] = useState<PredictionResult[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [models, setModels] = useState<PredictiveModel[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [selectedHorizon, setSelectedHorizon] = useState<string>('7d');

  // Fetch available metrics
  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        // In a real implementation, this would be an API call to get available metrics
        // For now, we'll use some sample metrics
        const sampleMetrics = ['open_rate', 'click_rate', 'conversion_rate', 'revenue', 'unsubscribe_rate'];
        setMetrics(sampleMetrics);
        setSelectedMetric(sampleMetrics[0]);
      } catch (err) {
        setError('Failed to fetch metrics');
        console.error(err);
      }
    };

    fetchMetrics();
  }, []);

  // Fetch models
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await axios.get('/api/analytics/predictive/models');
        setModels(response.data);
        if (response.data.length > 0) {
          setSelectedModel(response.data[0].id);
        }
      } catch (err) {
        setError('Failed to fetch prediction models');
        console.error(err);
      }
    };

    fetchModels();
  }, []);

  // Fetch data when metric or date range changes
  useEffect(() => {
    const fetchData = async () => {
      if (!selectedMetric) return;

      setLoading(true);
      setError(null);

      try {
        // Fetch historical data
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 30); // Last 30 days

        const metricResponse = await axios.get(`/api/analytics/predictive/metrics/${selectedMetric}`, {
          params: {
            startDate: startDate.toISOString(),
            endDate: endDate.toISOString(),
          },
        });

        // Format data for charts
        const formattedData = metricResponse.data.map((item: any) => ({
          timestamp: item.timestamp,
          value: item.value,
          source: item.source,
          date: format(new Date(item.timestamp), 'MMM dd'),
        }));

        setMetricData(formattedData);

        // Fetch predictions if a model is selected
        if (selectedModel) {
          const predictionResponse = await axios.get(
            `/api/analytics/predictive/predict/${selectedModel}/${selectedMetric}/${selectedHorizon}`
          );

          // Format prediction data
          const formattedPredictions = predictionResponse.data.map((item: any) => ({
            ...item,
            date: format(new Date(item.timestamp), 'MMM dd'),
          }));

          setPredictions(formattedPredictions);
        }

        // Fetch recommendations
        const recommendationsResponse = await axios.get(
          `/api/analytics/predictive/recommendations/metric/${selectedMetric}`
        );

        setRecommendations(recommendationsResponse.data);

        setLoading(false);
      } catch (err) {
        setError('Failed to fetch data');
        console.error(err);
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedMetric, selectedModel, selectedHorizon]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleMetricChange = (metric: string) => {
    setSelectedMetric(metric);
  };

  const handleModelChange = (modelId: string) => {
    setSelectedModel(modelId);
  };

  const handleHorizonChange = (horizon: string) => {
    setSelectedHorizon(horizon);
  };

  // Combine historical data with predictions for the chart
  const combinedChartData = [...metricData];

  // Add predictions to chart data
  if (predictions.length > 0) {
    // Find the last date in the historical data
    const lastHistoricalDate = new Date(metricData[metricData.length - 1]?.timestamp || new Date());

    // Add predictions with dates after the last historical date
    predictions.forEach(prediction => {
      const predictionDate = new Date(prediction.timestamp);
      if (predictionDate > lastHistoricalDate) {
        combinedChartData.push({
          timestamp: prediction.timestamp,
          value: prediction.value,
          source: 'prediction',
          date: format(predictionDate, 'MMM dd'),
        });
      }
    });
  }

  // Sort combined data by date
  combinedChartData.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Predictive Analytics
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="predictive analytics tabs">
          <Tab label="Dashboard" icon={<ShowChart />} iconPosition="start" {...a11yProps(0)} />
          <Tab label="Predictions" icon={<Timeline />} iconPosition="start" {...a11yProps(1)} />
          <Tab label="Recommendations" icon={<Recommend />} iconPosition="start" {...a11yProps(2)} />
          <Tab label="Insights" icon={<Insights />} iconPosition="start" {...a11yProps(3)} />
        </Tabs>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle1" gutterBottom>
          Select Metric:
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {metrics.map(metric => (
            <Chip
              key={metric}
              label={metric.replace('_', ' ')}
              onClick={() => handleMetricChange(metric)}
              color={selectedMetric === metric ? 'primary' : 'default'}
              variant={selectedMetric === metric ? 'filled' : 'outlined'}
            />
          ))}
        </Box>
      </Box>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          <TabPanel value={tabValue} index={0}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Card>
                  <CardHeader title={`${selectedMetric.replace('_', ' ')} Trend with Predictions`} />
                  <CardContent>
                    <Box sx={{ height: 400 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart
                          data={combinedChartData}
                          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="date" />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Line
                            type="monotone"
                            dataKey="value"
                            stroke={theme.palette.primary.main}
                            strokeWidth={2}
                            dot={{ r: 3 }}
                            activeDot={{ r: 8 }}
                            name="Historical"
                            connectNulls
                          />
                          <Line
                            type="monotone"
                            dataKey="value"
                            stroke={theme.palette.secondary.main}
                            strokeWidth={2}
                            strokeDasharray="5 5"
                            dot={{ r: 3 }}
                            activeDot={{ r: 8 }}
                            name="Prediction"
                            connectNulls
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardHeader title="Top Recommendations" />
                  <CardContent>
                    {recommendations.length > 0 ? (
                      recommendations.slice(0, 3).map((rec) => (
                        <Paper
                          key={rec.id}
                          elevation={1}
                          sx={{ p: 2, mb: 2, borderLeft: `4px solid ${theme.palette.warning.main}` }}
                        >
                          <Typography variant="subtitle1" fontWeight="bold">
                            {rec.ruleName}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            {rec.message}
                          </Typography>
                          <Typography variant="body2">
                            <strong>Suggestion:</strong> {rec.suggestion}
                          </Typography>
                          <Box sx={{ mt: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Chip
                              size="small"
                              label={`Confidence: ${Math.round(rec.confidence * 100)}%`}
                              color={rec.confidence > 0.7 ? 'success' : rec.confidence > 0.4 ? 'warning' : 'error'}
                            />
                            <Typography variant="caption" color="text.secondary">
                              {format(new Date(rec.timestamp), 'MMM dd, yyyy')}
                            </Typography>
                          </Box>
                        </Paper>
                      ))
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        No recommendations available for this metric.
                      </Typography>
                    )}
                    {recommendations.length > 3 && (
                      <Button
                        variant="text"
                        onClick={() => setTabValue(2)}
                        sx={{ mt: 1 }}
                      >
                        View all recommendations
                      </Button>
                    )}
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardHeader title="Prediction Models" />
                  <CardContent>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle1" gutterBottom>
                        Select Model:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {models.map(model => (
                          <Chip
                            key={model.id}
                            label={model.name}
                            onClick={() => handleModelChange(model.id)}
                            color={selectedModel === model.id ? 'primary' : 'default'}
                            variant={selectedModel === model.id ? 'filled' : 'outlined'}
                          />
                        ))}
                      </Box>
                    </Box>

                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle1" gutterBottom>
                        Prediction Horizon:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {['1d', '7d', '30d', '90d'].map(horizon => (
                          <Chip
                            key={horizon}
                            label={horizon}
                            onClick={() => handleHorizonChange(horizon)}
                            color={selectedHorizon === horizon ? 'primary' : 'default'}
                            variant={selectedHorizon === horizon ? 'filled' : 'outlined'}
                          />
                        ))}
                      </Box>
                    </Box>

                    {selectedModel && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle1">
                          Selected Model: {models.find(m => m.id === selectedModel)?.name}
                        </Typography>
                        <Typography variant="body2">
                          Type: {models.find(m => m.id === selectedModel)?.type}
                        </Typography>
                        <Typography variant="body2">
                          Version: {models.find(m => m.id === selectedModel)?.version}
                        </Typography>
                        <Typography variant="body2">
                          Accuracy: {models.find(m => m.id === selectedModel)?.accuracy 
                            ? `${Math.round((models.find(m => m.id === selectedModel)?.accuracy || 0) * 100)}%` 
                            : 'Not trained'}
                        </Typography>
                        <Typography variant="body2">
                          Last Trained: {models.find(m => m.id === selectedModel)?.lastTrained 
                            ? format(new Date(models.find(m => m.id === selectedModel)?.lastTrained || ''), 'MMM dd, yyyy') 
                            : 'Never'}
                        </Typography>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Card>
                  <CardHeader title={`${selectedMetric.replace('_', ' ')} Predictions`} />
                  <CardContent>
                    <Box sx={{ height: 400 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart
                          data={combinedChartData}
                          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="date" />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Line
                            type="monotone"
                            dataKey="value"
                            stroke={theme.palette.primary.main}
                            strokeWidth={2}
                            dot={{ r: 3 }}
                            activeDot={{ r: 8 }}
                            name="Historical"
                            connectNulls
                          />
                          <Line
                            type="monotone"
                            dataKey="value"
                            stroke={theme.palette.secondary.main}
                            strokeWidth={2}
                            strokeDasharray="5 5"
                            dot={{ r: 3 }}
                            activeDot={{ r: 8 }}
                            name="Prediction"
                            connectNulls
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12}>
                <Card>
                  <CardHeader title="Prediction Details" />
                  <CardContent>
                    <Box sx={{ overflowX: 'auto' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead>
                          <tr>
                            <th style={{ textAlign: 'left', padding: '8px', borderBottom: '1px solid #ddd' }}>Date</th>
                            <th style={{ textAlign: 'left', padding: '8px', borderBottom: '1px solid #ddd' }}>Value</th>
                            <th style={{ textAlign: 'left', padding: '8px', borderBottom: '1px solid #ddd' }}>Confidence</th>
                            <th style={{ textAlign: 'left', padding: '8px', borderBottom: '1px solid #ddd' }}>Horizon</th>
                          </tr>
                        </thead>
                        <tbody>
                          {predictions.map((prediction) => (
                            <tr key={prediction.timestamp}>
                              <td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>
                                {format(new Date(prediction.timestamp), 'MMM dd, yyyy')}
                              </td>
                              <td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>
                                {prediction.value.toFixed(4)}
                              </td>
                              <td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>
                                <Chip
                                  size="small"
                                  label={`${Math.round(prediction.confidence * 100)}%`}
                                  color={prediction.confidence > 0.7 ? 'success' : prediction.confidence > 0.4 ? 'warning' : 'error'}
                                />
                              </td>
                              <td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>
                                {prediction.horizon}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Card>
                  <CardHeader title="Recommendations" />
                  <CardContent>
                    {recommendations.length > 0 ? (
                      recommendations.map((rec) => (
                        <Paper
                          key={rec.id}
                          elevation={1}
                          sx={{ p: 2, mb: 2, borderLeft: `4px solid ${
                            rec.priority > 8 ? theme.palette.error.main :
                            rec.priority > 5 ? theme.palette.warning.main :
                            theme.palette.info.main
                          }` }}
                        >
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                            <Typography variant="subtitle1" fontWeight="bold">
                              {rec.ruleName}
                            </Typography>
                            <Chip
                              size="small"
                              label={`Priority: ${rec.priority}`}
                              color={
                                rec.priority > 8 ? 'error' :
                                rec.priority > 5 ? 'warning' :
                                'info'
                              }
                            />
                          </Box>
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            {rec.message}
                          </Typography>
                          <Typography variant="body2" paragraph>
                            <strong>Suggestion:</strong> {rec.suggestion}
                          </Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 1 }}>
                            {rec.tags.map(tag => (
                              <Chip key={tag} label={tag} size="small" variant="outlined" />
                            ))}
                          </Box>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Chip
                              size="small"
                              label={`Confidence: ${Math.round(rec.confidence * 100)}%`}
                              color={rec.confidence > 0.7 ? 'success' : rec.confidence > 0.4 ? 'warning' : 'error'}
                            />
                            <Typography variant="caption" color="text.secondary">
                              {format(new Date(rec.timestamp), 'MMM dd, yyyy')}
                            </Typography>
                          </Box>
                        </Paper>
                      ))
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        No recommendations available for this metric.
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={tabValue} index={3}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardHeader title="Performance Insights" />
                  <CardContent>
                    <Box sx={{ height: 300 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={[
                            { name: 'Open Rate', value: 0.25, benchmark: 0.22 },
                            { name: 'Click Rate', value: 0.12, benchmark: 0.08 },
                            { name: 'Conversion', value: 0.05, benchmark: 0.03 },
                            { name: 'Revenue', value: 1250, benchmark: 1000 },
                          ]}
                          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Bar dataKey="value" name="Your Performance" fill={theme.palette.primary.main} />
                          <Bar dataKey="benchmark" name="Industry Benchmark" fill={theme.palette.grey[400]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </Box>
                    <Typography variant="body2" sx={{ mt: 2 }}>
                      Your campaign performance is above industry benchmarks across all key metrics.
                      The most significant improvement is in click rate, which is 50% higher than the benchmark.
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardHeader title="Trend Analysis" />
                  <CardContent>
                    <Box sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <TrendingUp color="success" sx={{ mr: 1 }} />
                        <Typography variant="body1">
                          <strong>Open Rate:</strong> Increasing trend (+5% MoM)
                        </Typography>
                      </Box>
                      <Typography variant="body2" color="text.secondary" sx={{ ml: 4 }}>
                        Your subject line optimizations are showing positive results.
                      </Typography>
                    </Box>

                    <Box sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <TrendingUp color="success" sx={{ mr: 1 }} />
                        <Typography variant="body1">
                          <strong>Click Rate:</strong> Increasing trend (+8% MoM)
                        </Typography>
                      </Box>
                      <Typography variant="body2" color="text.secondary" sx={{ ml: 4 }}>
                        Content personalization is driving higher engagement.
                      </Typography>
                    </Box>

                    <Box sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <TrendingDown color="error" sx={{ mr: 1 }} />
                        <Typography variant="body1">
                          <strong>Unsubscribe Rate:</strong> Decreasing trend (-3% MoM)
                        </Typography>
                      </Box>
                      <Typography variant="body2" color="text.secondary" sx={{ ml: 4 }}>
                        Improved targeting and content relevance are reducing opt-outs.
                      </Typography>
                    </Box>

                    <Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <TrendingUp color="success" sx={{ mr: 1 }} />
                        <Typography variant="body1">
                          <strong>Revenue:</strong> Increasing trend (+12% MoM)
                        </Typography>
                      </Box>
                      <Typography variant="body2" color="text.secondary" sx={{ ml: 4 }}>
                        Higher conversion rates are driving revenue growth.
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12}>
                <Card>
                  <CardHeader title="AI-Generated Insights" />
                  <CardContent>
                    <Paper elevation={0} sx={{ p: 2, mb: 2, bgcolor: theme.palette.background.default }}>
                      <Typography variant="body1" paragraph>
                        <strong>Campaign Optimization:</strong> Based on predictive analysis, sending campaigns on Tuesday and Thursday mornings (9-11 AM) could increase open rates by an estimated 15%. The data shows a strong correlation between time of delivery and engagement metrics.
                      </Typography>
                      <Typography variant="body1" paragraph>
                        <strong>Content Strategy:</strong> Emails with personalized product recommendations are showing 2.3x higher conversion rates compared to generic newsletters. Consider increasing the frequency of personalized content in your campaign mix.
                      </Typography>
                      <Typography variant="body1" paragraph>
                        <strong>Segment Performance:</strong> The "Active Shoppers" segment is predicted to generate 40% more revenue in the next 30 days compared to other segments. Consider allocating more resources to this high-value segment.
                      </Typography>
                      <Typography variant="body1">
                        <strong>Subject Line Analysis:</strong> Subject lines containing numbers and questions have 22% higher open rates. The AI model predicts that incorporating these elements could improve overall campaign performance.
                      </Typography>
                    </Paper>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>
        </>
      )}
    </Box>
  );
};

export default PredictiveAnalyticsDashboard;
