/**
 * Prediction Service
 * 
 * This service provides machine learning predictions for analytics data.
 */

import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { RedisService } from '../utils/redis.service';
import { DataAggregationService } from './data-aggregation.service';
import * as tf from '@tensorflow/tfjs-node';

interface PredictionModel {
  id: string;
  name: string;
  type: string;
  version: string;
  metrics: string[];
  config: Record<string, any>;
  model: tf.LayersModel | null;
  lastTrained: Date | null;
  accuracy: number | null;
}

interface PredictionResult {
  modelId: string;
  modelName: string;
  modelType: string;
  modelVersion: string;
  timestamp: Date;
  metric: string;
  value: number;
  confidence: number;
  horizon: string;
  metadata: Record<string, any>;
}

@Injectable()
export class PredictionService {
  private readonly logger = new Logger(PredictionService.name);
  private models: PredictionModel[] = [];
  private readonly CACHE_KEY_PREFIX = 'predictive:prediction:';
  private readonly CACHE_TTL = 3600; // 1 hour

  constructor(
    private readonly configService: ConfigService,
    private readonly redisService: RedisService,
    private readonly dataAggregationService: DataAggregationService,
  ) {
    this.initializeModels();
  }

  /**
   * Initialize prediction models from configuration
   */
  private async initializeModels(): Promise<void> {
    try {
      // Load model configurations from config
      const modelConfigs = this.configService.get<any[]>('analytics.predictionModels') || [];
      
      // Initialize models
      this.models = modelConfigs.map(config => ({
        id: config.id,
        name: config.name,
        type: config.type,
        version: config.version,
        metrics: config.metrics,
        config: config.config,
        model: null,
        lastTrained: null,
        accuracy: null,
      }));
      
      this.logger.log(`Initialized ${this.models.length} prediction models`);
      
      // Load pre-trained models
      await this.loadPreTrainedModels();
    } catch (error) {
      this.logger.error(`Failed to initialize prediction models: ${error.message}`, error.stack);
      // Initialize with empty array to prevent errors
      this.models = [];
    }
  }

  /**
   * Load pre-trained models from storage
   */
  private async loadPreTrainedModels(): Promise<void> {
    try {
      for (const model of this.models) {
        try {
          // Check if model files exist
          const modelPath = `file://./models/${model.id}`;
          
          try {
            // Load model
            model.model = await tf.loadLayersModel(modelPath);
            this.logger.log(`Loaded pre-trained model: ${model.name} (${model.id})`);
            
            // Load metadata
            const metadataKey = `${this.CACHE_KEY_PREFIX}metadata:${model.id}`;
            const metadata = await this.redisService.get(metadataKey);
            
            if (metadata) {
              const parsedMetadata = JSON.parse(metadata);
              model.lastTrained = new Date(parsedMetadata.lastTrained);
              model.accuracy = parsedMetadata.accuracy;
            }
          } catch (loadError) {
            this.logger.warn(`Could not load pre-trained model ${model.id}: ${loadError.message}`);
            // Will be trained on demand
          }
        } catch (modelError) {
          this.logger.error(`Error loading model ${model.id}: ${modelError.message}`);
        }
      }
    } catch (error) {
      this.logger.error(`Failed to load pre-trained models: ${error.message}`, error.stack);
    }
  }

  /**
   * Get all prediction models
   */
  async getModels(): Promise<Omit<PredictionModel, 'model'>[]> {
    return this.models.map(({ model, ...rest }) => rest);
  }

  /**
   * Get a specific prediction model
   */
  async getModel(modelId: string): Promise<Omit<PredictionModel, 'model'> | null> {
    const model = this.models.find(m => m.id === modelId);
    
    if (!model) {
      return null;
    }
    
    const { model: tfModel, ...rest } = model;
    return rest;
  }

  /**
   * Train a specific model
   */
  async trainModel(modelId: string): Promise<boolean> {
    try {
      const modelIndex = this.models.findIndex(m => m.id === modelId);
      
      if (modelIndex === -1) {
        throw new Error(`Model not found: ${modelId}`);
      }
      
      const model = this.models[modelIndex];
      
      this.logger.log(`Training model: ${model.name} (${model.id})`);
      
      // Get training data
      const trainingData = await this.getTrainingData(model);
      
      if (!trainingData || trainingData.length === 0) {
        throw new Error(`No training data available for model: ${model.id}`);
      }
      
      // Create and train model
      const { trainedModel, accuracy } = await this.createAndTrainModel(model, trainingData);
      
      // Update model
      this.models[modelIndex].model = trainedModel;
      this.models[modelIndex].lastTrained = new Date();
      this.models[modelIndex].accuracy = accuracy;
      
      // Save model
      await this.saveModel(model.id, trainedModel, accuracy);
      
      this.logger.log(`Model trained successfully: ${model.name} (${model.id}), accuracy: ${accuracy}`);
      
      return true;
    } catch (error) {
      this.logger.error(`Failed to train model: ${error.message}`, error.stack);
      return false;
    }
  }

  /**
   * Get training data for a model
   */
  private async getTrainingData(model: PredictionModel): Promise<any[]> {
    try {
      // Get data for each metric
      const metricsData: Record<string, any[]> = {};
      
      for (const metric of model.metrics) {
        // Get historical data for the metric
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - model.config.trainingDays || 365); // Default to 1 year
        
        const metricData = await this.dataAggregationService.getMetricData(metric, startDate, endDate);
        
        if (metricData.length > 0) {
          metricsData[metric] = metricData;
        }
      }
      
      // Process data based on model type
      switch (model.type) {
        case 'timeseries':
          return this.prepareTimeSeriesData(metricsData, model.config);
        case 'regression':
          return this.prepareRegressionData(metricsData, model.config);
        case 'classification':
          return this.prepareClassificationData(metricsData, model.config);
        default:
          throw new Error(`Unsupported model type: ${model.type}`);
      }
    } catch (error) {
      this.logger.error(`Failed to get training data: ${error.message}`, error.stack);
      throw error;
    }
  }

  /**
   * Prepare time series data for training
   */
  private prepareTimeSeriesData(metricsData: Record<string, any[]>, config: Record<string, any>): any[] {
    try {
      const { windowSize = 10, targetMetric } = config;
      
      if (!targetMetric || !metricsData[targetMetric]) {
        throw new Error(`Target metric not found: ${targetMetric}`);
      }
      
      const data = metricsData[targetMetric];
      
      // Sort by timestamp
      data.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
      
      // Create windows
      const windows = [];
      
      for (let i = 0; i <= data.length - windowSize - 1; i++) {
        const window = data.slice(i, i + windowSize);
        const target = data[i + windowSize].value;
        
        windows.push({
          features: window.map(item => item.value),
          target,
        });
      }
      
      return windows;
    } catch (error) {
      this.logger.error(`Failed to prepare time series data: ${error.message}`, error.stack);
      throw error;
    }
  }

  /**
   * Prepare regression data for training
   */
  private prepareRegressionData(metricsData: Record<string, any[]>, config: Record<string, any>): any[] {
    try {
      const { featureMetrics, targetMetric } = config;
      
      if (!targetMetric || !metricsData[targetMetric]) {
        throw new Error(`Target metric not found: ${targetMetric}`);
      }
      
      if (!featureMetrics || featureMetrics.length === 0) {
        throw new Error('No feature metrics specified');
      }
      
      // Check if all feature metrics are available
      for (const metric of featureMetrics) {
        if (!metricsData[metric]) {
          throw new Error(`Feature metric not found: ${metric}`);
        }
      }
      
      // Get target data
      const targetData = metricsData[targetMetric];
      
      // Create feature vectors
      const samples = [];
      
      for (const targetSample of targetData) {
        const features = [];
        
        // Find corresponding feature values
        for (const metric of featureMetrics) {
          const metricData = metricsData[metric];
          
          // Find closest data point by timestamp
          const closestDataPoint = metricData.reduce((closest, current) => {
            const currentDiff = Math.abs(current.timestamp.getTime() - targetSample.timestamp.getTime());
            const closestDiff = Math.abs(closest.timestamp.getTime() - targetSample.timestamp.getTime());
            
            return currentDiff < closestDiff ? current : closest;
          });
          
          features.push(closestDataPoint.value);
        }
        
        samples.push({
          features,
          target: targetSample.value,
        });
      }
      
      return samples;
    } catch (error) {
      this.logger.error(`Failed to prepare regression data: ${error.message}`, error.stack);
      throw error;
    }
  }

  /**
   * Prepare classification data for training
   */
  private prepareClassificationData(metricsData: Record<string, any[]>, config: Record<string, any>): any[] {
    try {
      const { featureMetrics, targetMetric, classes } = config;
      
      if (!targetMetric || !metricsData[targetMetric]) {
        throw new Error(`Target metric not found: ${targetMetric}`);
      }
      
      if (!featureMetrics || featureMetrics.length === 0) {
        throw new Error('No feature metrics specified');
      }
      
      if (!classes || classes.length === 0) {
        throw new Error('No classes specified for classification');
      }
      
      // Check if all feature metrics are available
      for (const metric of featureMetrics) {
        if (!metricsData[metric]) {
          throw new Error(`Feature metric not found: ${metric}`);
        }
      }
      
      // Get target data
      const targetData = metricsData[targetMetric];
      
      // Create feature vectors
      const samples = [];
      
      for (const targetSample of targetData) {
        const features = [];
        
        // Find corresponding feature values
        for (const metric of featureMetrics) {
          const metricData = metricsData[metric];
          
          // Find closest data point by timestamp
          const closestDataPoint = metricData.reduce((closest, current) => {
            const currentDiff = Math.abs(current.timestamp.getTime() - targetSample.timestamp.getTime());
            const closestDiff = Math.abs(closest.timestamp.getTime() - targetSample.timestamp.getTime());
            
            return currentDiff < closestDiff ? current : closest;
          });
          
          features.push(closestDataPoint.value);
        }
        
        // Convert target to class index
        let targetClass = -1;
        
        for (let i = 0; i < classes.length; i++) {
          const { min, max } = classes[i];
          
          if (targetSample.value >= min && targetSample.value <= max) {
            targetClass = i;
            break;
          }
        }
        
        if (targetClass === -1) {
          // Skip samples that don't fit into any class
          continue;
        }
        
        samples.push({
          features,
          target: targetClass,
        });
      }
      
      return samples;
    } catch (error) {
      this.logger.error(`Failed to prepare classification data: ${error.message}`, error.stack);
      throw error;
    }
  }

  /**
   * Create and train a model
   */
  private async createAndTrainModel(modelConfig: PredictionModel, trainingData: any[]): Promise<{ trainedModel: tf.LayersModel, accuracy: number }> {
    try {
      // Split data into training and validation sets
      const splitIndex = Math.floor(trainingData.length * 0.8);
      const trainingSet = trainingData.slice(0, splitIndex);
      const validationSet = trainingData.slice(splitIndex);
      
      // Prepare tensors
      const trainingFeatures = tf.tensor2d(trainingSet.map(sample => sample.features));
      const trainingTargets = tf.tensor2d(trainingSet.map(sample => [sample.target]));
      
      const validationFeatures = tf.tensor2d(validationSet.map(sample => sample.features));
      const validationTargets = tf.tensor2d(validationSet.map(sample => [sample.target]));
      
      // Create model
      const model = this.createModelArchitecture(modelConfig);
      
      // Train model
      await model.fit(trainingFeatures, trainingTargets, {
        epochs: modelConfig.config.epochs || 100,
        batchSize: modelConfig.config.batchSize || 32,
        validationData: [validationFeatures, validationTargets],
        callbacks: {
          onEpochEnd: (epoch, logs) => {
            if (epoch % 10 === 0) {
              this.logger.log(`Training model ${modelConfig.id} - Epoch ${epoch}: loss = ${logs.loss}, val_loss = ${logs.val_loss}`);
            }
          }
        }
      });
      
      // Evaluate model
      const evaluation = model.evaluate(validationFeatures, validationTargets) as tf.Scalar[];
      const loss = evaluation[0].dataSync()[0];
      
      // Calculate accuracy (1 - normalized loss)
      const maxLoss = validationTargets.max().dataSync()[0];
      const normalizedLoss = loss / maxLoss;
      const accuracy = Math.max(0, 1 - normalizedLoss);
      
      // Clean up tensors
      trainingFeatures.dispose();
      trainingTargets.dispose();
      validationFeatures.dispose();
      validationTargets.dispose();
      
      return { trainedModel: model, accuracy };
    } catch (error) {
      this.logger.error(`Failed to create and train model: ${error.message}`, error.stack);
      throw error;
    }
  }

  /**
   * Create model architecture based on configuration
   */
  private createModelArchitecture(modelConfig: PredictionModel): tf.LayersModel {
    try {
      const { type, config } = modelConfig;
      
      // Create sequential model
      const model = tf.sequential();
      
      switch (type) {
        case 'timeseries':
          // LSTM model for time series
          model.add(tf.layers.lstm({
            units: config.units || 50,
            returnSequences: false,
            inputShape: [config.windowSize || 10, 1],
          }));
          model.add(tf.layers.dense({ units: 1 }));
          break;
          
        case 'regression':
          // Dense model for regression
          model.add(tf.layers.dense({
            units: config.hiddenUnits || 64,
            activation: 'relu',
            inputShape: [config.featureMetrics.length],
          }));
          
          if (config.layers && config.layers > 1) {
            for (let i = 1; i < config.layers; i++) {
              model.add(tf.layers.dense({
                units: config.hiddenUnits || 64,
                activation: 'relu',
              }));
            }
          }
          
          model.add(tf.layers.dense({ units: 1 }));
          break;
          
        case 'classification':
          // Dense model for classification
          model.add(tf.layers.dense({
            units: config.hiddenUnits || 64,
            activation: 'relu',
            inputShape: [config.featureMetrics.length],
          }));
          
          if (config.layers && config.layers > 1) {
            for (let i = 1; i < config.layers; i++) {
              model.add(tf.layers.dense({
                units: config.hiddenUnits || 64,
                activation: 'relu',
              }));
            }
          }
          
          model.add(tf.layers.dense({
            units: config.classes.length,
            activation: 'softmax',
          }));
          break;
          
        default:
          throw new Error(`Unsupported model type: ${type}`);
      }
      
      // Compile model
      model.compile({
        optimizer: tf.train.adam(config.learningRate || 0.001),
        loss: type === 'classification' ? 'categoricalCrossentropy' : 'meanSquaredError',
        metrics: ['mse'],
      });
      
      return model;
    } catch (error) {
      this.logger.error(`Failed to create model architecture: ${error.message}`, error.stack);
      throw error;
    }
  }

  /**
   * Save trained model
   */
  private async saveModel(modelId: string, model: tf.LayersModel, accuracy: number): Promise<void> {
    try {
      // Save model to file system
      const modelPath = `file://./models/${modelId}`;
      await model.save(modelPath);
      
      // Save metadata to Redis
      const metadataKey = `${this.CACHE_KEY_PREFIX}metadata:${modelId}`;
      const metadata = {
        lastTrained: new Date().toISOString(),
        accuracy,
      };
      
      await this.redisService.set(metadataKey, JSON.stringify(metadata));
      
      this.logger.log(`Saved model ${modelId} with accuracy ${accuracy}`);
    } catch (error) {
      this.logger.error(`Failed to save model: ${error.message}`, error.stack);
      throw error;
    }
  }

  /**
   * Make predictions using a specific model
   */
  async predict(modelId: string, metric: string, horizon: string, context?: Record<string, any>): Promise<PredictionResult[]> {
    try {
      // Find model
      const model = this.models.find(m => m.id === modelId);
      
      if (!model) {
        throw new Error(`Model not found: ${modelId}`);
      }
      
      if (!model.model) {
        // Train model if not loaded
        await this.trainModel(modelId);
        
        if (!model.model) {
          throw new Error(`Failed to train model: ${modelId}`);
        }
      }
      
      // Check if metric is supported by model
      if (!model.metrics.includes(metric)) {
        throw new Error(`Metric not supported by model: ${metric}`);
      }
      
      // Parse horizon
      const { value: horizonValue, unit: horizonUnit } = this.parseHorizon(horizon);
      
      // Check cache
      const cacheKey = `${this.CACHE_KEY_PREFIX}${modelId}:${metric}:${horizon}:${JSON.stringify(context || {})}`;
      const cachedPrediction = await this.redisService.get(cacheKey);
      
      if (cachedPrediction) {
        return JSON.parse(cachedPrediction);
      }
      
      // Get input data for prediction
      const inputData = await this.getPredictionInputData(model, metric, context);
      
      // Make prediction
      const predictions = await this.makePrediction(model, inputData, horizonValue, horizonUnit);
      
      // Cache prediction
      await this.redisService.set(cacheKey, JSON.stringify(predictions), 3600); // 1 hour cache
      
      return predictions;
    } catch (error) {
      this.logger.error(`Failed to make prediction: ${error.message}`, error.stack);
      throw error;
    }
  }

  /**
   * Parse horizon string (e.g., "7d", "24h", "3m")
   */
  private parseHorizon(horizon: string): { value: number, unit: string } {
    const match = horizon.match(/^(\d+)([dhm])$/);
    
    if (!match) {
      throw new Error(`Invalid horizon format: ${horizon}. Expected format: Xd, Xh, or Xm (e.g., 7d, 24h, 3m)`);
    }
    
    return {
      value: parseInt(match[1], 10),
      unit: match[2],
    };
  }

  /**
   * Get input data for prediction
   */
  private async getPredictionInputData(model: PredictionModel, metric: string, context?: Record<string, any>): Promise<any> {
    try {
      switch (model.type) {
        case 'timeseries':
          return this.getTimeSeriesInputData(model, metric);
        case 'regression':
          return this.getRegressionInputData(model, metric, context);
        case 'classification':
          return this.getClassificationInputData(model, metric, context);
        default:
          throw new Error(`Unsupported model type: ${model.type}`);
      }
    } catch (error) {
      this.logger.error(`Failed to get prediction input data: ${error.message}`, error.stack);
      throw error;
    }
  }

  /**
   * Get input data for time series prediction
   */
  private async getTimeSeriesInputData(model: PredictionModel, metric: string): Promise<number[]> {
    try {
      const { windowSize = 10 } = model.config;
      
      // Get historical data
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - windowSize * 2); // Get more data than needed to ensure we have enough
      
      const metricData = await this.dataAggregationService.getMetricData(metric, startDate, endDate);
      
      if (metricData.length < windowSize) {
        throw new Error(`Not enough historical data for prediction. Need at least ${windowSize} data points, but got ${metricData.length}`);
      }
      
      // Sort by timestamp and get the most recent window
      metricData.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
      
      const recentData = metricData.slice(0, windowSize).reverse();
      
      return recentData.map(item => item.value);
    } catch (error) {
      this.logger.error(`Failed to get time series input data: ${error.message}`, error.stack);
      throw error;
    }
  }

  /**
   * Get input data for regression prediction
   */
  private async getRegressionInputData(model: PredictionModel, metric: string, context?: Record<string, any>): Promise<number[]> {
    try {
      const { featureMetrics } = model.config;
      
      if (!featureMetrics || featureMetrics.length === 0) {
        throw new Error('No feature metrics specified');
      }
      
      // Get latest data for each feature metric
      const features = [];
      
      for (const featureMetric of featureMetrics) {
        // Check if value is provided in context
        if (context && context[featureMetric] !== undefined) {
          features.push(context[featureMetric]);
          continue;
        }
        
        // Get latest value from data
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 7); // Get last week of data
        
        const metricData = await this.dataAggregationService.getMetricData(featureMetric, startDate, endDate);
        
        if (metricData.length === 0) {
          throw new Error(`No data available for feature metric: ${featureMetric}`);
        }
        
        // Get most recent value
        metricData.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
        features.push(metricData[0].value);
      }
      
      return features;
    } catch (error) {
      this.logger.error(`Failed to get regression input data: ${error.message}`, error.stack);
      throw error;
    }
  }

  /**
   * Get input data for classification prediction
   */
  private async getClassificationInputData(model: PredictionModel, metric: string, context?: Record<string, any>): Promise<number[]> {
    // Classification uses the same input format as regression
    return this.getRegressionInputData(model, metric, context);
  }

  /**
   * Make prediction using model
   */
  private async makePrediction(
    model: PredictionModel,
    inputData: any,
    horizonValue: number,
    horizonUnit: string
  ): Promise<PredictionResult[]> {
    try {
      const tfModel = model.model;
      
      if (!tfModel) {
        throw new Error('Model not loaded');
      }
      
      const results: PredictionResult[] = [];
      
      switch (model.type) {
        case 'timeseries': {
          // For time series, we need to make predictions for each step in the horizon
          const input = tf.tensor2d([inputData]);
          
          // Calculate number of steps based on horizon
          let steps = horizonValue;
          if (horizonUnit === 'h') {
            steps = Math.ceil(horizonValue / 24); // Convert hours to days
          } else if (horizonUnit === 'm') {
            steps = Math.ceil(horizonValue / 30); // Convert months to days (approximate)
          }
          
          // Make predictions for each step
          let currentInput = input;
          
          for (let i = 0; i < steps; i++) {
            // Make prediction
            const prediction = tfModel.predict(currentInput) as tf.Tensor;
            const predictionValue = prediction.dataSync()[0];
            
            // Calculate confidence based on model accuracy
            const confidence = model.accuracy || 0.5;
            
            // Calculate timestamp for this prediction
            const timestamp = new Date();
            if (horizonUnit === 'd') {
              timestamp.setDate(timestamp.getDate() + i + 1);
            } else if (horizonUnit === 'h') {
              timestamp.setHours(timestamp.getHours() + horizonValue);
            } else if (horizonUnit === 'm') {
              timestamp.setMonth(timestamp.getMonth() + horizonValue);
            }
            
            // Add to results
            results.push({
              modelId: model.id,
              modelName: model.name,
              modelType: model.type,
              modelVersion: model.version,
              timestamp,
              metric: model.metrics[0], // Time series models typically predict a single metric
              value: predictionValue,
              confidence,
              horizon: `${i + 1}${horizonUnit}`,
              metadata: {
                inputData,
              },
            });
            
            // Update input for next prediction (sliding window)
            const newInput = currentInput.arraySync()[0].slice(1);
            newInput.push(predictionValue);
            
            // Dispose old tensor and create new one
            currentInput.dispose();
            currentInput = tf.tensor2d([newInput]);
            
            // Dispose prediction tensor
            prediction.dispose();
          }
          
          // Dispose final input tensor
          currentInput.dispose();
          break;
        }
        
        case 'regression': {
          // For regression, we make a single prediction
          const input = tf.tensor2d([inputData]);
          
          // Make prediction
          const prediction = tfModel.predict(input) as tf.Tensor;
          const predictionValue = prediction.dataSync()[0];
          
          // Calculate confidence based on model accuracy
          const confidence = model.accuracy || 0.5;
          
          // Calculate timestamp for this prediction
          const timestamp = new Date();
          if (horizonUnit === 'd') {
            timestamp.setDate(timestamp.getDate() + horizonValue);
          } else if (horizonUnit === 'h') {
            timestamp.setHours(timestamp.getHours() + horizonValue);
          } else if (horizonUnit === 'm') {
            timestamp.setMonth(timestamp.getMonth() + horizonValue);
          }
          
          // Add to results
          results.push({
            modelId: model.id,
            modelName: model.name,
            modelType: model.type,
            modelVersion: model.version,
            timestamp,
            metric: model.metrics[0], // Regression models typically predict a single metric
            value: predictionValue,
            confidence,
            horizon: `${horizonValue}${horizonUnit}`,
            metadata: {
              inputData,
            },
          });
          
          // Dispose tensors
          input.dispose();
          prediction.dispose();
          break;
        }
        
        case 'classification': {
          // For classification, we predict class probabilities
          const input = tf.tensor2d([inputData]);
          
          // Make prediction
          const prediction = tfModel.predict(input) as tf.Tensor;
          const probabilities = prediction.dataSync();
          
          // Find class with highest probability
          let maxProbIndex = 0;
          let maxProb = probabilities[0];
          
          for (let i = 1; i < probabilities.length; i++) {
            if (probabilities[i] > maxProb) {
              maxProb = probabilities[i];
              maxProbIndex = i;
            }
          }
          
          // Get class value
          const { classes } = model.config;
          const classConfig = classes[maxProbIndex];
          const classValue = (classConfig.min + classConfig.max) / 2; // Use middle of class range
          
          // Calculate timestamp for this prediction
          const timestamp = new Date();
          if (horizonUnit === 'd') {
            timestamp.setDate(timestamp.getDate() + horizonValue);
          } else if (horizonUnit === 'h') {
            timestamp.setHours(timestamp.getHours() + horizonValue);
          } else if (horizonUnit === 'm') {
            timestamp.setMonth(timestamp.getMonth() + horizonValue);
          }
          
          // Add to results
          results.push({
            modelId: model.id,
            modelName: model.name,
            modelType: model.type,
            modelVersion: model.version,
            timestamp,
            metric: model.metrics[0], // Classification models typically predict a single metric
            value: classValue,
            confidence: maxProb, // Use the probability as confidence
            horizon: `${horizonValue}${horizonUnit}`,
            metadata: {
              inputData,
              classIndex: maxProbIndex,
              className: classConfig.name || `Class ${maxProbIndex}`,
              probabilities: Array.from(probabilities),
            },
          });
          
          // Dispose tensors
          input.dispose();
          prediction.dispose();
          break;
        }
      }
      
      return results;
    } catch (error) {
      this.logger.error(`Failed to make prediction: ${error.message}`, error.stack);
      throw error;
    }
  }
}
