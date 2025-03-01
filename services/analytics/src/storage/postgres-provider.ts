/**
 * PostgreSQL storage provider for analytics events
 */

import { Pool, PoolClient } from 'pg';
import {
  AnalyticsEvent,
  AnalyticsQuery,
  AnalyticsQueryResult,
  AnalyticsStorageProvider,
  AggregatedMetrics,
  TimeFrame
} from '../index';
import { createLogger } from '../utils/logger';

const logger = createLogger('postgres-provider');

/**
 * Configuration for the PostgreSQL provider
 */
export interface PostgresProviderConfig {
  /**
   * Connection string
   */
  connectionString?: string;

  /**
   * Database host
   */
  host?: string;

  /**
   * Database port
   */
  port?: number;

  /**
   * Database name
   */
  database?: string;

  /**
   * Database user
   */
  user?: string;

  /**
   * Database password
   */
  password?: string;

  /**
   * Pool size
   */
  poolSize?: number;

  /**
   * Events table name
   */
  eventsTable?: string;

  /**
   * Properties table name
   */
  propertiesTable?: string;

  /**
   * Context table name
   */
  contextTable?: string;
}

/**
 * PostgreSQL storage provider for analytics events
 *
 * This provider stores events in a PostgreSQL database with optimized
 * table structure for efficient querying and aggregation.
 */
export class PostgresStorageProvider implements AnalyticsStorageProvider {
  private pool: Pool;
  private eventsTable: string;
  private propertiesTable: string;
  private contextTable: string;
  private initialized: boolean = false;

  /**
   * Create a PostgreSQL storage provider
   * @param config Configuration options
   */
  constructor(config: PostgresProviderConfig) {
    this.eventsTable = config.eventsTable || 'analytics_events';
    this.propertiesTable = config.propertiesTable || 'analytics_properties';
    this.contextTable = config.contextTable || 'analytics_context';

    this.pool = new Pool({
      connectionString: config.connectionString,
      host: config.host,
      port: config.port,
      database: config.database,
      user: config.user,
      password: config.password,
      max: config.poolSize || 20,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 5000,
    });

    this.pool.on('error', (err) => {
      logger.error('Unexpected error on idle PostgreSQL client', { error: err.message });
    });
  }

  /**
   * Initialize the database schema
   */
  async initialize(): Promise<void> {
    if (this.initialized) {
      return;
    }

    logger.info('Initializing PostgreSQL storage provider');

    const client = await this.pool.connect();

    try {
      // Create extension for efficient JSON operations
      await client.query('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"');
      await client.query('CREATE EXTENSION IF NOT EXISTS "pgcrypto"');

      // Create events table
      await client.query(`
        CREATE TABLE IF NOT EXISTS ${this.eventsTable} (
          id UUID PRIMARY KEY,
          type VARCHAR(50) NOT NULL,
          name VARCHAR(100) NOT NULL,
          timestamp TIMESTAMPTZ NOT NULL,
          user_id VARCHAR(100),
          session_id VARCHAR(100),
          source VARCHAR(100),
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
      `);

      // Create properties table with JSONB for efficient querying
      await client.query(`
        CREATE TABLE IF NOT EXISTS ${this.propertiesTable} (
          event_id UUID NOT NULL REFERENCES ${this.eventsTable}(id) ON DELETE CASCADE,
          properties JSONB NOT NULL,
          PRIMARY KEY (event_id)
        )
      `);

      // Create context table with JSONB for efficient querying
      await client.query(`
        CREATE TABLE IF NOT EXISTS ${this.contextTable} (
          event_id UUID NOT NULL REFERENCES ${this.eventsTable}(id) ON DELETE CASCADE,
          context JSONB NOT NULL,
          PRIMARY KEY (event_id)
        )
      `);

      // Create indexes for common queries
      await client.query(`CREATE INDEX IF NOT EXISTS idx_${this.eventsTable}_type ON ${this.eventsTable}(type)`);
      await client.query(`CREATE INDEX IF NOT EXISTS idx_${this.eventsTable}_name ON ${this.eventsTable}(name)`);
      await client.query(`CREATE INDEX IF NOT EXISTS idx_${this.eventsTable}_timestamp ON ${this.eventsTable}(timestamp)`);
      await client.query(`CREATE INDEX IF NOT EXISTS idx_${this.eventsTable}_user_id ON ${this.eventsTable}(user_id)`);
      await client.query(`CREATE INDEX IF NOT EXISTS idx_${this.eventsTable}_session_id ON ${this.eventsTable}(session_id)`);

      // Create GIN indexes for JSONB
      await client.query(`CREATE INDEX IF NOT EXISTS idx_${this.propertiesTable}_properties ON ${this.propertiesTable} USING GIN (properties jsonb_path_ops)`);
      await client.query(`CREATE INDEX IF NOT EXISTS idx_${this.contextTable}_context ON ${this.contextTable} USING GIN (context jsonb_path_ops)`);

      this.initialized = true;
      logger.info('PostgreSQL storage provider initialized');
    } catch (error) {
      logger.error('Error initializing PostgreSQL storage provider', { error });
      throw error;
    } finally {
      client.release();
    }
  }

  /**
   * Store an analytics event
   * @param event Analytics event to store
   */
  async storeEvent(event: AnalyticsEvent): Promise<void> {
    if (!this.initialized) {
      await this.initialize();
    }

    const client = await this.pool.connect();

    try {
      await client.query('BEGIN');

      // Insert event
      await client.query(
        `
        INSERT INTO ${this.eventsTable}
          (id, type, name, timestamp, user_id, session_id, source)
        VALUES
          ($1, $2, $3, $4, $5, $6, $7)
        `,
        [
          event.id,
          event.type,
          event.name,
          event.timestamp,
          event.userId,
          event.sessionId,
          event.source,
        ]
      );

      // Insert properties if present
      if (event.properties && Object.keys(event.properties).length > 0) {
        await client.query(
          `
          INSERT INTO ${this.propertiesTable}
            (event_id, properties)
          VALUES
            ($1, $2)
          `,
          [
            event.id,
            JSON.stringify(event.properties),
          ]
        );
      }

      // Insert context if present
      if (event.context && Object.keys(event.context).length > 0) {
        await client.query(
          `
          INSERT INTO ${this.contextTable}
            (event_id, context)
          VALUES
            ($1, $2)
          `,
          [
            event.id,
            JSON.stringify(event.context),
          ]
        );
      }

      await client.query('COMMIT');
    } catch (error) {
      await client.query('ROLLBACK');
      logger.error('Error storing analytics event', { eventId: event.id, error });
      throw error;
    } finally {
      client.release();
    }
  }

  /**
   * Query analytics events
   * @param query Query parameters
   * @returns Promise resolving to query results
   */
  async queryEvents(query: AnalyticsQuery): Promise<AnalyticsQueryResult> {
    if (!this.initialized) {
      await this.initialize();
    }

    const client = await this.pool.connect();

    try {
      // Build query conditions
      const conditions: string[] = [];
      const params: any[] = [];
      let paramIndex = 1;

      // Event types
      if (query.eventTypes && query.eventTypes.length > 0) {
        conditions.push(`e.type IN (${query.eventTypes.map(() => `$${paramIndex++}`).join(', ')})`);
        params.push(...query.eventTypes);
      }

      // Event names
      if (query.eventNames && query.eventNames.length > 0) {
        conditions.push(`e.name IN (${query.eventNames.map(() => `$${paramIndex++}`).join(', ')})`);
        params.push(...query.eventNames);
      }

      // User IDs
      if (query.userIds && query.userIds.length > 0) {
        conditions.push(`e.user_id IN (${query.userIds.map(() => `$${paramIndex++}`).join(', ')})`);
        params.push(...query.userIds);
      }

      // Session IDs
      if (query.sessionIds && query.sessionIds.length > 0) {
        conditions.push(`e.session_id IN (${query.sessionIds.map(() => `$${paramIndex++}`).join(', ')})`);
        params.push(...query.sessionIds);
      }

      // Time range
      if (query.startTime) {
        conditions.push(`e.timestamp >= $${paramIndex++}`);
        params.push(query.startTime);
      }

      if (query.endTime) {
        conditions.push(`e.timestamp <= $${paramIndex++}`);
        params.push(query.endTime);
      }

      // Property filters
      if (query.properties && Object.keys(query.properties).length > 0) {
        for (const [key, value] of Object.entries(query.properties)) {
          if (value === null) {
            conditions.push(`p.properties ? $${paramIndex++}`);
            params.push(key);
          } else {
            conditions.push(`p.properties->$${paramIndex++} @> $${paramIndex++}::jsonb`);
            params.push(key, JSON.stringify(value));
          }
        }
      }

      // Context filters
      if (query.context && Object.keys(query.context).length > 0) {
        for (const [key, value] of Object.entries(query.context)) {
          if (value === null) {
            conditions.push(`c.context ? $${paramIndex++}`);
            params.push(key);
          } else {
            conditions.push(`c.context->$${paramIndex++} @> $${paramIndex++}::jsonb`);
            params.push(key, JSON.stringify(value));
          }
        }
      }

      // Build WHERE clause
      const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';

      // Get total count
      const countQuery = `
        SELECT COUNT(e.id) as total
        FROM ${this.eventsTable} e
        LEFT JOIN ${this.propertiesTable} p ON e.id = p.event_id
        LEFT JOIN ${this.contextTable} c ON e.id = c.event_id
        ${whereClause}
      `;

      const countResult = await client.query(countQuery, params);
      const totalCount = parseInt(countResult.rows[0].total, 10);

      // Build sorting
      const sortBy = query.sortBy || 'timestamp';
      const sortDirection = query.sortDirection || 'desc';
      const sortField = (() => {
        if (sortBy.startsWith('properties.')) {
          return `p.properties->>'${sortBy.substring('properties.'.length)}'`;
        } else if (sortBy.startsWith('context.')) {
          return `c.context->>'${sortBy.substring('context.'.length)}'`;
        } else {
          return `e.${sortBy}`;
        }
      })();

      // Add pagination
      const limit = query.limit || 100;
      const offset = query.offset || 0;

      // Build full query
      const fullQuery = `
        SELECT
          e.*,
          p.properties,
          c.context
        FROM ${this.eventsTable} e
        LEFT JOIN ${this.propertiesTable} p ON e.id = p.event_id
        LEFT JOIN ${this.contextTable} c ON e.id = c.event_id
        ${whereClause}
        ORDER BY ${sortField} ${sortDirection}
        LIMIT $${paramIndex++} OFFSET $${paramIndex++}
      `;

      params.push(limit, offset);

      const result = await client.query(fullQuery, params);

      // Transform results
      const events: AnalyticsEvent[] = result.rows.map(row => ({
        id: row.id,
        type: row.type as EventType,
        name: row.name,
        timestamp: row.timestamp,
        userId: row.user_id,
        sessionId: row.session_id,
        source: row.source,
        properties: row.properties || {},
        context: row.context || {},
      }));

      return {
        events,
        totalCount,
        limit,
        offset,
      };
    } catch (error) {
      logger.error('Error querying analytics events', { error });
      throw error;
    } finally {
      client.release();
    }
  }

  /**
   * Get aggregated metrics
   * @param metric Metric to aggregate
   * @param dimensions Dimensions to group by
   * @param filters Filters to apply
   * @param timeframe Timeframe to query
   * @returns Promise resolving to aggregated metrics
   */
  async getMetrics(
    metric: string,
    dimensions: string[] = [],
    filters: Record<string, any> = {},
    timeframe: TimeFrame = { start: new Date(Date.now() - 86400000), end: new Date() }
  ): Promise<AggregatedMetrics> {
    if (!this.initialized) {
      await this.initialize();
    }

    const client = await this.pool.connect();

    try {
      // Generate dimension selections and group by clauses
      const dimensionSelections: string[] = [];
      const groupByClauses: string[] = [];

      dimensions.forEach((dimension, index) => {
        if (dimension.startsWith('properties.')) {
          const propName = dimension.substring('properties.'.length);
          dimensionSelections.push(`p.properties->>'${propName}' as "${dimension}"`);
          groupByClauses.push(`p.properties->>'${propName}'`);
        } else if (dimension.startsWith('context.')) {
          const contextName = dimension.substring('context.'.length);
          dimensionSelections.push(`c.context->>'${contextName}' as "${dimension}"`);
          groupByClauses.push(`c.context->>'${contextName}'`);
        } else {
          dimensionSelections.push(`e.${dimension} as "${dimension}"`);
          groupByClauses.push(`e.${dimension}`);
        }
      });

      // Build metric calculation
      let metricCalculation = '';
      if (metric === 'count') {
        metricCalculation = 'COUNT(*)';
      } else if (metric.startsWith('unique_')) {
        const field = metric.substring('unique_'.length);
        metricCalculation = `COUNT(DISTINCT e.${field})`;
      } else if (metric.startsWith('avg_') && metric.includes('properties.')) {
        const propName = metric.substring('avg_properties.'.length);
        metricCalculation = `AVG((p.properties->>'${propName}')::numeric)`;
      } else if (metric.startsWith('sum_') && metric.includes('properties.')) {
        const propName = metric.substring('sum_properties.'.length);
        metricCalculation = `SUM((p.properties->>'${propName}')::numeric)`;
      } else {
        throw new Error(`Unsupported metric: ${metric}`);
      }

      // Build conditions from filters and timeframe
      const conditions: string[] = [];
      const params: any[] = [];
      let paramIndex = 1;

      // Timeframe
      conditions.push(`e.timestamp >= $${paramIndex++}`);
      params.push(timeframe.start);

      conditions.push(`e.timestamp <= $${paramIndex++}`);
      params.push(timeframe.end);

      // Filters
      Object.entries(filters).forEach(([key, value]) => {
        if (key.startsWith('properties.')) {
          const propName = key.substring('properties.'.length);
          conditions.push(`p.properties->>'${propName}' = $${paramIndex++}`);
          params.push(value);
        } else if (key.startsWith('context.')) {
          const contextName = key.substring('context.'.length);
          conditions.push(`c.context->>'${contextName}' = $${paramIndex++}`);
          params.push(value);
        } else {
          conditions.push(`e.${key} = $${paramIndex++}`);
          params.push(value);
        }
      });

      // Build WHERE clause
      const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';

      // Build group by clause
      const groupBy = groupByClauses.length > 0 ? `GROUP BY ${groupByClauses.join(', ')}` : '';

      // Build the query
      const dimensionSelectClause = dimensionSelections.length > 0
        ? `${dimensionSelections.join(', ')}, `
        : '';

      const query = `
        SELECT
          ${dimensionSelectClause}
          ${metricCalculation} as value
        FROM ${this.eventsTable} e
        LEFT JOIN ${this.propertiesTable} p ON e.id = p.event_id
        LEFT JOIN ${this.contextTable} c ON e.id = c.event_id
        ${whereClause}
        ${groupBy}
        ORDER BY value DESC
      `;

      // Get total
      const totalQuery = `
        SELECT
          ${metricCalculation} as total
        FROM ${this.eventsTable} e
        LEFT JOIN ${this.propertiesTable} p ON e.id = p.event_id
        LEFT JOIN ${this.contextTable} c ON e.id = c.event_id
        ${whereClause}
      `;

      const result = await client.query(query, params);
      const totalResult = await client.query(totalQuery, params);

      // Transform results
      const groups = result.rows.map(row => {
        const dimensionValues: Record<string, any> = {};

        dimensions.forEach(dimension => {
          dimensionValues[dimension] = row[dimension];
        });

        return {
          dimensions: dimensionValues,
          value: parseFloat(row.value) || 0,
        };
      });

      return {
        metric,
        dimensions,
        groups,
        total: parseFloat(totalResult.rows[0].total) || 0,
      };
    } catch (error) {
      logger.error('Error getting metrics', { error, metric, dimensions });
      throw error;
    } finally {
      client.release();
    }
  }

  /**
   * Close the database connection pool
   */
  async close(): Promise<void> {
    await this.pool.end();
  }
}

export default PostgresStorageProvider;
