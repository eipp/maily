/**
 * Base query interface
 */
export interface Query {
  /**
   * Query type
   */
  readonly type: string;
}

/**
 * Result of a query execution
 */
export interface QueryResult<T = any> {
  /**
   * Whether the query was successful
   */
  success: boolean;

  /**
   * Result data
   */
  data?: T;

  /**
   * Error message if the query failed
   */
  error?: string;

  /**
   * Error code if the query failed
   */
  errorCode?: string;
}

/**
 * Query handler interface
 */
export interface QueryHandler<TQuery extends Query, TResult = any> {
  /**
   * Execute the query
   * @param query Query to execute
   */
  execute(query: TQuery): Promise<QueryResult<TResult>>;
}

/**
 * Query bus interface for dispatching queries
 */
export interface QueryBus {
  /**
   * Register a query handler
   * @param queryType Query type
   * @param handler Query handler
   */
  register<TQuery extends Query, TResult = any>(
    queryType: string,
    handler: QueryHandler<TQuery, TResult>
  ): void;

  /**
   * Execute a query
   * @param query Query to execute
   */
  execute<TQuery extends Query, TResult = any>(
    query: TQuery
  ): Promise<QueryResult<TResult>>;
}

/**
 * In-memory query bus implementation
 */
export class InMemoryQueryBus implements QueryBus {
  private handlers: Map<string, QueryHandler<any, any>> = new Map();

  /**
   * Register a query handler
   * @param queryType Query type
   * @param handler Query handler
   */
  register<TQuery extends Query, TResult = any>(
    queryType: string,
    handler: QueryHandler<TQuery, TResult>
  ): void {
    this.handlers.set(queryType, handler);
  }

  /**
   * Execute a query
   * @param query Query to execute
   */
  async execute<TQuery extends Query, TResult = any>(
    query: TQuery
  ): Promise<QueryResult<TResult>> {
    const handler = this.handlers.get(query.type);

    if (!handler) {
      return {
        success: false,
        error: `No handler registered for query type: ${query.type}`,
        errorCode: 'QUERY_HANDLER_NOT_FOUND',
      };
    }

    try {
      return await handler.execute(query);
    } catch (error: any) {
      return {
        success: false,
        error: error.message,
        errorCode: error.code || 'QUERY_EXECUTION_ERROR',
      };
    }
  }
}
