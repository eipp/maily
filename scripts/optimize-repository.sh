#!/bin/bash

# Maily Repository Optimization Script
# This script removes deprecated components and generates a report

set -e

echo "=== Starting Maily Repository Optimization ==="
echo "$(date '+%Y-%m-%d %H:%M:%S')"
echo

# Create optimization directory structure if it doesn't exist
mkdir -p optimization/backups
mkdir -p optimization/logs
mkdir -p optimization/reports

# Function to backup a file or directory before removing it
backup_file() {
    local path=$1
    if [ -e "$path" ]; then
        local backup_path="optimization/backups/$(dirname "$path" | sed 's/^\.\///')"
        mkdir -p "$backup_path"
        cp -r "$path" "$backup_path/"
        echo "Backed up $path to $backup_path"
    else
        echo "Warning: $path does not exist, skipping backup"
    fi
}

# Function to log actions
log_action() {
    local action=$1
    local path=$2
    local reason=$3
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $action: $path - $reason" >> optimization/logs/removal.log
    echo "$action: $path - $reason"
}

# List of deprecated components to remove
declare -a deprecated_components=(
    "apps/api/middleware/usage_monitoring.py:Usage monitoring middleware is deprecated and replaced by the new metrics system"
    "apps/api/services/usage_monitoring_service.py:Usage monitoring service is deprecated and replaced by the new metrics system"
    "packages/ai:AI package is deprecated and replaced by the new AI service integration"
    "apps/api/models:Models module is replaced by the OctoTools integration"
    "apps/trust-infrastructure:Trust infrastructure is deprecated and replaced by the new blockchain service"
)

# List of deprecated documentation files to remove
declare -a deprecated_docs=(
    "docs/sprint-9-documentation-summary.md:Outdated sprint documentation"
    "docs/modernization-roadmap.md:Roadmap has been completed and is now outdated"
    "docs/ai-handbook.md:AI handbook is deprecated and replaced by the new AI service documentation"
    "apps/api/ROUTING.md:Routing documentation is outdated and replaced by the API documentation"
)

# Remove deprecated components
echo "Removing deprecated components..."
for component in "${deprecated_components[@]}"; do
    path=${component%%:*}
    reason=${component#*:}

    if [ -e "$path" ]; then
        backup_file "$path"
        rm -rf "$path"
        log_action "Removed component" "$path" "$reason"
    else
        log_action "Skipped component" "$path" "Does not exist"
    fi
done

# Remove deprecated documentation
echo "Removing deprecated documentation..."
for doc in "${deprecated_docs[@]}"; do
    path=${doc%%:*}
    reason=${doc#*:}

    if [ -e "$path" ]; then
        backup_file "$path"
        rm -f "$path"
        log_action "Removed documentation" "$path" "$reason"
    else
        log_action "Skipped documentation" "$path" "Does not exist"
    fi
done

# Generate optimization report
echo "Generating optimization report..."
cat > optimization/reports/optimization-summary.md << EOF
# Maily Repository Optimization Summary

## Overview
This report summarizes the optimization actions performed on the Maily repository to prepare it for production.

## Removed Components
The following components were removed from the repository:

| Component | Reason |
|-----------|--------|
EOF

for component in "${deprecated_components[@]}"; do
    path=${component%%:*}
    reason=${component#*:}
    echo "| \`$path\` | $reason |" >> optimization/reports/optimization-summary.md
done

cat >> optimization/reports/optimization-summary.md << EOF

## Removed Documentation
The following documentation files were removed:

| Documentation | Reason |
|---------------|--------|
EOF

for doc in "${deprecated_docs[@]}"; do
    path=${doc%%:*}
    reason=${doc#*:}
    echo "| \`$path\` | $reason |" >> optimization/reports/optimization-summary.md
done

cat >> optimization/reports/optimization-summary.md << EOF

## Impact
The removal of these deprecated components has:
- Reduced the repository size
- Removed potential confusion from outdated code
- Improved documentation accuracy
- Streamlined the codebase for better maintainability

## Next Steps
1. Update import statements in files that referenced the removed components
2. Run tests to ensure no regressions
3. Update deployment configurations to reflect the removed components
4. Update documentation to reflect the current architecture

## Backup
All removed components have been backed up to \`optimization/backups/\` for reference.

## Completion Date
$(date '+%Y-%m-%d')
EOF

echo "Optimization report generated at optimization/reports/optimization-summary.md"

echo
echo "=== Maily Repository Optimization Completed ==="
echo "$(date '+%Y-%m-%d %H:%M:%S')"
