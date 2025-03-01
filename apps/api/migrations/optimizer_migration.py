"""
Database optimization migration utilities.
"""
from typing import List, Dict, Any, Optional, Union, Set
from sqlalchemy import Column, Index, MetaData, Table, create_engine, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.sql import select, text
import structlog
import time

from ..logging.logging_config import get_logger
from ..config.settings import get_settings

logger = get_logger("maily.migrations.optimizer")

class DatabaseOptimizer:
    """Database optimization utilities for migrations."""

    def __init__(self, engine: Optional[Engine] = None):
        """Initialize database optimizer.

        Args:
            engine: SQLAlchemy engine or None to create from settings
        """
        if engine is None:
            settings = get_settings()
            self.engine = create_engine(settings.DATABASE_URL)
        else:
            self.engine = engine

        self.inspector = inspect(self.engine)
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine)

    def analyze_table_indexes(self, table_name: str) -> Dict[str, Any]:
        """Analyze indexes for a table and recommend optimizations.

        Args:
            table_name: Name of table to analyze

        Returns:
            Dictionary with analysis results
        """
        if table_name not in self.metadata.tables:
            return {"error": f"Table {table_name} not found"}

        table = self.metadata.tables[table_name]
        existing_indexes = self.inspector.get_indexes(table_name)

        # Collect column statistics
        column_stats = self._get_column_statistics(table_name)

        # Check for missing indexes on foreign keys
        fk_columns = set()
        for fk in self.inspector.get_foreign_keys(table_name):
            for col in fk['constrained_columns']:
                fk_columns.add(col)

        # Check existing indexes
        indexed_columns = set()
        for idx in existing_indexes:
            for col in idx['column_names']:
                indexed_columns.add(col)

        # Find foreign keys without indexes
        unindexed_fks = fk_columns - indexed_columns

        # Analyze existing indexes
        duplicate_indexes = self._find_duplicate_indexes(existing_indexes)
        unused_indexes = self._find_unused_indexes(table_name)

        # Find high cardinality columns that might benefit from indexes
        high_cardinality_columns = []
        for col, stats in column_stats.items():
            # Skip columns that are already indexed
            if col in indexed_columns:
                continue

            # Skip columns with low cardinality (e.g., boolean, status)
            if stats.get('cardinality_ratio', 0) > 0.1:  # More than 10% unique values
                high_cardinality_columns.append({
                    'column': col,
                    'cardinality_ratio': stats.get('cardinality_ratio', 0),
                    'null_ratio': stats.get('null_ratio', 0)
                })

        # Recommend composite indexes for query patterns
        query_patterns = self._analyze_query_patterns(table_name)
        recommended_composites = []

        for pattern in query_patterns:
            if len(pattern['columns']) >= 2:
                # Check if these columns are already covered by an index
                if not self._has_covering_index(existing_indexes, pattern['columns']):
                    recommended_composites.append({
                        'columns': pattern['columns'],
                        'frequency': pattern['frequency'],
                        'suggested_name': f"idx_{table_name}_{'_'.join(pattern['columns'])}"
                    })

        # Generate results
        return {
            'table_name': table_name,
            'existing_indexes': existing_indexes,
            'column_stats': column_stats,
            'unindexed_foreign_keys': list(unindexed_fks),
            'duplicate_indexes': duplicate_indexes,
            'unused_indexes': unused_indexes,
            'high_cardinality_columns': high_cardinality_columns,
            'recommended_composite_indexes': recommended_composites,
            'recommendations': self._generate_recommendations(
                table_name,
                unindexed_fks,
                duplicate_indexes,
                unused_indexes,
                high_cardinality_columns,
                recommended_composites
            )
        }

    def _get_column_statistics(self, table_name: str) -> Dict[str, Dict[str, Any]]:
        """Get statistics for columns in a table.

        Args:
            table_name: Name of table

        Returns:
            Dictionary of column statistics
        """
        try:
            # Get column info
            columns = self.inspector.get_columns(table_name)
            result = {}

            # Get row count (approximate)
            with self.engine.connect() as conn:
                row_count_query = text(f"SELECT COUNT(*) FROM {table_name}")
                row_count = conn.execute(row_count_query).scalar() or 0

                # Skip detailed analysis for empty tables
                if row_count == 0:
                    return {col['name']: {
                        'type': str(col['type']),
                        'nullable': col.get('nullable', True),
                        'row_count': 0,
                        'cardinality': 0,
                        'cardinality_ratio': 0,
                        'null_count': 0,
                        'null_ratio': 0
                    } for col in columns}

                # For each column, get cardinality and null count
                for col in columns:
                    col_name = col['name']

                    # Get distinct count (cardinality)
                    cardinality_query = text(f"SELECT COUNT(DISTINCT {col_name}) FROM {table_name}")
                    cardinality = conn.execute(cardinality_query).scalar() or 0

                    # Get null count
                    null_query = text(f"SELECT COUNT(*) FROM {table_name} WHERE {col_name} IS NULL")
                    null_count = conn.execute(null_query).scalar() or 0

                    result[col_name] = {
                        'type': str(col['type']),
                        'nullable': col.get('nullable', True),
                        'row_count': row_count,
                        'cardinality': cardinality,
                        'cardinality_ratio': cardinality / row_count if row_count > 0 else 0,
                        'null_count': null_count,
                        'null_ratio': null_count / row_count if row_count > 0 else 0
                    }

            return result
        except Exception as e:
            logger.error(
                "Error getting column statistics",
                table=table_name,
                error=str(e),
                error_type=e.__class__.__name__
            )
            return {}

    def _find_duplicate_indexes(self, indexes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find duplicate indexes in a list of indexes.

        Args:
            indexes: List of index dictionaries

        Returns:
            List of duplicate indexes
        """
        # Group indexes by columns
        index_map = {}
        duplicates = []

        for idx in indexes:
            # Skip primary key
            if idx.get('name') == 'PRIMARY' or idx.get('primary_key', False):
                continue

            # Create a hashable representation of columns
            cols_tuple = tuple(sorted(idx['column_names']))

            if cols_tuple in index_map:
                # Found a duplicate
                duplicates.append({
                    'columns': idx['column_names'],
                    'indexes': [index_map[cols_tuple]['name'], idx['name']]
                })
            else:
                index_map[cols_tuple] = idx

        return duplicates

    def _find_unused_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Find unused indexes for a table.

        Args:
            table_name: Name of table

        Returns:
            List of unused indexes
        """
        try:
            with self.engine.connect() as conn:
                # Check if we can access index usage stats
                try:
                    # For PostgreSQL
                    if 'postgresql' in self.engine.name:
                        query = text("""
                        SELECT
                            indexrelname as index_name,
                            idx_scan as usage_count
                        FROM
                            pg_stat_user_indexes
                        WHERE
                            schemaname = 'public' AND
                            relname = :table_name AND
                            idx_scan = 0 AND
                            indexrelname NOT LIKE '%_pkey'
                        """)
                        result = conn.execute(query, {'table_name': table_name}).fetchall()
                        return [{'name': row.index_name, 'usage_count': row.usage_count} for row in result]

                    # For MySQL
                    elif 'mysql' in self.engine.name:
                        query = text("""
                        SELECT
                            index_name,
                            stat_value as usage_count
                        FROM
                            performance_schema.table_io_waits_summary_by_index_usage
                        WHERE
                            object_schema = DATABASE() AND
                            object_name = :table_name AND
                            stat_value = 0 AND
                            index_name IS NOT NULL AND
                            index_name != 'PRIMARY'
                        """)
                        result = conn.execute(query, {'table_name': table_name}).fetchall()
                        return [{'name': row.index_name, 'usage_count': row.usage_count} for row in result]

                except Exception:
                    # Fall back to a best-effort approach if we can't get usage stats
                    pass

            # If we can't access index usage stats, return empty list
            return []

        except Exception as e:
            logger.error(
                "Error finding unused indexes",
                table=table_name,
                error=str(e),
                error_type=e.__class__.__name__
            )
            return []

    def _analyze_query_patterns(self, table_name: str) -> List[Dict[str, Any]]:
        """Analyze query patterns for a table.

        Args:
            table_name: Name of table

        Returns:
            List of query pattern dictionaries
        """
        # This is a placeholder that would normally analyze query logs
        # to find common query patterns
        #
        # In a real implementation, this would:
        # 1. Analyze slow query logs
        # 2. Look at application query patterns
        # 3. Use a query analyzer tool
        #
        # For now, we'll return an empty list
        return []

    def _has_covering_index(self, indexes: List[Dict[str, Any]], columns: List[str]) -> bool:
        """Check if a set of columns is covered by an existing index.

        Args:
            indexes: List of index dictionaries
            columns: List of column names

        Returns:
            True if columns are covered by an index
        """
        # Convert to sets for easier comparison
        columns_set = set(columns)

        for idx in indexes:
            idx_columns = set(idx['column_names'])

            # Check if all target columns are in this index
            # Note: Order matters for indexes, but this is a simplification
            if columns_set.issubset(idx_columns):
                return True

        return False

    def _generate_recommendations(
        self,
        table_name: str,
        unindexed_fks: Set[str],
        duplicate_indexes: List[Dict[str, Any]],
        unused_indexes: List[Dict[str, Any]],
        high_cardinality_columns: List[Dict[str, Any]],
        recommended_composites: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on analysis.

        Args:
            table_name: Name of table
            unindexed_fks: Set of foreign key columns without indexes
            duplicate_indexes: List of duplicate indexes
            unused_indexes: List of unused indexes
            high_cardinality_columns: List of high cardinality columns
            recommended_composites: List of recommended composite indexes

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Add foreign key indexes
        for fk in unindexed_fks:
            recommendations.append(
                f"CREATE INDEX idx_{table_name}_{fk} ON {table_name} ({fk});"
            )

        # Remove duplicate indexes
        for dup in duplicate_indexes:
            recommendations.append(
                f"-- Consider dropping one of these duplicate indexes on {', '.join(dup['columns'])}:"
            )
            for idx_name in dup['indexes']:
                recommendations.append(
                    f"-- DROP INDEX {idx_name} ON {table_name};"
                )

        # Remove unused indexes
        for unused in unused_indexes:
            recommendations.append(
                f"-- Consider dropping unused index {unused['name']} if it's not needed for constraints:"
            )
            recommendations.append(
                f"-- DROP INDEX {unused['name']} ON {table_name};"
            )

        # Add indexes for high cardinality columns
        for col in high_cardinality_columns:
            if col['cardinality_ratio'] > 0.5 and col['null_ratio'] < 0.5:
                recommendations.append(
                    f"CREATE INDEX idx_{table_name}_{col['column']} ON {table_name} ({col['column']});"
                )

        # Add composite indexes
        for comp in recommended_composites:
            recommendations.append(
                f"CREATE INDEX {comp['suggested_name']} ON {table_name} ({', '.join(comp['columns'])});"
            )

        return recommendations

    def execute_optimization(self, sql: str) -> Dict[str, Any]:
        """Execute an optimization SQL statement.

        Args:
            sql: SQL statement to execute

        Returns:
            Result dictionary
        """
        try:
            start_time = time.time()

            with self.engine.connect() as conn:
                result = conn.execute(text(sql))
                conn.commit()

            duration = time.time() - start_time

            return {
                'status': 'success',
                'duration_seconds': duration,
                'rowcount': result.rowcount if hasattr(result, 'rowcount') else None,
                'sql': sql
            }
        except Exception as e:
            logger.error(
                "Error executing optimization",
                sql=sql,
                error=str(e),
                error_type=e.__class__.__name__
            )
            return {
                'status': 'error',
                'error': str(e),
                'error_type': e.__class__.__name__,
                'sql': sql
            }

    def optimize_table(self, table_name: str) -> Dict[str, Any]:
        """Run database-specific optimization for a table.

        Args:
            table_name: Name of table to optimize

        Returns:
            Result dictionary
        """
        try:
            start_time = time.time()

            with self.engine.connect() as conn:
                if 'mysql' in self.engine.name:
                    # MySQL/MariaDB optimization
                    sql = f"OPTIMIZE TABLE {table_name}"
                    result = conn.execute(text(sql))
                elif 'postgresql' in self.engine.name:
                    # PostgreSQL optimization
                    sql = f"VACUUM ANALYZE {table_name}"
                    result = conn.execute(text(sql))
                else:
                    return {
                        'status': 'error',
                        'error': f"Unsupported database engine: {self.engine.name}",
                        'table': table_name
                    }

                conn.commit()

            duration = time.time() - start_time

            return {
                'status': 'success',
                'table': table_name,
                'duration_seconds': duration,
                'engine': self.engine.name
            }
        except Exception as e:
            logger.error(
                "Error optimizing table",
                table=table_name,
                error=str(e),
                error_type=e.__class__.__name__
            )
            return {
                'status': 'error',
                'table': table_name,
                'error': str(e),
                'error_type': e.__class__.__name__
            }

    def analyze_database(self) -> Dict[str, Any]:
        """Analyze entire database and generate optimization recommendations.

        Returns:
            Analysis results
        """
        start_time = time.time()
        results = {}

        # Get all tables
        tables = self.inspector.get_table_names()

        # Analyze each table
        for table_name in tables:
            results[table_name] = self.analyze_table_indexes(table_name)

        duration = time.time() - start_time

        return {
            'tables_analyzed': len(tables),
            'duration_seconds': duration,
            'results': results
        }

    def generate_schema_optimization_script(self) -> Dict[str, Any]:
        """Generate a comprehensive optimization script for the entire database.

        Returns:
            Dictionary with optimization script
        """
        analysis = self.analyze_database()
        recommendations = []

        for table, result in analysis['results'].items():
            if 'recommendations' in result:
                table_recs = result['recommendations']
                if table_recs:
                    recommendations.append(f"\n-- Recommendations for table {table}")
                    recommendations.extend(table_recs)

        return {
            'schema_optimization_script': '\n'.join(recommendations),
            'tables_analyzed': analysis['tables_analyzed'],
            'tables_with_recommendations': sum(1 for r in analysis['results'].values() if r.get('recommendations', []))
        }

# CLI function for running the optimizer
def run_optimizer_cli():
    """Run the database optimizer from command line."""
    import argparse

    parser = argparse.ArgumentParser(description='Database optimizer')
    parser.add_argument('--table', help='Table to analyze')
    parser.add_argument('--analyze', action='store_true', help='Analyze database')
    parser.add_argument('--optimize', action='store_true', help='Optimize table')
    parser.add_argument('--script', action='store_true', help='Generate optimization script')
    parser.add_argument('--execute', help='Execute SQL')

    args = parser.parse_args()

    # Initialize optimizer
    optimizer = DatabaseOptimizer()

    if args.analyze and args.table:
        # Analyze specific table
        result = optimizer.analyze_table_indexes(args.table)
        import json
        print(json.dumps(result, indent=2))
    elif args.analyze:
        # Analyze entire database
        result = optimizer.analyze_database()
        import json
        print(json.dumps(result, indent=2))
    elif args.optimize and args.table:
        # Optimize specific table
        result = optimizer.optimize_table(args.table)
        import json
        print(json.dumps(result, indent=2))
    elif args.script:
        # Generate optimization script
        result = optimizer.generate_schema_optimization_script()
        print(result['schema_optimization_script'])
    elif args.execute:
        # Execute SQL
        result = optimizer.execute_optimization(args.execute)
        import json
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()

if __name__ == "__main__":
    run_optimizer_cli()
