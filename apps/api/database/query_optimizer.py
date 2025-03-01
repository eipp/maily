"""
Database query optimizer for SQLAlchemy.
Provides optimized query patterns and performance enhancements.
"""
from typing import List, Dict, Any, Optional, Type, TypeVar, Generic, Union
from sqlalchemy import Column, Table, func, text, select, inspect
from sqlalchemy.orm import Query, Session, joinedload, selectinload, contains_eager
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql import Select
import time
import structlog
from functools import wraps

logger = structlog.get_logger(__name__)

T = TypeVar('T')

class QueryOptimizer:
    """Optimizes database queries for performance and efficiency.

    Provides methods for:
    - Selecting only needed columns
    - Adding proper indexes
    - Implementing eager loading strategies
    - Query timing and logging
    """

    def __init__(self, db: Session):
        """Initialize optimizer with database session.

        Args:
            db: SQLAlchemy session
        """
        self.db = db
        self.query_count = 0
        self.slow_query_threshold_ms = 500  # Log queries slower than this

    def select_columns(
        self,
        model: Type[DeclarativeMeta],
        columns: List[str]
    ) -> Query:
        """Create query that selects only specific columns.

        Args:
            model: SQLAlchemy model
            columns: List of column names to select

        Returns:
            Optimized query
        """
        # Get the actual column objects
        model_columns = [getattr(model, col) for col in columns]

        # Create a query with only selected columns
        return self.db.query(*model_columns)

    def get_by_id(
        self,
        model: Type[DeclarativeMeta],
        id_value: Any,
        columns: Optional[List[str]] = None
    ) -> Optional[Any]:
        """Get model instance by ID with optional column selection.

        Args:
            model: SQLAlchemy model
            id_value: ID value to query for
            columns: Optional list of columns to select

        Returns:
            Model instance or None if not found
        """
        if columns:
            selected_columns = [getattr(model, col) for col in columns]
            return self.db.query(*selected_columns).filter(model.id == id_value).first()
        else:
            return self.db.query(model).filter(model.id == id_value).first()

    def with_eager_loading(
        self,
        query: Query,
        relationships: Dict[str, Dict[str, Any]]
    ) -> Query:
        """Add eager loading strategies for relationships.

        Args:
            query: Base query
            relationships: Dict mapping relationship name to loading options
                Format: {"relation_name": {"strategy": "joined|selectin|subquery", "nested": {...}}}

        Returns:
            Query with eager loading strategies
        """
        for relation, options in relationships.items():
            strategy = options.get("strategy", "selectin")
            nested = options.get("nested", {})

            if strategy == "joined":
                relation_obj = joinedload(relation)
            elif strategy == "selectin":
                relation_obj = selectinload(relation)
            else:  # subquery is the default fallback
                relation_obj = joinedload(relation).subqueryload()

            # Apply nested eager loading if specified
            if nested:
                for nested_relation, nested_options in nested.items():
                    nested_strategy = nested_options.get("strategy", "selectin")

                    if nested_strategy == "joined":
                        relation_obj = relation_obj.joinedload(nested_relation)
                    elif nested_strategy == "selectin":
                        relation_obj = relation_obj.selectinload(nested_relation)
                    else:
                        relation_obj = relation_obj.subqueryload(nested_relation)

            query = query.options(relation_obj)

        return query

    def paginate(
        self,
        query: Query,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """Paginate query results.

        Args:
            query: Base query
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Dict with items and pagination metadata
        """
        # Ensure valid pagination parameters
        page = max(1, page)
        page_size = max(1, min(100, page_size))  # Limit maximum page size

        # Get total count
        total_items = query.count()

        # Calculate total pages
        total_pages = max(1, (total_items + page_size - 1) // page_size)

        # Get paginated items
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        # Create pagination metadata
        return {
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "total_items": total_items,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }
        }

    def add_search_filters(
        self,
        query: Query,
        model: Type[DeclarativeMeta],
        search_term: str,
        search_columns: List[str]
    ) -> Query:
        """Add search filters to query.

        Args:
            query: Base query
            model: SQLAlchemy model
            search_term: Search term
            search_columns: List of column names to search in

        Returns:
            Query with search filters
        """
        if not search_term or not search_columns:
            return query

        # Create filters for each column
        filters = []
        for column_name in search_columns:
            column = getattr(model, column_name)
            filters.append(column.ilike(f"%{search_term}%"))

        # Combine filters with OR
        from sqlalchemy import or_
        return query.filter(or_(*filters))

    def timed_query(self, query: Query) -> Any:
        """Execute query with timing and logging.

        Args:
            query: Query to execute

        Returns:
            Query results
        """
        # Increment query counter
        self.query_count += 1

        # Generate query ID for logging
        from uuid import uuid4
        query_id = str(uuid4())[:8]

        # Time the query execution
        start_time = time.time()
        result = query.all()
        duration_ms = (time.time() - start_time) * 1000

        # Log query performance
        log = logger.debug if duration_ms < self.slow_query_threshold_ms else logger.warning

        log("Database query executed",
            query_id=query_id,
            duration_ms=round(duration_ms, 2),
            result_count=len(result),
            query_count=self.query_count,
            slow=duration_ms >= self.slow_query_threshold_ms)

        return result

    def analyze_query(self, query: Query) -> Dict[str, Any]:
        """Analyze query for performance insights.

        Args:
            query: Query to analyze

        Returns:
            Analysis with execution plan and stats
        """
        try:
            # Get compiled SQL
            compiled_query = query.statement.compile(
                dialect=self.db.bind.dialect,
                compile_kwargs={"literal_binds": True}
            )

            # Execute EXPLAIN ANALYZE
            explain_query = f"EXPLAIN ANALYZE {compiled_query}"
            result = self.db.execute(text(explain_query)).fetchall()

            # Parse execution plan
            plan_lines = [row[0] for row in result]

            # Extract key metrics (estimation)
            planning_time = None
            execution_time = None

            for line in plan_lines:
                if "Planning Time" in line:
                    planning_time = float(line.split(":")[1].strip("ms"))
                elif "Execution Time" in line:
                    execution_time = float(line.split(":")[1].strip("ms"))

            return {
                "sql": str(compiled_query),
                "execution_plan": plan_lines,
                "stats": {
                    "planning_time_ms": planning_time,
                    "execution_time_ms": execution_time,
                    "total_time_ms": (planning_time or 0) + (execution_time or 0)
                }
            }
        except Exception as e:
            logger.warning("Query analysis failed", error=str(e))
            return {
                "sql": str(query),
                "error": str(e),
                "error_type": e.__class__.__name__
            }

# Decorator for timing query execution
def timed_operation(operation_name: str = None):
    """Decorator for timing and logging operations.

    Args:
        operation_name: Optional name for the operation

    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate operation ID
            from uuid import uuid4
            operation_id = str(uuid4())[:8]
            op_name = operation_name or func.__name__

            # Time the operation
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                success = True
            except Exception as e:
                success = False
                logger.error(f"Operation failed: {op_name}",
                            operation_id=operation_id,
                            error=str(e),
                            error_type=e.__class__.__name__)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000

                # Log operation performance
                log_level = logger.debug if duration_ms < 500 else logger.info
                log_level(f"Operation completed: {op_name}",
                         operation_id=operation_id,
                         duration_ms=round(duration_ms, 2),
                         success=success)

            return result
        return wrapper
    return decorator

# Query optimization context
class OptimizedQueryContext:
    """Context manager for optimized queries.

    Attributes:
        db: Database session
        optimizer: Query optimizer
    """

    def __init__(self, db: Session):
        """Initialize context.

        Args:
            db: SQLAlchemy session
        """
        self.db = db
        self.optimizer = QueryOptimizer(db)
        self.start_time = None
        self.query_count_start = 0

    def __enter__(self):
        """Enter context with timing.

        Returns:
            Query optimizer
        """
        self.start_time = time.time()
        self.query_count_start = self.optimizer.query_count
        return self.optimizer

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context with timing and logging.

        Args:
            exc_type: Exception type if raised
            exc_val: Exception value if raised
            exc_tb: Exception traceback if raised
        """
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            queries_executed = self.optimizer.query_count - self.query_count_start

            logger.info("Query context completed",
                       duration_ms=round(duration_ms, 2),
                       queries_executed=queries_executed,
                       avg_query_ms=round(duration_ms / max(1, queries_executed), 2),
                       success=exc_type is None)

# Helper function to get DB session with optimizer
def get_optimized_db(db: Session) -> OptimizedQueryContext:
    """Get optimized database context.

    Args:
        db: SQLAlchemy session

    Returns:
        Optimized query context
    """
    return OptimizedQueryContext(db)

# Usage example:
# with get_optimized_db(db) as query_optimizer:
#     results = query_optimizer.timed_query(
#         query_optimizer.with_eager_loading(
#             query_optimizer.add_search_filters(
#                 db.query(User),
#                 User,
#                 search_term,
#                 ["username", "email"]
#             ),
#             {"campaigns": {"strategy": "selectin"}}
#         )
#     )
