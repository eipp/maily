/**
 * Real-time Analytics Service
 * 
 * This service provides real-time data processing and analytics capabilities
 * using Kafka for streaming data and real-time dashboards.
 */

import { Kafka, Consumer, Producer, KafkaMessage } from 'kafkajs';
import { Redis } from 'ioredis';
import { v4 as uuidv4 } from 'uuid';
import { logger } from '../utils/logger';
import { prisma } from '../lib/prisma';
import { AnalyticsEvent, EventType } from '../models/analytics-event';
import { AnomalyDetector } from '../utils/anomaly-detector';

// Environment variables
const KAFKA_BROKERS = (process.env.KAFKA_BROKERS || 'localhost:9092').split(',');
const KAFKA_CLIENT_ID = process.env.KAFKA_CLIENT_ID || 'analytics-service';
const KAFKA_GROUP_ID = process.env.KAFKA_GROUP_ID || 'analytics-service-group';
const KAFKA_TOPIC_PREFIX = process.env.KAFKA_TOPIC_PREFIX || 'maily.';
const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';
const BATCH_SIZE = parseInt(process.env.ANALYTICS_BATCH_SIZE || '100', 10);
const BATCH_WINDOW_MS = parseInt(process.env.ANALYTICS_BATCH_WINDOW_MS || '5000', 10);
const ENABLE_ANOMALY_DETECTION = process.env.ENABLE_ANOMALY_DETECTION === 'true';

// Kafka topics
const TOPICS = {
  EMAIL_EVENTS: `${KAFKA_TOPIC_PREFIX}email-events`,
  CAMPAIGN_EVENTS: `${KAFKA_TOPIC_PREFIX}campaign-events`,
  USER_EVENTS: `${KAFKA_TOPIC_PREFIX}user-events`,
  SYSTEM_EVENTS: `${KAFKA_TOPIC_PREFIX}system-events`,
  ANALYTICS_RESULTS: `${KAFKA_TOPIC_PREFIX}analytics-results`,
  ANOMALIES: `${KAFKA_TOPIC_PREFIX}anomalies`,
};

/**
 * Real-time Analytics Service
 */
export class RealTimeAnalyticsService {
  private kafka: Kafka;
  private producer: Producer;
  private consumer: Consumer;
  private redis: Redis;
  private anomalyDetector: AnomalyDetector;
  private eventBatches: Map<string, AnalyticsEvent[]>;
  private batchTimers: Map<string, NodeJS.Timeout>;
  private isRunning: boolean;
  
  constructor() {
    // Initialize Kafka
    this.kafka = new Kafka({
      clientId: KAFKA_CLIENT_ID,
      brokers: KAFKA_BROKERS,
      retry: {
        initialRetryTime: 100,
        retries: 8,
      },
    });
    
    // Initialize producer
    this.producer = this.kafka.producer({
      allowAutoTopicCreation: true,
      transactionalId: `${KAFKA_CLIENT_ID}-producer-${uuidv4()}`,
    });
    
    // Initialize consumer
    this.consumer = this.kafka.consumer({
      groupId: KAFKA_GROUP_ID,
      sessionTimeout: 30000,
      heartbeatInterval: 3000,
    });
    
    // Initialize Redis
    this.redis = new Redis(REDIS_URL, {
      maxRetriesPerRequest: 3,
      enableReadyCheck: false,
    });
    
    // Initialize anomaly detector
    this.anomalyDetector = new AnomalyDetector();
    
    // Initialize event batches
    this.eventBatches = new Map<string, AnalyticsEvent[]>();
    this.batchTimers = new Map<string, NodeJS.Timeout>();
    this.isRunning = false;
    
    logger.info('Real-time Analytics Service initialized');
  }
  
  /**
   * Start the real-time analytics service
   */
  async start(): Promise<void> {
    if (this.isRunning) {
      logger.warn('Real-time Analytics Service is already running');
      return;
    }
    
    try {
      // Connect to Kafka
      await this.producer.connect();
      await this.consumer.connect();
      
      // Subscribe to topics
      await this.consumer.subscribe({
        topics: Object.values(TOPICS).filter(topic => topic !== TOPICS.ANALYTICS_RESULTS && topic !== TOPICS.ANOMALIES),
        fromBeginning: false,
      });
      
      // Start consuming messages
      await this.consumer.run({
        eachMessage: async ({ topic, partition, message }) => {
          try {
            await this.processMessage(topic, message);
          } catch (error) {
            logger.error(`Error processing message from topic ${topic}:`, error);
          }
        },
      });
      
      this.isRunning = true;
      logger.info('Real-time Analytics Service started');
    } catch (error) {
      logger.error('Failed to start Real-time Analytics Service:', error);
      throw error;
    }
  }
  
  /**
   * Stop the real-time analytics service
   */
  async stop(): Promise<void> {
    if (!this.isRunning) {
      logger.warn('Real-time Analytics Service is not running');
      return;
    }
    
    try {
      // Clear all batch timers
      for (const timer of this.batchTimers.values()) {
        clearTimeout(timer);
      }
      
      // Process any remaining batches
      for (const [batchKey, events] of this.eventBatches.entries()) {
        if (events.length > 0) {
          await this.processBatch(batchKey, events);
        }
      }
      
      // Disconnect from Kafka
      await this.consumer.disconnect();
      await this.producer.disconnect();
      
      // Disconnect from Redis
      await this.redis.quit();
      
      this.isRunning = false;
      logger.info('Real-time Analytics Service stopped');
    } catch (error) {
      logger.error('Error stopping Real-time Analytics Service:', error);
      throw error;
    }
  }
  
  /**
   * Process a Kafka message
   * 
   * @param topic Topic
   * @param message Kafka message
   */
  private async processMessage(topic: string, message: KafkaMessage): Promise<void> {
    if (!message.value) {
      logger.warn(`Received message with no value from topic ${topic}`);
      return;
    }
    
    try {
      // Parse message value
      const event = JSON.parse(message.value.toString()) as AnalyticsEvent;
      
      // Add event to batch
      this.addEventToBatch(topic, event);
      
      // Check for anomalies if enabled
      if (ENABLE_ANOMALY_DETECTION) {
        this.checkForAnomalies(event);
      }
      
      // Update real-time counters
      await this.updateRealTimeCounters(event);
    } catch (error) {
      logger.error(`Error processing message from topic ${topic}:`, error);
    }
  }
  
  /**
   * Add event to batch
   * 
   * @param topic Topic
   * @param event Analytics event
   */
  private addEventToBatch(topic: string, event: AnalyticsEvent): void {
    // Determine batch key based on event type
    let batchKey: string;
    
    switch (topic) {
      case TOPICS.EMAIL_EVENTS:
        batchKey = `email:${event.entityId || 'unknown'}`;
        break;
      case TOPICS.CAMPAIGN_EVENTS:
        batchKey = `campaign:${event.entityId || 'unknown'}`;
        break;
      case TOPICS.USER_EVENTS:
        batchKey = `user:${event.entityId || 'unknown'}`;
        break;
      case TOPICS.SYSTEM_EVENTS:
        batchKey = `system:${event.eventType}`;
        break;
      default:
        batchKey = `unknown:${uuidv4()}`;
    }
    
    // Get or create batch
    if (!this.eventBatches.has(batchKey)) {
      this.eventBatches.set(batchKey, []);
    }
    
    // Add event to batch
    const batch = this.eventBatches.get(batchKey)!;
    batch.push(event);
    
    // Process batch if it reaches the batch size
    if (batch.length >= BATCH_SIZE) {
      // Clear any existing timer
      if (this.batchTimers.has(batchKey)) {
        clearTimeout(this.batchTimers.get(batchKey)!);
        this.batchTimers.delete(batchKey);
      }
      
      // Process batch
      this.processBatch(batchKey, batch);
      
      // Clear batch
      this.eventBatches.set(batchKey, []);
    } else if (!this.batchTimers.has(batchKey)) {
      // Set timer to process batch after batch window
      const timer = setTimeout(() => {
        const currentBatch = this.eventBatches.get(batchKey)!;
        
        if (currentBatch.length > 0) {
          this.processBatch(batchKey, currentBatch);
          this.eventBatches.set(batchKey, []);
        }
        
        this.batchTimers.delete(batchKey);
      }, BATCH_WINDOW_MS);
      
      this.batchTimers.set(batchKey, timer);
    }
  }
  
  /**
   * Process a batch of events
   * 
   * @param batchKey Batch key
   * @param events Events
   */
  private async processBatch(batchKey: string, events: AnalyticsEvent[]): Promise<void> {
    if (events.length === 0) {
      return;
    }
    
    try {
      logger.debug(`Processing batch of ${events.length} events for key ${batchKey}`);
      
      // Group events by type
      const eventsByType = new Map<EventType, AnalyticsEvent[]>();
      
      for (const event of events) {
        if (!eventsByType.has(event.eventType)) {
          eventsByType.set(event.eventType, []);
        }
        
        eventsByType.get(event.eventType)!.push(event);
      }
      
      // Process each event type
      for (const [eventType, typeEvents] of eventsByType.entries()) {
        // Aggregate events
        const aggregatedData = this.aggregateEvents(eventType, typeEvents);
        
        // Store aggregated data
        await this.storeAggregatedData(batchKey, eventType, aggregatedData);
        
        // Publish aggregated data to Kafka
        await this.publishAggregatedData(batchKey, eventType, aggregatedData);
      }
      
      // Store events in database
      await this.storeEvents(events);
    } catch (error) {
      logger.error(`Error processing batch for key ${batchKey}:`, error);
    }
  }
  
  /**
   * Aggregate events
   * 
   * @param eventType Event type
   * @param events Events
   * @returns Aggregated data
   */
  private aggregateEvents(eventType: EventType, events: AnalyticsEvent[]): Record<string, any> {
    // Initialize aggregated data
    const aggregatedData: Record<string, any> = {
      eventType,
      count: events.length,
      timestamp: new Date().toISOString(),
    };
    
    // Aggregate based on event type
    switch (eventType) {
      case EventType.EMAIL_SENT:
      case EventType.EMAIL_DELIVERED:
      case EventType.EMAIL_OPENED:
      case EventType.EMAIL_CLICKED:
      case EventType.EMAIL_BOUNCED:
      case EventType.EMAIL_SPAM:
      case EventType.EMAIL_UNSUBSCRIBED:
        // Aggregate email events
        this.aggregateEmailEvents(eventType, events, aggregatedData);
        break;
      
      case EventType.CAMPAIGN_CREATED:
      case EventType.CAMPAIGN_UPDATED:
      case EventType.CAMPAIGN_SENT:
      case EventType.CAMPAIGN_COMPLETED:
        // Aggregate campaign events
        this.aggregateCampaignEvents(eventType, events, aggregatedData);
        break;
      
      case EventType.USER_CREATED:
      case EventType.USER_UPDATED:
      case EventType.USER_DELETED:
      case EventType.USER_LOGIN:
      case EventType.USER_LOGOUT:
        // Aggregate user events
        this.aggregateUserEvents(eventType, events, aggregatedData);
        break;
      
      case EventType.SYSTEM_ERROR:
      case EventType.SYSTEM_WARNING:
      case EventType.SYSTEM_INFO:
        // Aggregate system events
        this.aggregateSystemEvents(eventType, events, aggregatedData);
        break;
      
      default:
        // Default aggregation
        aggregatedData.events = events;
    }
    
    return aggregatedData;
  }
  
  /**
   * Aggregate email events
   * 
   * @param eventType Event type
   * @param events Events
   * @param aggregatedData Aggregated data
   */
  private aggregateEmailEvents(
    eventType: EventType,
    events: AnalyticsEvent[],
    aggregatedData: Record<string, any>
  ): void {
    // Group by campaign
    const byCampaign = new Map<string, AnalyticsEvent[]>();
    
    for (const event of events) {
      const campaignId = event.metadata?.campaignId || 'unknown';
      
      if (!byCampaign.has(campaignId)) {
        byCampaign.set(campaignId, []);
      }
      
      byCampaign.get(campaignId)!.push(event);
    }
    
    // Aggregate by campaign
    aggregatedData.campaigns = Array.from(byCampaign.entries()).map(([campaignId, campaignEvents]) => ({
      campaignId,
      count: campaignEvents.length,
    }));
    
    // Calculate rates
    if (eventType === EventType.EMAIL_OPENED) {
      aggregatedData.openRate = this.calculateOpenRate(events);
    } else if (eventType === EventType.EMAIL_CLICKED) {
      aggregatedData.clickRate = this.calculateClickRate(events);
      
      // Aggregate clicks by link
      const byLink = new Map<string, number>();
      
      for (const event of events) {
        const link = event.metadata?.link || 'unknown';
        byLink.set(link, (byLink.get(link) || 0) + 1);
      }
      
      aggregatedData.linkClicks = Array.from(byLink.entries()).map(([link, count]) => ({
        link,
        count,
      }));
    } else if (eventType === EventType.EMAIL_BOUNCED) {
      aggregatedData.bounceRate = this.calculateBounceRate(events);
      
      // Aggregate bounces by reason
      const byReason = new Map<string, number>();
      
      for (const event of events) {
        const reason = event.metadata?.reason || 'unknown';
        byReason.set(reason, (byReason.get(reason) || 0) + 1);
      }
      
      aggregatedData.bounceReasons = Array.from(byReason.entries()).map(([reason, count]) => ({
        reason,
        count,
      }));
    }
  }
  
  /**
   * Aggregate campaign events
   * 
   * @param eventType Event type
   * @param events Events
   * @param aggregatedData Aggregated data
   */
  private aggregateCampaignEvents(
    eventType: EventType,
    events: AnalyticsEvent[],
    aggregatedData: Record<string, any>
  ): void {
    // Group by user
    const byUser = new Map<string, AnalyticsEvent[]>();
    
    for (const event of events) {
      const userId = event.metadata?.userId || 'unknown';
      
      if (!byUser.has(userId)) {
        byUser.set(userId, []);
      }
      
      byUser.get(userId)!.push(event);
    }
    
    // Aggregate by user
    aggregatedData.users = Array.from(byUser.entries()).map(([userId, userEvents]) => ({
      userId,
      count: userEvents.length,
    }));
    
    if (eventType === EventType.CAMPAIGN_SENT) {
      // Calculate total recipients
      let totalRecipients = 0;
      
      for (const event of events) {
        totalRecipients += event.metadata?.recipientCount || 0;
      }
      
      aggregatedData.totalRecipients = totalRecipients;
    }
  }
  
  /**
   * Aggregate user events
   * 
   * @param eventType Event type
   * @param events Events
   * @param aggregatedData Aggregated data
   */
  private aggregateUserEvents(
    eventType: EventType,
    events: AnalyticsEvent[],
    aggregatedData: Record<string, any>
  ): void {
    if (eventType === EventType.USER_LOGIN || eventType === EventType.USER_LOGOUT) {
      // Calculate active users
      const uniqueUsers = new Set<string>();
      
      for (const event of events) {
        if (event.entityId) {
          uniqueUsers.add(event.entityId);
        }
      }
      
      aggregatedData.uniqueUsers = uniqueUsers.size;
      
      // Group by user agent
      const byUserAgent = new Map<string, number>();
      
      for (const event of events) {
        const userAgent = event.metadata?.userAgent || 'unknown';
        byUserAgent.set(userAgent, (byUserAgent.get(userAgent) || 0) + 1);
      }
      
      aggregatedData.userAgents = Array.from(byUserAgent.entries()).map(([userAgent, count]) => ({
        userAgent,
        count,
      }));
    }
  }
  
  /**
   * Aggregate system events
   * 
   * @param eventType Event type
   * @param events Events
   * @param aggregatedData Aggregated data
   */
  private aggregateSystemEvents(
    eventType: EventType,
    events: AnalyticsEvent[],
    aggregatedData: Record<string, any>
  ): void {
    // Group by service
    const byService = new Map<string, AnalyticsEvent[]>();
    
    for (const event of events) {
      const service = event.metadata?.service || 'unknown';
      
      if (!byService.has(service)) {
        byService.set(service, []);
      }
      
      byService.get(service)!.push(event);
    }
    
    // Aggregate by service
    aggregatedData.services = Array.from(byService.entries()).map(([service, serviceEvents]) => ({
      service,
      count: serviceEvents.length,
    }));
    
    if (eventType === EventType.SYSTEM_ERROR) {
      // Group by error code
      const byErrorCode = new Map<string, number>();
      
      for (const event of events) {
        const errorCode = event.metadata?.errorCode || 'unknown';
        byErrorCode.set(errorCode, (byErrorCode.get(errorCode) || 0) + 1);
      }
      
      aggregatedData.errorCodes = Array.from(byErrorCode.entries()).map(([errorCode, count]) => ({
        errorCode,
        count,
      }));
    }
  }
  
  /**
   * Calculate open rate
   * 
   * @param events Events
   * @returns Open rate
   */
  private calculateOpenRate(events: AnalyticsEvent[]): number {
    // Group by email
    const byEmail = new Map<string, boolean>();
    
    for (const event of events) {
      if (event.entityId) {
        byEmail.set(event.entityId, true);
      }
    }
    
    // Get total sent emails
    return byEmail.size / events.length;
  }
  
  /**
   * Calculate click rate
   * 
   * @param events Events
   * @returns Click rate
   */
  private calculateClickRate(events: AnalyticsEvent[]): number {
    // Group by email
    const byEmail = new Map<string, boolean>();
    
    for (const event of events) {
      if (event.entityId) {
        byEmail.set(event.entityId, true);
      }
    }
    
    // Get total sent emails
    return byEmail.size / events.length;
  }
  
  /**
   * Calculate bounce rate
   * 
   * @param events Events
   * @returns Bounce rate
   */
  private calculateBounceRate(events: AnalyticsEvent[]): number {
    // Group by email
    const byEmail = new Map<string, boolean>();
    
    for (const event of events) {
      if (event.entityId) {
        byEmail.set(event.entityId, true);
      }
    }
    
    // Get total sent emails
    return byEmail.size / events.length;
  }
  
  /**
   * Store aggregated data
   * 
   * @param batchKey Batch key
   * @param eventType Event type
   * @param aggregatedData Aggregated data
   */
  private async storeAggregatedData(
    batchKey: string,
    eventType: EventType,
    aggregatedData: Record<string, any>
  ): Promise<void> {
    try {
      // Store in Redis for real-time dashboards
      const redisKey = `analytics:${batchKey}:${eventType}`;
      await this.redis.set(redisKey, JSON.stringify(aggregatedData), 'EX', 86400); // 24 hours
      
      // Store in database for historical analysis
      await prisma.analyticsAggregate.create({
        data: {
          id: uuidv4(),
          key: batchKey,
          eventType,
          data: aggregatedData,
          timestamp: new Date(),
        },
      });
    } catch (error) {
      logger.error(`Error storing aggregated data for ${batchKey}:${eventType}:`, error);
    }
  }
  
  /**
   * Publish aggregated data to Kafka
   * 
   * @param batchKey Batch key
   * @param eventType Event type
   * @param aggregatedData Aggregated data
   */
  private async publishAggregatedData(
    batchKey: string,
    eventType: EventType,
    aggregatedData: Record<string, any>
  ): Promise<void> {
    try {
      await this.producer.send({
        topic: TOPICS.ANALYTICS_RESULTS,
        messages: [
          {
            key: batchKey,
            value: JSON.stringify({
              batchKey,
              eventType,
              data: aggregatedData,
              timestamp: new Date().toISOString(),
            }),
          },
        ],
      });
    } catch (error) {
      logger.error(`Error publishing aggregated data for ${batchKey}:${eventType}:`, error);
    }
  }
  
  /**
   * Store events in database
   * 
   * @param events Events
   */
  private async storeEvents(events: AnalyticsEvent[]): Promise<void> {
    try {
      // Store events in batches
      const batches = [];
      const batchSize = 100;
      
      for (let i = 0; i < events.length; i += batchSize) {
        const batch = events.slice(i, i + batchSize);
        
        batches.push(
          prisma.analyticsEvent.createMany({
            data: batch.map(event => ({
              id: event.id || uuidv4(),
              eventType: event.eventType,
              entityId: event.entityId,
              userId: event.userId,
              metadata: event.metadata || {},
              timestamp: new Date(event.timestamp || Date.now()),
            })),
            skipDuplicates: true,
          })
        );
      }
      
      await Promise.all(batches);
    } catch (error) {
      logger.error(`Error storing events:`, error);
    }
  }
  
  /**
   * Update real-time counters
   * 
   * @param event Analytics event
   */
  private async updateRealTimeCounters(event: AnalyticsEvent): Promise<void> {
    try {
      const timestamp = Math.floor(Date.now() / 1000);
      const hourKey = Math.floor(timestamp / 3600) * 3600;
      const minuteKey = Math.floor(timestamp / 60) * 60;
      
      // Update counters for different time windows
      const pipeline = this.redis.pipeline();
      
      // Increment total counter
      pipeline.incr(`counter:${event.eventType}:total`);
      
      // Increment hourly counter
      pipeline.incr(`counter:${event.eventType}:hourly:${hourKey}`);
      pipeline.expire(`counter:${event.eventType}:hourly:${hourKey}`, 86400); // 24 hours
      
      // Increment minute counter
      pipeline.incr(`counter:${event.eventType}:minute:${minuteKey}`);
      pipeline.expire(`counter:${event.eventType}:minute:${minuteKey}`, 3600); // 1 hour
      
      // If event has entityId, update entity-specific counters
      if (event.entityId) {
        // Increment entity total counter
        pipeline.incr(`counter:${event.eventType}:entity:${event.entityId}:total`);
        
        // Increment entity hourly counter
        pipeline.incr(`counter:${event.eventType}:entity:${event.entityId}:hourly:${hourKey}`);
        pipeline.expire(`counter:${event.eventType}:entity:${event.entityId}:hourly:${hourKey}`, 86400); // 24 hours
        
        // Increment entity minute counter
        pipeline.incr(`counter:${event.eventType}:entity:${event.entityId}:minute:${minuteKey}`);
        pipeline.expire(`counter:${event.eventType}:entity:${event.entityId}:minute:${minuteKey}`, 3600); // 1 hour
      }
      
      // If event has userId, update user-specific counters
      if (event.userId) {
        // Increment user total counter
        pipeline.incr(`counter:${event.eventType}:user:${event.userId}:total`);
        
        // Increment user hourly counter
        pipeline.incr(`counter:${event.eventType}:user:${event.userId}:hourly:${hourKey}`);
        pipeline.expire(`counter:${event.eventType}:user:${event.userId}:hourly:${hourKey}`, 86400); // 24 hours
        
        // Increment user minute counter
        pipeline.incr(`counter:${event.eventType}:user:${event.userId}:minute:${minuteKey}`);
        pipeline.expire(`counter:${event.eventType}:user:${event.userId}:minute:${minuteKey}`, 3600); // 1 hour
      }
      
      await pipeline.exec();
    } catch (error) {
      logger.error(`Error updating real-time counters for event ${event.id}:`, error);
    }
  }
  
  /**
   * Check for anomalies
   * 
   * @param event Analytics event
   */
  private async checkForAnomalies(event: AnalyticsEvent): Promise<void> {
    try {
      // Skip anomaly detection for certain event types
      if (
        event.eventType === EventType.SYSTEM_INFO ||
        event.eventType === EventType.USER_LOGIN ||
        event.eventType === EventType.USER_LOGOUT
      ) {
        return;
      }
      
      // Get current rate
      const currentRate = await this.getCurrentEventRate(event.eventType);
      
      // Check for anomalies
      const anomaly = this.anomalyDetector.detectAnomaly(event.eventType, currentRate);
      
      if (anomaly) {
        logger.warn(`Anomaly detected for ${event.eventType}: ${anomaly.message}`);
        
        // Publish anomaly to Kafka
        await this.producer.send({
          topic: TOPICS.ANOMALIES,
          messages: [
            {
              key: event.eventType,
              value: JSON.stringify({
                eventType: event.eventType,
                currentRate,
                expectedRate: anomaly.expectedRate,
                deviation: anomaly.deviation,
                message: anomaly.message,
                timestamp: new Date().toISOString(),
              }),
            },
          ],
        });
      }
    } catch (error) {
      logger.error(`Error checking for anomalies for event ${event.id}:`, error);
    }
  }
  
  /**
   * Get current event rate
   * 
   * @param eventType Event type
   * @returns Current event rate (events per minute)
   */
  private async getCurrentEventRate(eventType: EventType): Promise<number> {
    try {
      const timestamp = Math.floor(Date.now() / 1000);
      const currentMinuteKey = Math.floor(timestamp / 60) * 60;
      const previousMinuteKey = currentMinuteKey - 60;
      
      // Get counts for current and previous minute
      const pipeline = this.redis.pipeline();
      pipeline.get(`counter:${eventType}:minute:${currentMinuteKey}`);
      pipeline.get(`counter:${eventType}:minute:${previousMinuteKey}`);
      
      const results = await pipeline.exec();
      
      // Calculate rate
      const currentCount = parseInt(results![0][1] as string) || 0;
      const previousCount = parseInt(results![1][1] as string) || 0;
      
      // Use previous minute count if current minute is too new
      const secondsInCurrentMinute = timestamp % 60;
      
      if (secondsInCurrentMinute < 10 && previousCount > 0) {
        return previousCount / 60; // Events per second
      }
      
      // Use current minute count extrapolated to a full minute
      if (secondsInCurrentMinute > 0) {
        return (currentCount / secondsInCurrentMinute) * 60; // Events per minute
      }
      
      return 0;
    } catch (error) {
      logger.error(`Error getting current event rate for ${eventType}:`, error);
      return 0;
    }
  }
  
  /**
   * Get real-time analytics data
   * 
   * @param eventType Event type
   * @param entityId Entity ID (optional)
   * @param userId User ID (optional)
   * @param timeWindow Time window in seconds (default: 3600 = 1 hour)
   * @returns Real-time analytics data
   */
  async getRealTimeAnalytics(
    eventType: EventType,
    entityId?: string,
    userId?: string,
    timeWindow: number = 3600
  ): Promise<Record<string, any>> {
    try {
      const timestamp = Math.floor(Date.now() / 1000);
      const startTime = timestamp - timeWindow;
      
      // Determine key prefix
      let keyPrefix = `counter:${eventType}`;
      
      if (entityId) {
        keyPrefix = `${keyPrefix}:entity:${entityId}`;
      } else
