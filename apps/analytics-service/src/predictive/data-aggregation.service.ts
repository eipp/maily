/**
 * Data Aggregation Service
 * 
 * This service provides multi-platform data aggregation for predictive analytics.
 */

import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { RedisService } from '../utils/redis.service';
import { DatabaseService } from '../storage/database.service';
import { EventService } from '../events/event.service';

interface DataSource {
  id: string;
  name: string;
  type: string;
  config: Record<string, any>;
  enabled: boolean;
}

interface AggregatedData {
  id: string;
  source: string;
  timestamp: Date;
  data: Record<string, any>;
  metadata: Record<string, any>;
}

@Injectable()
export class DataAggregationService {
  private readonly logger = new Logger(DataAggregationService.name);
  private dataSources: DataSource[] = [];
  private readonly CACHE_KEY_PREFIX = 'predictive:aggregated:';
  private readonly CACHE_TTL = 3600; // 1 hour

  constructor(
    private readonly configService: ConfigService,
    private readonly redisService: RedisService,
    private readonly databaseService: DatabaseService,
    private readonly eventService: EventService,
  ) {
    this.initializeDataSources();
  }

  /**
   * Initialize data sources from configuration
   */
  private async initializeDataSources(): Promise<void> {
    try {
      // Load data sources from configuration
      const configuredSources = this.configService.get<DataSource[]>('analytics.dataSources') || [];
      
      // Load data sources from database
      const dbSources = await this.databaseService.getDataSources();
      
      // Merge sources, with database taking precedence
      this.dataSources = [
        ...configuredSources,
        ...dbSources.filter(dbSource => 
          !configuredSources.some(configSource => configSource.id === dbSource.id)
        )
      ];
      
      this.logger.log(`Initialized ${this.dataSources.length} data sources`);
    } catch (error) {
      this.logger.error(`Failed to initialize data sources: ${error.message}`, error.stack);
      // Initialize with empty array to prevent errors
      this.dataSources = [];
    }
  }

  /**
   * Get all data sources
   */
  async getDataSources(): Promise<DataSource[]> {
    return this.dataSources;
  }

  /**
   * Add a new data source
   */
  async addDataSource(dataSource: Omit<DataSource, 'id'>): Promise<DataSource> {
    try {
      // Generate ID if not provided
      const id = `source_${Date.now()}`;
      
      const newSource: DataSource = {
        id,
        ...dataSource,
      };
      
      // Save to database
      await this.databaseService.saveDataSource(newSource);
      
      // Add to in-memory list
      this.dataSources.push(newSource);
      
      this.logger.log(`Added new data source: ${newSource.name} (${newSource.id})`);
      
      return newSource;
    } catch (error) {
      this.logger.error(`Failed to add data source: ${error.message}`, error.stack);
      throw error;
    }
  }

  /**
   * Update an existing data source
   */
  async updateDataSource(id: string, updates: Partial<DataSource>): Promise<DataSource> {
    try {
      // Find data source
      const sourceIndex = this.dataSources.findIndex(source => source.id === id);
      
      if (sourceIndex === -1) {
        throw new Error(`Data source not found: ${id}`);
      }
      
      // Update data source
      const updatedSource = {
        ...this.dataSources[sourceIndex],
        ...updates,
      };
      
      // Save to database
      await this.databaseService.saveDataSource(updatedSource);
      
      // Update in-memory list
      this.dataSources[sourceIndex] = updatedSource;
      
      this.logger.log(`Updated data source: ${updatedSource.name} (${updatedSource.id})`);
      
      return updatedSource;
    } catch (error) {
      this.logger.error(`Failed to update data source: ${error.message}`, error.stack);
      throw error;
    }
  }

  /**
   * Delete a data source
   */
  async deleteDataSource(id: string): Promise<boolean> {
    try {
      // Find data source
      const sourceIndex = this.dataSources.findIndex(source => source.id === id);
      
      if (sourceIndex === -1) {
        throw new Error(`Data source not found: ${id}`);
      }
      
      // Delete from database
      await this.databaseService.deleteDataSource(id);
      
      // Remove from in-memory list
      this.dataSources.splice(sourceIndex, 1);
      
      this.logger.log(`Deleted data source: ${id}`);
      
      return true;
    } catch (error) {
      this.logger.error(`Failed to delete data source: ${error.message}`, error.stack);
      throw error;
    }
  }

  /**
   * Aggregate data from all enabled sources
   */
  async aggregateData(startDate?: Date, endDate?: Date): Promise<AggregatedData[]> {
    try {
      const enabledSources = this.dataSources.filter(source => source.enabled);
      
      if (enabledSources.length === 0) {
        this.logger.warn('No enabled data sources found');
        return [];
      }
      
      // Set default date range if not provided
      const end = endDate || new Date();
      const start = startDate || new Date(end.getTime() - 30 * 24 * 60 * 60 * 1000); // 30 days ago
      
      // Check cache first
      const cacheKey = `${this.CACHE_KEY_PREFIX}${start.getTime()}_${end.getTime()}`;
      const cachedData = await this.redisService.get(cacheKey);
      
      if (cachedData) {
        this.logger.log('Using cached aggregated data');
        return JSON.parse(cachedData);
      }
      
      // Aggregate data from each source
      const aggregationPromises = enabledSources.map(source => this.aggregateFromSource(source, start, end));
      
      // Wait for all aggregations to complete
      const aggregatedDataArrays = await Promise.all(aggregationPromises);
      
      // Flatten the array of arrays
      const aggregatedData = aggregatedDataArrays.flat();
      
      // Cache the result
      await this.redisService.set(cacheKey, JSON.stringify(aggregatedData), this.CACHE_TTL);
      
      this.logger.log(`Aggregated data from ${enabledSources.length} sources, total records: ${aggregatedData.length}`);
      
      return aggregatedData;
    } catch (error) {
      this.logger.error(`Failed to aggregate data: ${error.message}`, error.stack);
      throw error;
    }
  }

  /**
   * Aggregate data from a specific source
   */
  private async aggregateFromSource(source: DataSource, startDate: Date, endDate: Date): Promise<AggregatedData[]> {
    try {
      this.logger.log(`Aggregating data from source: ${source.name} (${source.id})`);
      
      let data: AggregatedData[] = [];
      
      switch (source.type) {
        case 'database':
          data = await this.aggregateFromDatabase(source, startDate, endDate);
          break;
        case 'api':
          data = await this.aggregateFromApi(source, startDate, endDate);
          break;
        case 'event':
          data = await this.aggregateFromEvents(source, startDate, endDate);
          break;
        default:
          this.logger.warn(`Unknown data source type: ${source.type}`);
          return [];
      }
      
      // Normalize data
      const normalizedData = this.normalizeData(data, source);
      
      this.logger.log(`Aggregated ${normalizedData.length} records from source: ${source.name}`);
      
      return normalizedData;
    } catch (error) {
      this.logger.error(`Failed to aggregate from source ${source.name}: ${error.message}`, error.stack);
      // Return empty array to prevent entire aggregation from failing
      return [];
    }
  }

  /**
   * Aggregate data from database source
   */
  private async aggregateFromDatabase(source: DataSource, startDate: Date, endDate: Date): Promise<AggregatedData[]> {
    try {
      const { table, dateField } = source.config;
      
      if (!table || !dateField) {
        throw new Error('Missing required configuration: table or dateField');
      }
      
      // Query database
      const records = await this.databaseService.query(
        `SELECT * FROM ${table} WHERE ${dateField} BETWEEN ? AND ?`,
        [startDate, endDate]
      );
      
      // Convert to AggregatedData format
      return records.map(record => ({
        id: `${source.id}_${record.id || Date.now()}`,
        source: source.id,
        timestamp: new Date(record[dateField]),
        data: record,
        metadata: {
          source_type: 'database',
          table,
        },
      }));
    } catch (error) {
      this.logger.error(`Failed to aggregate from database: ${error.message}`, error.stack);
      throw error;
    }
  }

  /**
   * Aggregate data from API source
   */
  private async aggregateFromApi(source: DataSource, startDate: Date, endDate: Date): Promise<AggregatedData[]> {
    try {
      const { endpoint, method, headers, dateField } = source.config;
      
      if (!endpoint || !method || !dateField) {
        throw new Error('Missing required configuration: endpoint, method, or dateField');
      }
      
      // Fetch data from API
      const response = await fetch(endpoint, {
        method: method,
        headers: headers || {},
        body: method !== 'GET' ? JSON.stringify({
          startDate: startDate.toISOString(),
          endDate: endDate.toISOString(),
        }) : undefined,
      });
      
      if (!response.ok) {
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Handle array or object response
      const records = Array.isArray(data) ? data : [data];
      
      // Convert to AggregatedData format
      return records.map(record => ({
        id: `${source.id}_${record.id || Date.now()}`,
        source: source.id,
        timestamp: new Date(record[dateField]),
        data: record,
        metadata: {
          source_type: 'api',
          endpoint,
        },
      }));
    } catch (error) {
      this.logger.error(`Failed to aggregate from API: ${error.message}`, error.stack);
      throw error;
    }
  }

  /**
   * Aggregate data from events
   */
  private async aggregateFromEvents(source: DataSource, startDate: Date, endDate: Date): Promise<AggregatedData[]> {
    try {
      const { eventType } = source.config;
      
      if (!eventType) {
        throw new Error('Missing required configuration: eventType');
      }
      
      // Get events from event service
      const events = await this.eventService.getEvents(eventType, startDate, endDate);
      
      // Convert to AggregatedData format
      return events.map(event => ({
        id: `${source.id}_${event.id || Date.now()}`,
        source: source.id,
        timestamp: new Date(event.timestamp),
        data: event.data,
        metadata: {
          source_type: 'event',
          event_type: eventType,
        },
      }));
    } catch (error) {
      this.logger.error(`Failed to aggregate from events: ${error.message}`, error.stack);
      throw error;
    }
  }

  /**
   * Normalize data from different sources
   */
  private normalizeData(data: AggregatedData[], source: DataSource): AggregatedData[] {
    try {
      // Apply source-specific normalization
      const { normalization } = source.config;
      
      if (!normalization) {
        return data; // No normalization needed
      }
      
      // Apply field mappings
      if (normalization.fieldMappings) {
        data = data.map(item => {
          const normalizedData = { ...item.data };
          
          // Apply field mappings
          for (const [sourceField, targetField] of Object.entries(normalization.fieldMappings)) {
            if (normalizedData[sourceField] !== undefined) {
              normalizedData[targetField] = normalizedData[sourceField];
              
              // Remove original field if different
              if (sourceField !== targetField) {
                delete normalizedData[sourceField];
              }
            }
          }
          
          return {
            ...item,
            data: normalizedData,
          };
        });
      }
      
      // Apply value transformations
      if (normalization.valueTransformations) {
        data = data.map(item => {
          const normalizedData = { ...item.data };
          
          // Apply value transformations
          for (const [field, transformation] of Object.entries(normalization.valueTransformations)) {
            if (normalizedData[field] !== undefined) {
              switch (transformation.type) {
                case 'scale':
                  normalizedData[field] = normalizedData[field] * transformation.factor;
                  break;
                case 'map':
                  normalizedData[field] = transformation.mapping[normalizedData[field]] || normalizedData[field];
                  break;
                case 'format':
                  if (transformation.format === 'date') {
                    normalizedData[field] = new Date(normalizedData[field]).toISOString();
                  }
                  break;
                default:
                  break;
              }
            }
          }
          
          return {
            ...item,
            data: normalizedData,
          };
        });
      }
      
      return data;
    } catch (error) {
      this.logger.error(`Failed to normalize data: ${error.message}`, error.stack);
      return data; // Return original data on error
    }
  }

  /**
   * Get aggregated data for a specific metric
   */
  async getMetricData(metricName: string, startDate?: Date, endDate?: Date): Promise<any[]> {
    try {
      // Get all aggregated data
      const aggregatedData = await this.aggregateData(startDate, endDate);
      
      // Filter and transform data for the specific metric
      const metricData = aggregatedData
        .filter(item => item.data[metricName] !== undefined)
        .map(item => ({
          timestamp: item.timestamp,
          value: item.data[metricName],
          source: item.source,
        }))
        .sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
      
      return metricData;
    } catch (error) {
      this.logger.error(`Failed to get metric data: ${error.message}`, error.stack);
      throw error;
    }
  }

  /**
   * Get aggregated data for multiple metrics
   */
  async getMultiMetricData(metricNames: string[], startDate?: Date, endDate?: Date): Promise<Record<string, any[]>> {
    try {
      // Get all aggregated data
      const aggregatedData = await this.aggregateData(startDate, endDate);
      
      // Initialize result object
      const result: Record<string, any[]> = {};
      
      // Process each metric
      for (const metricName of metricNames) {
        result[metricName] = aggregatedData
          .filter(item => item.data[metricName] !== undefined)
          .map(item => ({
            timestamp: item.timestamp,
            value: item.data[metricName],
            source: item.source,
          }))
          .sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
      }
      
      return result;
    } catch (error) {
      this.logger.error(`Failed to get multi-metric data: ${error.message}`, error.stack);
      throw error;
    }
  }
}
