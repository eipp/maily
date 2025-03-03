/**
 * Predictive Analytics Module
 * 
 * This module provides predictive analytics capabilities including data aggregation,
 * machine learning predictions, and AI-generated recommendations.
 */

import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { DataAggregationService } from './data-aggregation.service';
import { PredictionService } from './prediction.service';
import { RecommendationService } from './recommendation.service';
import { PredictiveController } from './predictive.controller';
import { RedisModule } from '../utils/redis.module';

@Module({
  imports: [
    ConfigModule,
    RedisModule,
  ],
  controllers: [
    PredictiveController,
  ],
  providers: [
    DataAggregationService,
    PredictionService,
    RecommendationService,
  ],
  exports: [
    DataAggregationService,
    PredictionService,
    RecommendationService,
  ],
})
export class PredictiveModule {}
