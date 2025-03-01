#!/bin/bash

# Maily Repository Optimization Verification Script
# This script verifies that the optimization process was successful

set -e

echo "=== Verifying Maily Repository Optimization ==="
echo "$(date '+%Y-%m-%d %H:%M:%S')"
echo

# Check if optimization reports exist
if [ ! -d "optimization/reports" ]; then
    echo "Error: optimization/reports directory does not exist"
    echo "Please run the optimization process first"
    exit 1
fi

# Check if required reports exist
required_reports=(
    "optimization/reports/final-report.md"
    "optimization/reports/duplicate-code.json"
    "optimization/reports/import-updates.json"
    "optimization/reports/optimization-summary.md"
)

missing_reports=0
for report in "${required_reports[@]}"; do
    if [ ! -f "$report" ]; then
        echo "Error: $report does not exist"
        missing_reports=$((missing_reports + 1))
    else
        echo "✓ $report exists"
    fi
done

if [ $missing_reports -gt 0 ]; then
    echo "Error: $missing_reports reports are missing"
    echo "Please run the optimization process again"
    exit 1
fi

# Verify that deprecated components were removed
deprecated_components=(
    "apps/api/middleware/usage_monitoring.py"
    "apps/api/services/usage_monitoring_service.py"
    "packages/ai"
    "apps/api/models"
    "apps/trust-infrastructure"
)

remaining_components=0
for component in "${deprecated_components[@]}"; do
    if [ -e "$component" ]; then
        echo "Warning: $component still exists"
        remaining_components=$((remaining_components + 1))
    else
        echo "✓ $component was removed"
    fi
done

if [ $remaining_components -gt 0 ]; then
    echo "Warning: $remaining_components deprecated components still exist"
else
    echo "All deprecated components were successfully removed"
fi

# Verify that backups were created
if [ ! -d "optimization/backups" ]; then
    echo "Error: optimization/backups directory does not exist"
    exit 1
fi

# Check if logs were created
if [ ! -d "optimization/logs" ]; then
    echo "Error: optimization/logs directory does not exist"
    exit 1
fi

if [ ! -f "optimization/logs/master.log" ]; then
    echo "Error: optimization/logs/master.log does not exist"
    exit 1
else
    echo "✓ optimization/logs/master.log exists"
fi

if [ ! -f "optimization/logs/removal.log" ]; then
    echo "Error: optimization/logs/removal.log does not exist"
    exit 1
else
    echo "✓ optimization/logs/removal.log exists"
fi

echo
echo "=== Maily Repository Optimization Verification Completed ==="
echo "$(date '+%Y-%m-%d %H:%M:%S')"

if [ $missing_reports -eq 0 ] && [ $remaining_components -eq 0 ]; then
    echo "✓ Optimization process was successful"
    exit 0
else
    echo "✗ Optimization process was not fully successful"
    exit 1
fi
