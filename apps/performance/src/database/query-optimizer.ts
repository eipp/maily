import { logger } from '../utils/logger';
import { PerformanceMetrics } from '../monitoring/metrics';

/**
 * Query optimization strategies
 */
export enum OptimizationStrategy {
  INDEX_SCAN = 'INDEX_SCAN',
  SEQUENTIAL_SCAN = 'SEQUENTIAL_SCAN',
  HASH_JOIN = 'HASH_JOIN',
  MERGE_JOIN = 'MERGE_JOIN',
  NESTED_LOOP = 'NESTED_LOOP',
  LIMIT = 'LIMIT',
  SORT = 'SORT',
  GROUP = 'GROUP',
  AGGREGATE = 'AGGREGATE',
}

/**
 * Query plan node
 */
export interface QueryPlanNode {
  id: string;
  parentId?: string;
  operation: string;
  table?: string;
  estimatedCost: number;
  estimatedRows: number;
  actualCost?: number;
  actualRows?: number;
  index?: string;
  filter?: string;
  children?: QueryPlanNode[];
}

/**
 * Query execution plan
 */
export interface QueryExecutionPlan {
  planId: string;
  query: string;
  timestamp: Date;
  duration: number;
  rootNode: QueryPlanNode;
  optimizationApplied?: OptimizationStrategy[];
}

/**
 * Query optimization configuration
 */
export interface QueryOptimizerConfig {
  maxQueryExecutionTime: number; // milliseconds
  slowQueryThreshold: number; // milliseconds
  enableAutomaticIndexing: boolean;
  optimizationStrategies: OptimizationStrategy[];
  cachingEnabled: boolean;
  cacheTTL: number; // seconds
  logSlowQueries: boolean;
  collectMetrics: boolean;
}

/**
 * Default configuration
 */
const DEFAULT_CONFIG: QueryOptimizerConfig = {
  maxQueryExecutionTime: 5000,
  slowQueryThreshold: 1000,
  enableAutomaticIndexing: true,
  optimizationStrategies: [
    OptimizationStrategy.INDEX_SCAN,
    OptimizationStrategy.HASH_JOIN,
    OptimizationStrategy.LIMIT,
  ],
  cachingEnabled: true,
  cacheTTL: 300, // 5 minutes
  logSlowQueries: true,
  collectMetrics: true,
};

/**
 * Query optimization result
 */
export interface QueryOptimizationResult {
  originalQuery: string;
  optimizedQuery: string;
  estimatedImprovement: number; // percentage
  appliedStrategies: OptimizationStrategy[];
  suggestedIndexes?: string[];
}

/**
 * Query optimizer for database performance optimization
 */
export class QueryOptimizer {
  private config: QueryOptimizerConfig;
  private queryHistory: Map<string, QueryExecutionPlan[]> = new Map();
  private indexSuggestions: Map<string, Set<string>> = new Map();
  private metrics: PerformanceMetrics;

  /**
   * Create a new query optimizer
   * @param config Configuration options
   * @param metrics Performance metrics tracker
   */
  constructor(
    config: Partial<QueryOptimizerConfig> = {},
    metrics?: PerformanceMetrics
  ) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.metrics = metrics || new PerformanceMetrics();
  }

  /**
   * Optimize a SQL query
   * @param query Original SQL query
   * @param params Query parameters
   * @returns Optimized query
   */
  public optimizeQuery(query: string, params: any[] = []): QueryOptimizationResult {
    const start = Date.now();
    logger.debug('Optimizing query', { query, params });

    // Generate query fingerprint for caching and history
    const queryFingerprint = this.generateQueryFingerprint(query, params);

    let optimizedQuery = query;
    const appliedStrategies: OptimizationStrategy[] = [];
    let estimatedImprovement = 0;

    // Apply optimization strategies based on configuration
    if (this.config.optimizationStrategies.includes(OptimizationStrategy.INDEX_SCAN)) {
      const indexOptimization = this.applyIndexScanOptimization(query);
      optimizedQuery = indexOptimization.query;
      estimatedImprovement += indexOptimization.improvement;

      if (indexOptimization.applied) {
        appliedStrategies.push(OptimizationStrategy.INDEX_SCAN);
      }
    }

    if (this.config.optimizationStrategies.includes(OptimizationStrategy.LIMIT)) {
      const limitOptimization = this.applyLimitOptimization(optimizedQuery);
      optimizedQuery = limitOptimization.query;
      estimatedImprovement += limitOptimization.improvement;

      if (limitOptimization.applied) {
        appliedStrategies.push(OptimizationStrategy.LIMIT);
      }
    }

    // Generate suggested indexes based on query analysis
    const suggestedIndexes = this.generateIndexSuggestions(query);

    // Record optimization time
    const duration = Date.now() - start;

    if (this.config.collectMetrics) {
      this.metrics.recordQueryOptimization(duration, estimatedImprovement);
    }

    logger.debug('Query optimization completed', {
      queryFingerprint,
      originalQuery: query,
      optimizedQuery,
      appliedStrategies,
      estimatedImprovement,
      duration,
    });

    return {
      originalQuery: query,
      optimizedQuery,
      estimatedImprovement,
      appliedStrategies,
      suggestedIndexes,
    };
  }

  /**
   * Record a query execution plan
   * @param plan Query execution plan
   */
  public recordQueryPlan(plan: QueryExecutionPlan): void {
    const queryFingerprint = this.generateQueryFingerprint(plan.query, []);

    // Store in query history
    if (!this.queryHistory.has(queryFingerprint)) {
      this.queryHistory.set(queryFingerprint, []);
    }

    const history = this.queryHistory.get(queryFingerprint)!;
    history.push(plan);

    // Keep history within reasonable limits
    if (history.length > 100) {
      history.shift();
    }

    // Log slow queries
    if (this.config.logSlowQueries && plan.duration > this.config.slowQueryThreshold) {
      logger.warn('Slow query detected', {
        query: plan.query,
        duration: plan.duration,
        threshold: this.config.slowQueryThreshold,
      });
    }

    // Record metrics
    if (this.config.collectMetrics) {
      this.metrics.recordQueryExecution(plan.duration, plan.rootNode.estimatedRows);
    }

    // Analyze for potential optimizations
    this.analyzeQueryPlan(plan);
  }

  /**
   * Get optimization suggestions for a table
   * @param tableName Table name
   * @returns Suggested indexes
   */
  public getSuggestedIndexes(tableName: string): string[] {
    if (!this.indexSuggestions.has(tableName)) {
      return [];
    }

    return Array.from(this.indexSuggestions.get(tableName)!);
  }

  /**
   * Get slow queries
   * @param limit Maximum number of queries to return
   * @returns Slow queries
   */
  public getSlowQueries(limit: number = 10): { query: string; avgDuration: number }[] {
    const queryStats: { query: string; avgDuration: number }[] = [];

    for (const [fingerprint, plans] of this.queryHistory.entries()) {
      if (plans.length === 0) continue;

      const avgDuration = plans.reduce((sum, plan) => sum + plan.duration, 0) / plans.length;

      if (avgDuration > this.config.slowQueryThreshold) {
        queryStats.push({
          query: plans[0].query,
          avgDuration,
        });
      }
    }

    // Sort by average duration (descending)
    queryStats.sort((a, b) => b.avgDuration - a.avgDuration);

    return queryStats.slice(0, limit);
  }

  /**
   * Generate a fingerprint for a query
   * @param query SQL query
   * @param params Query parameters
   * @returns Query fingerprint
   */
  private generateQueryFingerprint(query: string, params: any[]): string {
    // Normalize query by removing whitespace and converting to lowercase
    const normalizedQuery = query
      .replace(/\s+/g, ' ')
      .trim()
      .toLowerCase();

    // Replace literal values with placeholders
    const fingerprintQuery = normalizedQuery
      .replace(/'\w+'|"\w+"/g, '?') // Replace string literals
      .replace(/\b\d+\b/g, '?'); // Replace numeric literals

    return fingerprintQuery;
  }

  /**
   * Apply index scan optimization
   * @param query SQL query
   * @returns Optimized query
   */
  private applyIndexScanOptimization(query: string): {
    query: string;
    applied: boolean;
    improvement: number;
  } {
    // Check if the query contains a WHERE clause without an indexed column
    const whereClauseMatch = query.match(/WHERE\s+(\w+)\s*=/i);
    if (!whereClauseMatch) {
      return { query, applied: false, improvement: 0 };
    }

    // This is a simplified example - in a real implementation,
    // we would check available indexes and schema information

    // For this example, just assume we're suggesting an index
    const column = whereClauseMatch[1];
    const tableName = this.extractTableName(query);

    if (tableName && column) {
      // Add to index suggestions
      if (!this.indexSuggestions.has(tableName)) {
        this.indexSuggestions.set(tableName, new Set());
      }

      this.indexSuggestions.get(tableName)!.add(column);
    }

    // For now, return the original query since we can't modify it
    // without database schema information
    return { query, applied: false, improvement: 0 };
  }

  /**
   * Apply limit optimization
   * @param query SQL query
   * @returns Optimized query
   */
  private applyLimitOptimization(query: string): {
    query: string;
    applied: boolean;
    improvement: number;
  } {
    // Check if query is a SELECT without a LIMIT clause
    if (
      query.trim().toUpperCase().startsWith('SELECT') &&
      !query.toUpperCase().includes('LIMIT ')
    ) {
      // Add a reasonable LIMIT clause for potentially unbounded queries
      const orderByMatch = query.match(/ORDER\s+BY\s.+$/i);

      if (orderByMatch) {
        // Insert LIMIT before the ORDER BY
        const newQuery =
          query.substring(0, orderByMatch.index) +
          ' LIMIT 1000 ' +
          query.substring(orderByMatch.index);

        return {
          query: newQuery,
          applied: true,
          improvement: 20, // Estimated 20% improvement by limiting results
        };
      } else {
        // Append LIMIT at the end
        return {
          query: `${query} LIMIT 1000`,
          applied: true,
          improvement: 20,
        };
      }
    }

    return { query, applied: false, improvement: 0 };
  }

  /**
   * Extract table name from a query
   * @param query SQL query
   * @returns Table name
   */
  private extractTableName(query: string): string | null {
    // Simple regex to extract table name from FROM clause
    const fromClauseMatch = query.match(/FROM\s+(\w+)/i);

    if (fromClauseMatch && fromClauseMatch[1]) {
      return fromClauseMatch[1];
    }

    return null;
  }

  /**
   * Generate index suggestions for a query
   * @param query SQL query
   * @returns Suggested indexes
   */
  private generateIndexSuggestions(query: string): string[] {
    const tableName = this.extractTableName(query);

    if (!tableName) {
      return [];
    }

    // Find potential columns for indexing in WHERE, JOIN, and ORDER BY clauses
    const whereColumns = this.extractColumnsFromClause(query, 'WHERE');
    const joinColumns = this.extractColumnsFromClause(query, 'JOIN');
    const orderByColumns = this.extractColumnsFromClause(query, 'ORDER BY');

    const allColumns = [...whereColumns, ...joinColumns, ...orderByColumns];

    // Generate index suggestions
    const suggestions: string[] = [];

    for (const column of allColumns) {
      suggestions.push(`CREATE INDEX idx_${tableName}_${column} ON ${tableName}(${column});`);
    }

    return suggestions;
  }

  /**
   * Extract columns from a specific clause
   * @param query SQL query
   * @param clause Clause name (WHERE, JOIN, ORDER BY)
   * @returns Columns
   */
  private extractColumnsFromClause(query: string, clause: string): string[] {
    const clausePattern = new RegExp(`${clause}\\s+(.+?)(?:ORDER BY|GROUP BY|LIMIT|$)`, 'i');
    const match = query.match(clausePattern);

    if (!match || !match[1]) {
      return [];
    }

    const clauseContent = match[1];
    const columnPattern = /(\w+)\s*(?:=|>|<|>=|<=|LIKE|IN|IS|ORDER BY|ASC|DESC)/g;
    const columns: string[] = [];
    let columnMatch;

    while ((columnMatch = columnPattern.exec(clauseContent)) !== null) {
      columns.push(columnMatch[1]);
    }

    return columns;
  }

  /**
   * Analyze a query execution plan for optimization opportunities
   * @param plan Query execution plan
   */
  private analyzeQueryPlan(plan: QueryExecutionPlan): void {
    // Check for sequential scans on large tables
    this.detectSequentialScans(plan.rootNode);

    // Check for missing indexes
    this.detectMissingIndexes(plan.rootNode);

    // Check for inefficient joins
    this.detectInefficientJoins(plan.rootNode);
  }

  /**
   * Detect sequential scans in a query plan
   * @param node Query plan node
   */
  private detectSequentialScans(node: QueryPlanNode): void {
    // Check if this node is a sequential scan
    if (
      node.operation.includes('Seq Scan') ||
      node.operation.includes('Sequential Scan')
    ) {
      const tableName = node.table;

      if (tableName && node.estimatedRows > 1000) {
        logger.warn('Sequential scan detected on large table', {
          table: tableName,
          estimatedRows: node.estimatedRows,
          nodeId: node.id,
        });

        // Generate suggestions based on filters
        if (node.filter) {
          const columnMatches = node.filter.match(/(\w+)\s*(?:=|>|<|>=|<=)/g);

          if (columnMatches && columnMatches.length > 0) {
            if (!this.indexSuggestions.has(tableName)) {
              this.indexSuggestions.set(tableName, new Set());
            }

            for (const columnMatch of columnMatches) {
              const column = columnMatch.trim().split(/\s+/)[0];
              this.indexSuggestions.get(tableName)!.add(column);
            }
          }
        }
      }
    }

    // Recursively check children
    if (node.children) {
      for (const child of node.children) {
        this.detectSequentialScans(child);
      }
    }
  }

  /**
   * Detect missing indexes in a query plan
   * @param node Query plan node
   */
  private detectMissingIndexes(node: QueryPlanNode): void {
    // Look for filter operations without index scans
    if (node.filter && (!node.operation.includes('Index') || node.operation.includes('Filter'))) {
      const tableName = node.table;

      if (tableName) {
        const columnMatches = node.filter.match(/(\w+)\s*(?:=|>|<|>=|<=)/g);

        if (columnMatches && columnMatches.length > 0) {
          if (!this.indexSuggestions.has(tableName)) {
            this.indexSuggestions.set(tableName, new Set());
          }

          for (const columnMatch of columnMatches) {
            const column = columnMatch.trim().split(/\s+/)[0];
            this.indexSuggestions.get(tableName)!.add(column);
          }
        }
      }
    }

    // Recursively check children
    if (node.children) {
      for (const child of node.children) {
        this.detectMissingIndexes(child);
      }
    }
  }

  /**
   * Detect inefficient joins in a query plan
   * @param node Query plan node
   */
  private detectInefficientJoins(node: QueryPlanNode): void {
    // Look for nested loop joins with high row counts
    if (
      (node.operation.includes('Nested Loop') || node.operation.includes('Nested Join')) &&
      node.estimatedRows > 1000
    ) {
      logger.warn('Inefficient nested loop join detected', {
        nodeId: node.id,
        estimatedRows: node.estimatedRows,
        estimatedCost: node.estimatedCost,
      });

      // Suggest indexes for join columns if we can extract them
      // This would require more detailed analysis of the query plan
    }

    // Recursively check children
    if (node.children) {
      for (const child of node.children) {
        this.detectInefficientJoins(child);
      }
    }
  }
}
