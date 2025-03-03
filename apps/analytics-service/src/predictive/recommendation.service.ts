/**
 * Recommendation Service
 * 
 * This service provides AI-generated recommendations based on predictive analytics.
 */

import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { RedisService } from '../utils/redis.service';
import { DataAggregationService } from './data-aggregation.service';
import { PredictionService } from './prediction.service';

interface RecommendationRule {
  id: string;
  name: string;
  description: string;
  type: 'threshold' | 'trend' | 'anomaly' | 'comparison';
  metric: string;
  parameters: Record<string, any>;
  enabled: boolean;
  priority: number;
  tags: string[];
}

interface Recommendation {
  id: string;
  ruleId: string;
  ruleName: string;
  type: string;
  metric: string;
  timestamp: Date;
  value: number;
  threshold?: number;
  confidence: number;
  message: string;
  suggestion: string;
  priority: number;
  tags: string[];
  metadata: Record<string, any>;
}

@Injectable()
export class RecommendationService {
  private readonly logger = new Logger(RecommendationService.name);
  private rules: RecommendationRule[] = [];
  private readonly CACHE_KEY_PREFIX = 'predictive:recommendation:';
  private readonly CACHE_TTL = 3600; // 1 hour

  constructor(
    private readonly configService: ConfigService,
    private readonly redisService: RedisService,
    private readonly dataAggregationService: DataAggregationService,
    private readonly predictionService: PredictionService,
  ) {
    this.initializeRules();
  }

  /**
   * Initialize recommendation rules from configuration
   */
  private async initializeRules(): Promise<void> {
    try {
      // Load rules from configuration
      const configRules = this.configService.get<RecommendationRule[]>('analytics.recommendationRules') || [];
      
      // Initialize rules
      this.rules = configRules.map(rule => ({
        ...rule,
        enabled: rule.enabled !== false, // Default to enabled
      }));
      
      this.logger.log(`Initialized ${this.rules.length} recommendation rules`);
    } catch (error) {
      this.logger.error(`Failed to initialize recommendation rules: ${error.message}`, error.stack);
      // Initialize with empty array to prevent errors
      this.rules = [];
    }
  }

  /**
   * Get all recommendation rules
   */
  async getRules(): Promise<RecommendationRule[]> {
    return this.rules;
  }

  /**
   * Get a specific recommendation rule
   */
  async getRule(ruleId: string): Promise<RecommendationRule | null> {
    return this.rules.find(rule => rule.id === ruleId) || null;
  }

  /**
   * Add a new recommendation rule
   */
  async addRule(rule: Omit<RecommendationRule, 'id'>): Promise<RecommendationRule> {
    try {
      // Generate ID
      const id = `rule_${Date.now()}`;
      
      // Create rule
      const newRule: RecommendationRule = {
        id,
        ...rule,
        enabled: rule.enabled !== false, // Default to enabled
      };
      
      // Add to rules
      this.rules.push(newRule);
      
      // Save rules to configuration (in a real implementation)
      // await this.saveRulesToConfig();
      
      this.logger.log(`Added new recommendation rule: ${newRule.name} (${newRule.id})`);
      
      return newRule;
    } catch (error) {
      this.logger.error(`Failed to add recommendation rule: ${error.message}`, error.stack);
      throw error;
    }
  }

  /**
   * Update a recommendation rule
   */
  async updateRule(ruleId: string, updates: Partial<RecommendationRule>): Promise<RecommendationRule> {
    try {
      // Find rule
      const ruleIndex = this.rules.findIndex(rule => rule.id === ruleId);
      
      if (ruleIndex === -1) {
        throw new Error(`Rule not found: ${ruleId}`);
      }
      
      // Update rule
      const updatedRule = {
        ...this.rules[ruleIndex],
        ...updates,
      };
      
      // Update in rules array
      this.rules[ruleIndex] = updatedRule;
      
      // Save rules to configuration (in a real implementation)
      // await this.saveRulesToConfig();
      
      this.logger.log(`Updated recommendation rule: ${updatedRule.name} (${updatedRule.id})`);
      
      return updatedRule;
    } catch (error) {
      this.logger.error(`Failed to update recommendation rule: ${error.message}`, error.stack);
      throw error;
    }
  }

  /**
   * Delete a recommendation rule
   */
  async deleteRule(ruleId: string): Promise<boolean> {
    try {
      // Find rule
      const ruleIndex = this.rules.findIndex(rule => rule.id === ruleId);
      
      if (ruleIndex === -1) {
        throw new Error(`Rule not found: ${ruleId}`);
      }
      
      // Remove from rules array
      this.rules.splice(ruleIndex, 1);
      
      // Save rules to configuration (in a real implementation)
      // await this.saveRulesToConfig();
      
      this.logger.log(`Deleted recommendation rule: ${ruleId}`);
      
      return true;
    } catch (error) {
      this.logger.error(`Failed to delete recommendation rule: ${error.message}`, error.stack);
      throw error;
    }
  }

  /**
   * Generate recommendations based on rules
   */
  async generateRecommendations(tags?: string[]): Promise<Recommendation[]> {
    try {
      // Check cache
      const cacheKey = `${this.CACHE_KEY_PREFIX}all:${tags ? tags.join(',') : 'all'}`;
      const cachedRecommendations = await this.redisService.get(cacheKey);
      
      if (cachedRecommendations) {
        return JSON.parse(cachedRecommendations);
      }
      
      // Filter rules by tags if provided
      let rulesToProcess = this.rules.filter(rule => rule.enabled);
      
      if (tags && tags.length > 0) {
        rulesToProcess = rulesToProcess.filter(rule => 
          rule.tags.some(tag => tags.includes(tag))
        );
      }
      
      // Process each rule
      const recommendationPromises = rulesToProcess.map(rule => this.processRule(rule));
      
      // Wait for all recommendations to be generated
      const recommendationsArrays = await Promise.all(recommendationPromises);
      
      // Flatten the array of arrays
      const recommendations = recommendationsArrays.flat();
      
      // Sort by priority (higher priority first)
      recommendations.sort((a, b) => b.priority - a.priority);
      
      // Cache recommendations
      await this.redisService.set(cacheKey, JSON.stringify(recommendations), this.CACHE_TTL);
      
      return recommendations;
    } catch (error) {
      this.logger.error(`Failed to generate recommendations: ${error.message}`, error.stack);
      return [];
    }
  }

  /**
   * Process a single rule to generate recommendations
   */
  private async processRule(rule: RecommendationRule): Promise<Recommendation[]> {
    try {
      switch (rule.type) {
        case 'threshold':
          return this.processThresholdRule(rule);
        case 'trend':
          return this.processTrendRule(rule);
        case 'anomaly':
          return this.processAnomalyRule(rule);
        case 'comparison':
          return this.processComparisonRule(rule);
        default:
          this.logger.warn(`Unknown rule type: ${rule.type}`);
          return [];
      }
    } catch (error) {
      this.logger.error(`Failed to process rule ${rule.id}: ${error.message}`, error.stack);
      return [];
    }
  }

  /**
   * Process a threshold rule
   */
  private async processThresholdRule(rule: RecommendationRule): Promise<Recommendation[]> {
    try {
      const { metric, parameters } = rule;
      const { threshold, operator, modelId, horizon, message, suggestion } = parameters;
      
      if (!threshold || !operator || !modelId || !horizon) {
        throw new Error(`Missing required parameters for threshold rule: ${rule.id}`);
      }
      
      // Get prediction
      const predictions = await this.predictionService.predict(modelId, metric, horizon);
      
      if (!predictions || predictions.length === 0) {
        return [];
      }
      
      // Check if prediction crosses threshold
      const recommendations: Recommendation[] = [];
      
      for (const prediction of predictions) {
        let thresholdCrossed = false;
        
        switch (operator) {
          case '>':
            thresholdCrossed = prediction.value > threshold;
            break;
          case '>=':
            thresholdCrossed = prediction.value >= threshold;
            break;
          case '<':
            thresholdCrossed = prediction.value < threshold;
            break;
          case '<=':
            thresholdCrossed = prediction.value <= threshold;
            break;
          case '==':
            thresholdCrossed = prediction.value === threshold;
            break;
          case '!=':
            thresholdCrossed = prediction.value !== threshold;
            break;
        }
        
        if (thresholdCrossed) {
          // Create recommendation
          recommendations.push({
            id: `rec_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            ruleId: rule.id,
            ruleName: rule.name,
            type: rule.type,
            metric,
            timestamp: prediction.timestamp,
            value: prediction.value,
            threshold,
            confidence: prediction.confidence,
            message: this.formatMessage(message, { 
              metric, 
              value: prediction.value, 
              threshold, 
              operator,
              horizon: prediction.horizon
            }),
            suggestion: this.formatMessage(suggestion, { 
              metric, 
              value: prediction.value, 
              threshold, 
              operator,
              horizon: prediction.horizon
            }),
            priority: rule.priority,
            tags: rule.tags,
            metadata: {
              prediction,
              rule: {
                id: rule.id,
                name: rule.name,
                type: rule.type,
                parameters: rule.parameters,
              },
            },
          });
        }
      }
      
      return recommendations;
    } catch (error) {
      this.logger.error(`Failed to process threshold rule ${rule.id}: ${error.message}`, error.stack);
      return [];
    }
  }

  /**
   * Process a trend rule
   */
  private async processTrendRule(rule: RecommendationRule): Promise<Recommendation[]> {
    try {
      const { metric, parameters } = rule;
      const { direction, minChange, period, modelId, message, suggestion } = parameters;
      
      if (!direction || !minChange || !period || !modelId) {
        throw new Error(`Missing required parameters for trend rule: ${rule.id}`);
      }
      
      // Get predictions for different horizons
      const shortHorizon = '1d';
      const longHorizon = `${period}d`;
      
      const shortPredictions = await this.predictionService.predict(modelId, metric, shortHorizon);
      const longPredictions = await this.predictionService.predict(modelId, metric, longHorizon);
      
      if (!shortPredictions || shortPredictions.length === 0 || !longPredictions || longPredictions.length === 0) {
        return [];
      }
      
      // Get current value
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - 7); // Get last week of data
      
      const metricData = await this.dataAggregationService.getMetricData(metric, startDate, endDate);
      
      if (!metricData || metricData.length === 0) {
        return [];
      }
      
      // Get most recent value
      metricData.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
      const currentValue = metricData[0].value;
      
      // Get future value
      const futureValue = longPredictions[longPredictions.length - 1].value;
      
      // Calculate change
      const absoluteChange = futureValue - currentValue;
      const percentChange = (absoluteChange / currentValue) * 100;
      
      // Check if trend matches direction and minimum change
      let trendMatches = false;
      
      if (direction === 'up' && percentChange >= minChange) {
        trendMatches = true;
      } else if (direction === 'down' && percentChange <= -minChange) {
        trendMatches = true;
      }
      
      if (!trendMatches) {
        return [];
      }
      
      // Create recommendation
      return [{
        id: `rec_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        ruleId: rule.id,
        ruleName: rule.name,
        type: rule.type,
        metric,
        timestamp: new Date(),
        value: futureValue,
        confidence: longPredictions[longPredictions.length - 1].confidence,
        message: this.formatMessage(message, { 
          metric, 
          currentValue, 
          futureValue, 
          absoluteChange, 
          percentChange,
          period,
          direction
        }),
        suggestion: this.formatMessage(suggestion, { 
          metric, 
          currentValue, 
          futureValue, 
          absoluteChange, 
          percentChange,
          period,
          direction
        }),
        priority: rule.priority,
        tags: rule.tags,
        metadata: {
          currentValue,
          futureValue,
          absoluteChange,
          percentChange,
          period,
          direction,
          shortPredictions,
          longPredictions,
          rule: {
            id: rule.id,
            name: rule.name,
            type: rule.type,
            parameters: rule.parameters,
          },
        },
      }];
    } catch (error) {
      this.logger.error(`Failed to process trend rule ${rule.id}: ${error.message}`, error.stack);
      return [];
    }
  }

  /**
   * Process an anomaly rule
   */
  private async processAnomalyRule(rule: RecommendationRule): Promise<Recommendation[]> {
    try {
      const { metric, parameters } = rule;
      const { deviationThreshold, period, modelId, message, suggestion } = parameters;
      
      if (!deviationThreshold || !period || !modelId) {
        throw new Error(`Missing required parameters for anomaly rule: ${rule.id}`);
      }
      
      // Get historical data
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - period); // Get data for the specified period
      
      const metricData = await this.dataAggregationService.getMetricData(metric, startDate, endDate);
      
      if (!metricData || metricData.length < 2) {
        return [];
      }
      
      // Calculate mean and standard deviation
      const values = metricData.map(item => item.value);
      const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
      const squaredDiffs = values.map(value => Math.pow(value - mean, 2));
      const variance = squaredDiffs.reduce((sum, value) => sum + value, 0) / values.length;
      const stdDev = Math.sqrt(variance);
      
      // Get most recent value
      metricData.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
      const currentValue = metricData[0].value;
      
      // Calculate z-score (number of standard deviations from the mean)
      const zScore = Math.abs((currentValue - mean) / stdDev);
      
      // Check if z-score exceeds threshold
      if (zScore < deviationThreshold) {
        return [];
      }
      
      // Create recommendation
      return [{
        id: `rec_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        ruleId: rule.id,
        ruleName: rule.name,
        type: rule.type,
        metric,
        timestamp: new Date(),
        value: currentValue,
        confidence: 1 - (deviationThreshold / zScore), // Higher z-score means higher confidence
        message: this.formatMessage(message, { 
          metric, 
          currentValue, 
          mean, 
          stdDev, 
          zScore,
          period
        }),
        suggestion: this.formatMessage(suggestion, { 
          metric, 
          currentValue, 
          mean, 
          stdDev, 
          zScore,
          period
        }),
        priority: rule.priority,
        tags: rule.tags,
        metadata: {
          currentValue,
          mean,
          stdDev,
          zScore,
          deviationThreshold,
          period,
          rule: {
            id: rule.id,
            name: rule.name,
            type: rule.type,
            parameters: rule.parameters,
          },
        },
      }];
    } catch (error) {
      this.logger.error(`Failed to process anomaly rule ${rule.id}: ${error.message}`, error.stack);
      return [];
    }
  }

  /**
   * Process a comparison rule
   */
  private async processComparisonRule(rule: RecommendationRule): Promise<Recommendation[]> {
    try {
      const { metric, parameters } = rule;
      const { compareMetric, operator, threshold, modelId, horizon, message, suggestion } = parameters;
      
      if (!compareMetric || !operator || !modelId || !horizon) {
        throw new Error(`Missing required parameters for comparison rule: ${rule.id}`);
      }
      
      // Get predictions for both metrics
      const predictions = await this.predictionService.predict(modelId, metric, horizon);
      const comparePredictions = await this.predictionService.predict(modelId, compareMetric, horizon);
      
      if (!predictions || predictions.length === 0 || !comparePredictions || comparePredictions.length === 0) {
        return [];
      }
      
      // Match predictions by timestamp
      const matchedPredictions = [];
      
      for (const prediction of predictions) {
        const matchingComparePrediction = comparePredictions.find(p => 
          p.timestamp.getTime() === prediction.timestamp.getTime()
        );
        
        if (matchingComparePrediction) {
          matchedPredictions.push({
            prediction,
            comparePrediction: matchingComparePrediction,
          });
        }
      }
      
      if (matchedPredictions.length === 0) {
        return [];
      }
      
      // Check if comparison meets criteria
      const recommendations: Recommendation[] = [];
      
      for (const { prediction, comparePrediction } of matchedPredictions) {
        let comparisonMet = false;
        let ratio = prediction.value / comparePrediction.value;
        let difference = prediction.value - comparePrediction.value;
        
        switch (operator) {
          case 'ratio>':
            comparisonMet = ratio > threshold;
            break;
          case 'ratio<':
            comparisonMet = ratio < threshold;
            break;
          case 'diff>':
            comparisonMet = difference > threshold;
            break;
          case 'diff<':
            comparisonMet = difference < threshold;
            break;
        }
        
        if (comparisonMet) {
          // Create recommendation
          recommendations.push({
            id: `rec_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            ruleId: rule.id,
            ruleName: rule.name,
            type: rule.type,
            metric,
            timestamp: prediction.timestamp,
            value: prediction.value,
            confidence: Math.min(prediction.confidence, comparePrediction.confidence),
            message: this.formatMessage(message, { 
              metric, 
              compareMetric, 
              value: prediction.value, 
              compareValue: comparePrediction.value,
              ratio,
              difference,
              threshold,
              operator,
              horizon: prediction.horizon
            }),
            suggestion: this.formatMessage(suggestion, { 
              metric, 
              compareMetric, 
              value: prediction.value, 
              compareValue: comparePrediction.value,
              ratio,
              difference,
              threshold,
              operator,
              horizon: prediction.horizon
            }),
            priority: rule.priority,
            tags: rule.tags,
            metadata: {
              prediction,
              comparePrediction,
              ratio,
              difference,
              rule: {
                id: rule.id,
                name: rule.name,
                type: rule.type,
                parameters: rule.parameters,
              },
            },
          });
        }
      }
      
      return recommendations;
    } catch (error) {
      this.logger.error(`Failed to process comparison rule ${rule.id}: ${error.message}`, error.stack);
      return [];
    }
  }

  /**
   * Format a message with variables
   */
  private formatMessage(template: string, variables: Record<string, any>): string {
    let message = template;
    
    // Replace variables in the format {{variable}}
    for (const [key, value] of Object.entries(variables)) {
      const placeholder = new RegExp(`\\{\\{${key}\\}\\}`, 'g');
      
      // Format numbers
      let formattedValue = value;
      if (typeof value === 'number') {
        if (Math.abs(value) < 0.01) {
          formattedValue = value.toExponential(2);
        } else if (Math.abs(value) < 1) {
          formattedValue = value.toFixed(4);
        } else if (Math.abs(value) < 100) {
          formattedValue = value.toFixed(2);
        } else {
          formattedValue = value.toFixed(0);
        }
      }
      
      message = message.replace(placeholder, String(formattedValue));
    }
    
    return message;
  }

  /**
   * Get recommendations for a specific metric
   */
  async getRecommendationsForMetric(metric: string): Promise<Recommendation[]> {
    try {
      // Get all recommendations
      const allRecommendations = await this.generateRecommendations();
      
      // Filter by metric
      return allRecommendations.filter(rec => rec.metric === metric);
    } catch (error) {
      this.logger.error(`Failed to get recommendations for metric ${metric}: ${error.message}`, error.stack);
      return [];
    }
  }

  /**
   * Get recommendations by tags
   */
  async getRecommendationsByTags(tags: string[]): Promise<Recommendation[]> {
    try {
      // Get all recommendations
      const allRecommendations = await this.generateRecommendations();
      
      // Filter by tags
      return allRecommendations.filter(rec => 
        rec.tags.some(tag => tags.includes(tag))
      );
    } catch (error) {
      this.logger.error(`Failed to get recommendations by tags: ${error.message}`, error.stack);
      return [];
    }
  }

  /**
   * Get top recommendations by priority
   */
  async getTopRecommendations(limit: number = 5): Promise<Recommendation[]> {
    try {
      // Get all recommendations
      const allRecommendations = await this.generateRecommendations();
      
      // Sort by priority and limit
      return allRecommendations
        .sort((a, b) => b.priority - a.priority)
        .slice(0, limit);
    } catch (error) {
      this.logger.error(`Failed to get top recommendations: ${error.message}`, error.stack);
      return [];
    }
  }
}
