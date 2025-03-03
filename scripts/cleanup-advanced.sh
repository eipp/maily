#!/bin/bash

set -euo pipefail

echo "Starting advanced cleanup..."

# Create backup directory
BACKUP_DIR="cleanup_advanced_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Function to safely move files to backup
safe_backup() {
    local source=$1
    if [ -e "$source" ]; then
        echo "Backing up $source"
        cp -r "$source" "$BACKUP_DIR/"
    fi
}

# Consolidate analytics services
echo "Consolidating analytics services..."
if [ -d "apps/analytics" ] && [ -d "apps/analytics-service" ]; then
    safe_backup "apps/analytics"
    safe_backup "apps/analytics-service"
    
    # Create new consolidated service
    mkdir -p apps/analytics-new
    cp -r apps/analytics-service/* apps/analytics-new/
    
    # Copy unique files from old analytics
    rsync -av --ignore-existing apps/analytics/ apps/analytics-new/
    
    # Replace old services with consolidated one
    rm -rf apps/analytics apps/analytics-service
    mv apps/analytics-new apps/analytics-service
fi

# Consolidate campaign services
echo "Consolidating campaign services..."
if [ -d "apps/campaign" ] && [ -d "apps/campaign-service" ]; then
    safe_backup "apps/campaign"
    safe_backup "apps/campaign-service"
    
    # Create new consolidated service
    mkdir -p apps/campaign-new
    cp -r apps/campaign-service/* apps/campaign-new/
    
    # Copy unique files from old campaign
    rsync -av --ignore-existing apps/campaign/ apps/campaign-new/
    
    # Replace old services with consolidated one
    rm -rf apps/campaign apps/campaign-service
    mv apps/campaign-new apps/campaign-service
fi

# Move performance monitoring into analytics service
echo "Consolidating performance monitoring..."
if [ -d "apps/performance" ]; then
    safe_backup "apps/performance"
    
    # Create performance module in analytics service
    mkdir -p apps/analytics-service/src/performance
    cp -r apps/performance/src/* apps/analytics-service/src/performance/
    
    # Update package.json dependencies
    if [ -f "apps/performance/package.json" ]; then
        echo "Merging performance dependencies into analytics service..."
        jq -s '.[0].dependencies * .[1].dependencies | {dependencies: .}' \
            apps/analytics-service/package.json apps/performance/package.json > temp.json
        mv temp.json apps/analytics-service/package.json
    fi
    
    rm -rf apps/performance
fi

# Clean up security placeholders
echo "Cleaning up security placeholders..."
find . -type f -name "*.yaml" -exec sed -i.bak 's/https:\/\/hooks.slack.com\/services\/[A-Z0-9]\+\/[A-Z0-9]\+\/[A-Z0-9]\+/{{ SLACK_WEBHOOK_URL }}/g' {} \;
find . -type f -name "*.yaml" -exec sed -i.bak 's/[a-zA-Z0-9]\{32\}/{{ PAGERDUTY_SERVICE_KEY }}/g' {} \;

# Remove backup files created by sed
find . -name "*.bak" -type f -delete

# Clean up unimplemented features
echo "Marking unimplemented features..."
cat > UNIMPLEMENTED_FEATURES.md << EOL
# Unimplemented Features

The following features are currently marked as TODO and need implementation:

## Document Generation
- PDF generation
- Presentation generation
- Contract generation
- Report generation
- Newsletter generation
- Form generation
- Invoice generation

## Authentication
- Login logic
- Signup logic
- Password reset
- User authentication

## Monitoring
- Admin notifications in throttling service

Please prioritize these features for implementation or remove them if no longer needed.
EOL

echo "Cleanup complete! Backup created in $BACKUP_DIR"
echo "Please review UNIMPLEMENTED_FEATURES.md for features that need attention"
echo "You can remove the backup directory once you've verified everything works:"
echo "rm -rf $BACKUP_DIR" 