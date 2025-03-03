/**
 * Predictive Analytics Controller
 * 
 * This controller provides REST API endpoints for predictive analytics capabilities.
 */

import { Controller, Get, Post, Put, Delete, Body, Param, Query } from '@nestjs/common';
import { DataAggregationService } from './data-aggregation.service';
import { PredictionService } from './prediction.service';
import { RecommendationService } from './recommendation.service';

@Controller('api/analytics/predictive')
export class PredictiveController {
  constructor(
    private readonly dataAggregationService: DataAggregationService,
    private readonly predictionService: PredictionService,
    private readonly recommendationService: RecommendationService,
  ) {}

  /**
   * Data Aggregation Endpoints
   */
  
  @Get('data-sources')
  async getDataSources() {
    return this.dataAggregationService.getDataSources();
  }
  
  @Post('data-sources')
  async addDataSource(@Body() dataSource: any) {
    return this.dataAggregationService.addDataSource(dataSource);
  }
  
  @Put('data-sources/:id')
  async updateDataSource(@Param('id') id: string, @Body() updates: any) {
    return this.dataAggregationService.updateDataSource(id, updates);
  }
  
  @Delete('data-sources/:id')
  async deleteDataSource(@Param('id') id: string) {
    return this.dataAggregationService.deleteDataSource(id);
  }
  
  @Get('metrics/:metric')
  async getMetricData(
    @Param('metric') metric: string,
    @Query('startDate') startDate?: string,
    @Query('endDate') endDate?: string,
  ) {
    const start = startDate ? new Date(startDate) : undefined;
    const end = endDate ? new Date(endDate) : undefined;
    
    return this.dataAggregationService.getMetricData(metric, start, end);
  }
  
  @Get('metrics')
  async getMultiMetricData(
    @Query('metrics') metrics: string,
    @Query('startDate') startDate?: string,
    @Query('endDate') endDate?: string,
  ) {
    const metricsArray = metrics.split(',');
    const start = startDate ? new Date(startDate) : undefined;
    const end = endDate ? new Date(endDate) : undefined;
    
    return this.dataAggregationService.getMultiMetricData(metricsArray, start, end);
  }

  /**
   * Prediction Endpoints
   */
  
  @Get('models')
  async getModels() {
    return this.predictionService.getModels();
  }
  
  @Get('models/:id')
  async getModel(@Param('id') id: string) {
    return this.predictionService.getModel(id);
  }
  
  @Post('models/:id/train')
  async trainModel(@Param('id') id: string) {
    return this.predictionService.trainModel(id);
  }
  
  @Get('predict/:modelId/:metric/:horizon')
  async predict(
    @Param('modelId') modelId: string,
    @Param('metric') metric: string,
    @Param('horizon') horizon: string,
    @Body() context?: Record<string, any>,
  ) {
    return this.predictionService.predict(modelId, metric, horizon, context);
  }

  /**
   * Recommendation Endpoints
   */
  
  @Get('rules')
  async getRules() {
    return this.recommendationService.getRules();
  }
  
  @Get('rules/:id')
  async getRule(@Param('id') id: string) {
    return this.recommendationService.getRule(id);
  }
  
  @Post('rules')
  async addRule(@Body() rule: any) {
    return this.recommendationService.addRule(rule);
  }
  
  @Put('rules/:id')
  async updateRule(@Param('id') id: string, @Body() updates: any) {
    return this.recommendationService.updateRule(id, updates);
  }
  
  @Delete('rules/:id')
  async deleteRule(@Param('id') id: string) {
    return this.recommendationService.deleteRule(id);
  }
  
  @Get('recommendations')
  async getRecommendations(@Query('tags') tags?: string) {
    const tagsArray = tags ? tags.split(',') : undefined;
    return this.recommendationService.generateRecommendations(tagsArray);
  }
  
  @Get('recommendations/metric/:metric')
  async getRecommendationsForMetric(@Param('metric') metric: string) {
    return this.recommendationService.getRecommendationsForMetric(metric);
  }
  
  @Get('recommendations/tags')
  async getRecommendationsByTags(@Query('tags') tags: string) {
    const tagsArray = tags.split(',');
    return this.recommendationService.getRecommendationsByTags(tagsArray);
  }
  
  @Get('recommendations/top')
  async getTopRecommendations(@Query('limit') limit?: string) {
    const limitNum = limit ? parseInt(limit, 10) : 5;
    return this.recommendationService.getTopRecommendations(limitNum);
  }
}
