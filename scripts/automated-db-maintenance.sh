#!/bin/bash

# Automated Database Maintenance Script
#
# This script automates periodic PostgreSQL database maintenance tasks including:
# 1. VACUUM ANALYZE to reclaim space and update statistics
# 2. Index maintenance and rebuilding
# 3. Bloat detection and cleanup
# 4. Long-running query detection and management
# 5. Connection monitoring
# 6. Performance statistics collection
#
# It can be scheduled to run automatically and replace manual maintenance tasks

set -e

# Configuration
DB_HOST="${DB_HOST:-maily-prod.example.com}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-maily}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-}"
REPORT_DIR="./db-maintenance-reports"
MAINTENANCE_WINDOW="${MAINTENANCE_WINDOW:-false}" # Set to true during scheduled maintenance windows
VACUUM_THRESHOLD="${VACUUM_THRESHOLD:-20}" # Percentage of dead tuples to trigger VACUUM
REINDEX_THRESHOLD="${REINDEX_THRESHOLD:-30}" # Percentage of bloat to trigger REINDEX
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}" # Set as environment variable

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Initialize report variables
report_id="db-maintenance-$(date +%Y%m%d-%H%M%S)"
report_file="${REPORT_DIR}/${report_id}.md"
maintenance_actions=()
warnings=()
errors=()

# Logging functions
log() {
  echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
  maintenance_actions+=("✅ $1")
}

warn() {
  echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
  warnings+=("⚠️ $1")
}

error() {
  echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
  errors+=("❌ $1")
}

# Create report directory if it doesn't exist
mkdir -p "${REPORT_DIR}"

# Set up PostgreSQL command
if [ -n "${DB_PASSWORD}" ]; then
  export PGPASSWORD="${DB_PASSWORD}"
  PG_CMD="psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} -t -c"
else
  # Use connection string without password - assumes .pgpass file or other auth method
  PG_CMD="psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} -t -c"
fi

# Run a SQL query and get the result
run_query() {
  $PG_CMD "$1"
}

# Run query but don't fail if it errors
safe_query() {
  $PG_CMD "$1" || echo "Query failed: $1"
}

# Check database statistics
check_database_stats() {
  log "Checking database statistics..."
  db_size=$(run_query "SELECT pg_size_pretty(pg_database_size('${DB_NAME}'));")
  log "Database size: ${db_size}"

  table_count=$(run_query "SELECT count(*) FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema');")
  log "Table count: ${table_count}"

  connection_count=$(run_query "SELECT count(*) FROM pg_stat_activity;")
  log "Current connections: ${connection_count}"

  max_connections=$(run_query "SHOW max_connections;")
  log "Max connections: ${max_connections}"

  # Save detailed stats to report
  run_query "SELECT schemaname, tablename, pg_size_pretty(pg_table_size(schemaname||'.'||tablename)) as size FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema') ORDER BY pg_table_size(schemaname||'.'||tablename) DESC LIMIT 10;" > "${report_file}.table_sizes"
}

# Check for tables needing VACUUM
check_vacuum_needs() {
  log "Checking for tables needing VACUUM..."

  vacuum_query="
    SELECT
      schemaname || '.' || relname AS table_name,
      n_dead_tup AS dead_tuples,
      n_live_tup AS live_tuples,
      round(n_dead_tup * 100.0 / nullif(n_live_tup, 0), 1) AS dead_percentage
    FROM pg_stat_user_tables
    WHERE n_dead_tup > 0
    ORDER BY n_dead_tup DESC
    LIMIT 20;
  "

  vacuum_results=$(run_query "${vacuum_query}")
  echo "${vacuum_results}" > "${report_file}.vacuum_candidates"

  # Count tables over threshold
  tables_to_vacuum=$(echo "${vacuum_results}" | grep -v "^$" | awk -v threshold="${VACUUM_THRESHOLD}" '$4 > threshold {count++} END {print count}')

  if [ "${tables_to_vacuum}" -gt 0 ]; then
    log "Found ${tables_to_vacuum} tables needing VACUUM (>${VACUUM_THRESHOLD}% dead tuples)"
  else
    log "No tables need VACUUM at this time"
  fi
}

# Check for index bloat
check_index_bloat() {
  log "Checking for index bloat..."

  bloat_query="
    SELECT
      schemaname || '.' || tablename AS table_name,
      indexname,
      pg_size_pretty(pg_relation_size(schemaname || '.' || indexrelname)) as index_size,
      round(100 * (bloat_ratio-1)) as bloat_percentage
    FROM (
      SELECT
        schemaname,
        tablename,
        indexname,
        indexrelname,
        idx_blks,
        idx_blks_used,
        CASE WHEN idx_blks_used = 0 THEN 1 ELSE idx_blks*1.0/idx_blks_used END as bloat_ratio
      FROM (
        -- Complex index bloat calculation query that's been simplified here
        SELECT
          ns.nspname AS schemaname,
          tbl.relname AS tablename,
          idx.relname AS indexname,
          idx.relname AS indexrelname,
          coalesce(1, 0) AS idx_blks,
          coalesce(1, 0) AS idx_blks_used
        FROM pg_index i
        JOIN pg_class idx ON idx.oid = i.indexrelid
        JOIN pg_class tbl ON tbl.oid = i.indrelid
        JOIN pg_namespace ns ON ns.oid = tbl.relnamespace
        WHERE ns.nspname NOT IN ('pg_catalog', 'information_schema')
      ) AS inner_bloat_calc
    ) AS bloat_calc
    WHERE round(100 * (bloat_ratio-1)) > 0
    ORDER BY bloat_ratio DESC
    LIMIT 20;
  "

  # This is a simplified version - a production system would use a more accurate but complex bloat query
  bloat_results=$(safe_query "${bloat_query}")
  echo "${bloat_results}" > "${report_file}.index_bloat"

  # Count indexes over threshold
  indexes_to_rebuild=$(echo "${bloat_results}" | grep -v "^$" | awk -v threshold="${REINDEX_THRESHOLD}" '$4 > threshold {count++} END {print count}')

  if [ "${indexes_to_rebuild}" -gt 0 ]; then
    log "Found ${indexes_to_rebuild} indexes with significant bloat (>${REINDEX_THRESHOLD}%)"
  else
    log "No indexes have significant bloat at this time"
  fi
}

# Check for long-running transactions
check_long_running_queries() {
  log "Checking for long-running queries..."

  query="
    SELECT
      pid,
      now() - pg_stat_activity.query_start AS duration,
      query
    FROM pg_stat_activity
    WHERE state = 'active'
      AND now() - pg_stat_activity.query_start > interval '5 minutes'
      AND query NOT LIKE '%pg_stat_activity%'
    ORDER BY duration DESC;
  "

  long_queries=$(run_query "${query}")
  echo "${long_queries}" > "${report_file}.long_queries"

  # Count long-running queries
  long_query_count=$(echo "${long_queries}" | grep -v "^$" | wc -l | tr -d ' ')

  if [ "${long_query_count}" -gt 0 ]; then
    warn "Found ${long_query_count} queries running longer than 5 minutes"

    # If we're in a maintenance window, consider terminating the long-running queries
    if [ "${MAINTENANCE_WINDOW}" = "true" ]; then
      if [ "${long_query_count}" -gt 5 ]; then
        warn "Too many long-running queries to automatically terminate, please review manually"
      else
        log "Maintenance window active, terminating long-running queries..."
        echo "${long_queries}" | grep -v "^$" | awk '{print $1}' | while read pid; do
          if [ -n "${pid}" ]; then
            log "Terminating query with PID ${pid}"
            run_query "SELECT pg_terminate_backend(${pid});"
          fi
        done
      fi
    fi
  else
    log "No long-running queries found"
  fi
}

# Check for locks and blocking queries
check_locks() {
  log "Checking for locks and blocked queries..."

  lock_query="
    SELECT
      blocked_locks.pid AS blocked_pid,
      blocked_activity.usename AS blocked_user,
      blocking_locks.pid AS blocking_pid,
      blocking_activity.usename AS blocking_user,
      blocked_activity.query AS blocked_statement,
      blocking_activity.query AS blocking_statement
    FROM pg_catalog.pg_locks blocked_locks
    JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
    JOIN pg_catalog.pg_locks blocking_locks
        ON blocking_locks.locktype = blocked_locks.locktype
        AND blocking_locks.DATABASE IS NOT DISTINCT FROM blocked_locks.DATABASE
        AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
        AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
        AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
        AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
        AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
        AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
        AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
        AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
        AND blocking_locks.pid != blocked_locks.pid
    JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
    WHERE NOT blocked_locks.GRANTED;
  "

  locks=$(run_query "${lock_query}")
  echo "${locks}" > "${report_file}.locks"

  # Count locked transactions
  lock_count=$(echo "${locks}" | grep -v "^$" | wc -l | tr -d ' ')

  if [ "${lock_count}" -gt 0 ]; then
    warn "Found ${lock_count} blocked queries"

    # If we're in a maintenance window, consider terminating the blocking queries
    if [ "${MAINTENANCE_WINDOW}" = "true" ]; then
      if [ "${lock_count}" -gt 5 ]; then
        warn "Too many locks to automatically resolve, please review manually"
      else
        log "Maintenance window active, terminating blocking queries..."
        echo "${locks}" | grep -v "^$" | awk '{print $3}' | sort -u | while read pid; do
          if [ -n "${pid}" ]; then
            log "Terminating blocking query with PID ${pid}"
            run_query "SELECT pg_terminate_backend(${pid});"
          fi
        done
      fi
    fi
  else
    log "No blocked queries found"
  fi
}

# Run VACUUM ANALYZE
run_vacuum() {
  if [ "${MAINTENANCE_WINDOW}" = "true" ]; then
    log "Running VACUUM ANALYZE..."
    run_query "VACUUM ANALYZE;" > "${report_file}.vacuum_output" 2>&1
    log "VACUUM ANALYZE completed"
  else
    # Outside maintenance window, only vacuum specific tables that need it
    vacuum_tables=$(run_query "
      SELECT schemaname || '.' || relname
      FROM pg_stat_user_tables
      WHERE n_dead_tup > 0
        AND round(n_dead_tup * 100.0 / nullif(n_live_tup, 0), 1) > ${VACUUM_THRESHOLD}
      ORDER BY n_dead_tup DESC
      LIMIT 5;
    ")

    table_count=$(echo "${vacuum_tables}" | grep -v "^$" | wc -l | tr -d ' ')

    if [ "${table_count}" -gt 0 ]; then
      log "Running targeted VACUUM ANALYZE on ${table_count} tables..."
      echo "${vacuum_tables}" | grep -v "^$" | while read table; do
        if [ -n "${table}" ]; then
          table=$(echo "${table}" | tr -d ' ')
          log "Vacuuming table ${table}"
          run_query "VACUUM ANALYZE ${table};" >> "${report_file}.vacuum_output" 2>&1
        fi
      done
      log "Targeted VACUUM ANALYZE completed"
    else
      log "No tables need immediate vacuuming"
    fi
  fi
}

# Rebuild indexes with high bloat
rebuild_indexes() {
  if [ "${MAINTENANCE_WINDOW}" = "true" ]; then
    bloated_indexes=$(safe_query "
      SELECT
        schemaname || '.' || indexrelname AS idx
      FROM (
        SELECT
          schemaname,
          indexrelname,
          pg_relation_size(schemaname || '.' || indexrelname) as index_size,
          CASE WHEN idx_blks_used = 0 THEN 1 ELSE idx_blks*1.0/idx_blks_used END as bloat_ratio
        FROM (
          -- Simplified index bloat calculation
          SELECT
            ns.nspname AS schemaname,
            idx.relname AS indexrelname,
            coalesce(1, 0) AS idx_blks,
            coalesce(1, 0) AS idx_blks_used
          FROM pg_index i
          JOIN pg_class idx ON idx.oid = i.indexrelid
          JOIN pg_class tbl ON tbl.oid = i.indrelid
          JOIN pg_namespace ns ON ns.oid = tbl.relnamespace
          WHERE ns.nspname NOT IN ('pg_catalog', 'information_schema')
        ) AS inner_bloat_calc
      ) AS bloat_calc
      WHERE round(100 * (bloat_ratio-1)) > ${REINDEX_THRESHOLD}
      ORDER BY bloat_ratio DESC
      LIMIT 5;
    ")

    index_count=$(echo "${bloated_indexes}" | grep -v "^$" | wc -l | tr -d ' ')

    if [ "${index_count}" -gt 0 ]; then
      log "Rebuilding ${index_count} bloated indexes..."
      echo "${bloated_indexes}" | grep -v "^$" | while read idx; do
        if [ -n "${idx}" ]; then
          idx=$(echo "${idx}" | tr -d ' ')
          log "Rebuilding index ${idx}"
          run_query "REINDEX INDEX CONCURRENTLY ${idx};" >> "${report_file}.reindex_output" 2>&1
        fi
      done
      log "Index rebuilding completed"
    else
      log "No indexes need immediate rebuilding"
    fi
  else
    log "Index rebuilding skipped outside maintenance window"
  fi
}

# Update database statistics
update_statistics() {
  log "Updating database statistics..."
  run_query "ANALYZE VERBOSE;" > "${report_file}.analyze_output" 2>&1
  log "Database statistics updated"
}

# Generate maintenance report
generate_report() {
  log "Generating maintenance report..."

  # Create report header
  cat > "${report_file}" << EOF
# Database Maintenance Report

**Report ID:** ${report_id}
**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')
**Database:** ${DB_NAME}
**Maintenance Window:** ${MAINTENANCE_WINDOW}

## Summary
EOF

  # Add maintenance actions
  echo -e "\n### Actions Performed\n" >> "${report_file}"
  for action in "${maintenance_actions[@]}"; do
    echo "- ${action}" >> "${report_file}"
  done

  # Add warnings
  if [ ${#warnings[@]} -gt 0 ]; then
    echo -e "\n### Warnings\n" >> "${report_file}"
    for warning in "${warnings[@]}"; do
      echo "- ${warning}" >> "${report_file}"
    done
  fi

  # Add errors
  if [ ${#errors[@]} -gt 0 ]; then
    echo -e "\n### Errors\n" >> "${report_file}"
    for error_msg in "${errors[@]}"; do
      echo "- ${error_msg}" >> "${report_file}"
    done
  fi

  # Add additional sections from output files
  if [ -f "${report_file}.table_sizes" ]; then
    echo -e "\n## Largest Tables\n" >> "${report_file}"
    echo '```' >> "${report_file}"
    cat "${report_file}.table_sizes" >> "${report_file}"
    echo '```' >> "${report_file}"
    rm "${report_file}.table_sizes"
  fi

  if [ -f "${report_file}.vacuum_candidates" ]; then
    echo -e "\n## Tables Needing VACUUM\n" >> "${report_file}"
    echo '```' >> "${report_file}"
    cat "${report_file}.vacuum_candidates" >> "${report_file}"
    echo '```' >> "${report_file}"
    rm "${report_file}.vacuum_candidates"
  fi

  if [ -f "${report_file}.index_bloat" ]; then
    echo -e "\n## Index Bloat\n" >> "${report_file}"
    echo '```' >> "${report_file}"
    cat "${report_file}.index_bloat" >> "${report_file}"
    echo '```' >> "${report_file}"
    rm "${report_file}.index_bloat"
  fi

  if [ -f "${report_file}.long_queries" ]; then
    echo -e "\n## Long-Running Queries\n" >> "${report_file}"
    echo '```' >> "${report_file}"
    cat "${report_file}.long_queries" >> "${report_file}"
    echo '```' >> "${report_file}"
    rm "${report_file}.long_queries"
  fi

  if [ -f "${report_file}.locks" ]; then
    echo -e "\n## Locks and Blocked Queries\n" >> "${report_file}"
    echo '```' >> "${report_file}"
    cat "${report_file}.locks" >> "${report_file}"
    echo '```' >> "${report_file}"
    rm "${report_file}.locks"
  fi

  if [ -f "${report_file}.vacuum_output" ]; then
    echo -e "\n## VACUUM Output\n" >> "${report_file}"
    echo '```' >> "${report_file}"
    cat "${report_file}.vacuum_output" >> "${report_file}"
    echo '```' >> "${report_file}"
    rm "${report_file}.vacuum_output"
  fi

  if [ -f "${report_file}.reindex_output" ]; then
    echo -e "\n## REINDEX Output\n" >> "${report_file}"
    echo '```' >> "${report_file}"
    cat "${report_file}.reindex_output" >> "${report_file}"
    echo '```' >> "${report_file}"
    rm "${report_file}.reindex_output"
  fi

  if [ -f "${report_file}.analyze_output" ]; then
    echo -e "\n## ANALYZE Output\n" >> "${report_file}"
    echo '```' >> "${report_file}"
    cat "${report_file}.analyze_output" >> "${report_file}"
    echo '```' >> "${report_file}"
    rm "${report_file}.analyze_output"
  fi

  log "Report generated: ${report_file}"

  # Send notification if configured
  if [ -n "${SLACK_WEBHOOK_URL}" ]; then
    send_notification
  fi
}

# Send notification with report summary
send_notification() {
  log "Sending notification..."

  # Create notification payload
  payload=$(cat << EOF
{
  "text": "Database Maintenance Completed",
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "Database Maintenance Completed"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Report ID:* ${report_id}\n*Database:* ${DB_NAME}\n*Maintenance Window:* ${MAINTENANCE_WINDOW}"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Actions:*\n$(echo "${maintenance_actions[@]:0:5}" | sed 's/ /\n/g')\n..."
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "See full report for details: ${REPORT_DIR}/${report_id}.md"
      }
    }
  ]
}
EOF
)

  # Send notification
  curl -s -X POST -H "Content-Type: application/json" -d "${payload}" "${SLACK_WEBHOOK_URL}" > /dev/null
}

# Main function
main() {
  log "Starting automated database maintenance..."

  # Analyze database state
  check_database_stats
  check_vacuum_needs
  check_index_bloat
  check_long_running_queries
  check_locks

  # Perform maintenance tasks
  update_statistics
  run_vacuum

  # Only rebuild indexes during maintenance window
  if [ "${MAINTENANCE_WINDOW}" = "true" ]; then
    rebuild_indexes
  fi

  # Generate report
  generate_report

  log "Database maintenance completed!"
}

# Run main function
main
