import { Router } from 'express';
import { DataAggregationService } from '../predictive/data-aggregation.service';
import { PredictionService } from '../predictive/prediction.service';
import { RecommendationService } from '../predictive/recommendation.service';

const router = Router();

// Initialize services
const dataAggregationService = new DataAggregationService();
const predictionService = new PredictionService();
const recommendationService = new RecommendationService();

/**
 * Data Aggregation Endpoints
 */

// Get all data sources
router.get('/data-sources', async (req, res, next) => {
  try {
    const dataSources = await dataAggregationService.getDataSources();
    res.json(dataSources);
  } catch (error) {
    next(error);
  }
});

// Add a new data source
router.post('/data-sources', async (req, res, next) => {
  try {
    const dataSource = await dataAggregationService.addDataSource(req.body);
    res.status(201).json(dataSource);
  } catch (error) {
    next(error);
  }
});

// Update a data source
router.put('/data-sources/:id', async (req, res, next) => {
  try {
    const dataSource = await dataAggregationService.updateDataSource(req.params.id, req.body);
    res.json(dataSource);
  } catch (error) {
    next(error);
  }
});

// Delete a data source
router.delete('/data-sources/:id', async (req, res, next) => {
  try {
    const success = await dataAggregationService.deleteDataSource(req.params.id);
    res.json({ success });
  } catch (error) {
    next(error);
  }
});

// Get metric data
router.get('/metrics/:metric', async (req, res, next) => {
  try {
    const { startDate, endDate } = req.query;
    const start = startDate ? new Date(startDate as string) : undefined;
    const end = endDate ? new Date(endDate as string) : undefined;
    
    const metricData = await dataAggregationService.getMetricData(req.params.metric, start, end);
    res.json(metricData);
  } catch (error) {
    next(error);
  }
});

// Get multi-metric data
router.get('/metrics', async (req, res, next) => {
  try {
    const { metrics, startDate, endDate } = req.query;
    
    if (!metrics) {
      return res.status(400).json({ error: 'Metrics parameter is required' });
    }
    
    const metricsArray = (metrics as string).split(',');
    const start = startDate ? new Date(startDate as string) : undefined;
    const end = endDate ? new Date(endDate as string) : undefined;
    
    const metricData = await dataAggregationService.getMultiMetricData(metricsArray, start, end);
    res.json(metricData);
  } catch (error) {
    next(error);
  }
});

/**
 * Prediction Endpoints
 */

// Get all prediction models
router.get('/models', async (req, res, next) => {
  try {
    const models = await predictionService.getModels();
    res.json(models);
  } catch (error) {
    next(error);
  }
});

// Get a specific prediction model
router.get('/models/:id', async (req, res, next) => {
  try {
    const model = await predictionService.getModel(req.params.id);
    
    if (!model) {
      return res.status(404).json({ error: 'Model not found' });
    }
    
    res.json(model);
  } catch (error) {
    next(error);
  }
});

// Train a model
router.post('/models/:id/train', async (req, res, next) => {
  try {
    const success = await predictionService.trainModel(req.params.id);
    res.json({ success });
  } catch (error) {
    next(error);
  }
});

// Make a prediction
router.post('/predict/:modelId/:metric/:horizon', async (req, res, next) => {
  try {
    const { modelId, metric, horizon } = req.params;
    const context = req.body;
    
    const predictions = await predictionService.predict(modelId, metric, horizon, context);
    res.json(predictions);
  } catch (error) {
    next(error);
  }
});

/**
 * Recommendation Endpoints
 */

// Get all recommendation rules
router.get('/rules', async (req, res, next) => {
  try {
    const rules = await recommendationService.getRules();
    res.json(rules);
  } catch (error) {
    next(error);
  }
});

// Get a specific recommendation rule
router.get('/rules/:id', async (req, res, next) => {
  try {
    const rule = await recommendationService.getRule(req.params.id);
    
    if (!rule) {
      return res.status(404).json({ error: 'Rule not found' });
    }
    
    res.json(rule);
  } catch (error) {
    next(error);
  }
});

// Add a new recommendation rule
router.post('/rules', async (req, res, next) => {
  try {
    const rule = await recommendationService.addRule(req.body);
    res.status(201).json(rule);
  } catch (error) {
    next(error);
  }
});

// Update a recommendation rule
router.put('/rules/:id', async (req, res, next) => {
  try {
    const rule = await recommendationService.updateRule(req.params.id, req.body);
    res.json(rule);
  } catch (error) {
    next(error);
  }
});

// Delete a recommendation rule
router.delete('/rules/:id', async (req, res, next) => {
  try {
    const success = await recommendationService.deleteRule(req.params.id);
    res.json({ success });
  } catch (error) {
    next(error);
  }
});

// Get recommendations
router.get('/recommendations', async (req, res, next) => {
  try {
    const { tags } = req.query;
    const tagsArray = tags ? (tags as string).split(',') : undefined;
    
    const recommendations = await recommendationService.generateRecommendations(tagsArray);
    res.json(recommendations);
  } catch (error) {
    next(error);
  }
});

// Get recommendations for a specific metric
router.get('/recommendations/metric/:metric', async (req, res, next) => {
  try {
    const recommendations = await recommendationService.getRecommendationsForMetric(req.params.metric);
    res.json(recommendations);
  } catch (error) {
    next(error);
  }
});

// Get recommendations by tags
router.get('/recommendations/tags', async (req, res, next) => {
  try {
    const { tags } = req.query;
    
    if (!tags) {
      return res.status(400).json({ error: 'Tags parameter is required' });
    }
    
    const tagsArray = (tags as string).split(',');
    const recommendations = await recommendationService.getRecommendationsByTags(tagsArray);
    res.json(recommendations);
  } catch (error) {
    next(error);
  }
});

// Get top recommendations
router.get('/recommendations/top', async (req, res, next) => {
  try {
    const { limit } = req.query;
    const limitNum = limit ? parseInt(limit as string, 10) : 5;
    
    const recommendations = await recommendationService.getTopRecommendations(limitNum);
    res.json(recommendations);
  } catch (error) {
    next(error);
  }
});

export default router;
