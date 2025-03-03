#!/bin/bash

set -euo pipefail

echo "Starting redundant file cleanup..."

# Create backup directory
BACKUP_DIR="cleanup_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Function to safely move files to backup
safe_backup() {
    local source=$1
    if [ -e "$source" ]; then
        echo "Backing up $source"
        cp -r "$source" "$BACKUP_DIR/"
    fi
}

# Backup files before removal
safe_backup "prometheus-deployment.yaml"
safe_backup "prometheus-configmap.yaml"
safe_backup "deploy.sh"
safe_backup "mailylaunch.sh"
safe_backup "api"
safe_backup "services"
safe_backup "mkdocs.yml"
safe_backup "package-templates"
safe_backup "monitoring"
safe_backup "prometheus"

# Consolidate Prometheus configs
echo "Consolidating Prometheus configurations..."
if [ -d "kubernetes/monitoring" ]; then
    mv prometheus-configmap.yaml kubernetes/monitoring/ 2>/dev/null || true
fi

# Remove redundant files
echo "Removing redundant files..."
rm -f prometheus-deployment.yaml
rm -f deploy.sh
rm -f mailylaunch.sh

# Consolidate service directories
echo "Consolidating service directories..."
if [ -d "api" ] && [ -d "apps/api" ]; then
    echo "Removing redundant api directory..."
    rm -rf api
fi

if [ -d "services" ]; then
    echo "Moving any unique services to apps/..."
    for service in services/*; do
        if [ -d "$service" ]; then
            service_name=$(basename "$service")
            if [ ! -d "apps/$service_name" ]; then
                mv "$service" "apps/"
            fi
        fi
    done
    rm -rf services
fi

# Consolidate monitoring
if [ -d "monitoring" ] && [ -d "prometheus" ]; then
    echo "Consolidating monitoring setup..."
    mkdir -p kubernetes/monitoring/prometheus
    cp -r monitoring/* kubernetes/monitoring/ 2>/dev/null || true
    cp -r prometheus/* kubernetes/monitoring/prometheus/ 2>/dev/null || true
    rm -rf monitoring prometheus
fi

# Clean up package templates if they're no longer used
if [ -d "package-templates" ]; then
    echo "Removing legacy package templates..."
    rm -rf package-templates
fi

echo "Cleanup complete! Backup created in $BACKUP_DIR"
echo "Please verify the changes and commit them if satisfied."
echo "You can remove the backup directory once you've verified everything works:"
echo "rm -rf $BACKUP_DIR" 