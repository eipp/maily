#!/bin/bash
# Script to implement the consolidation plan for Maily scripts
# This script moves scripts to their new directories based on the consolidation plan

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Maily Scripts Migration${NC}"
echo "This script will implement the consolidation plan as outlined in CONSOLIDATION-PLAN.md"
echo "Timestamp: $(date)"

# Create directories if they don't exist
echo -e "${GREEN}Creating directory structure...${NC}"
mkdir -p scripts/core
mkdir -p scripts/testing
mkdir -p scripts/security
mkdir -p scripts/infrastructure
mkdir -p scripts/database
mkdir -p scripts/docs
mkdir -p scripts/utils

# 1. Core Deployment System
echo -e "${GREEN}Migrating core deployment scripts...${NC}"
cp -v scripts/maily-deploy.sh scripts/core/
cp -v scripts/deployment-validator.sh scripts/core/
cp -v scripts/config-collector.sh scripts/core/
cp -v scripts/update-image-tags.sh scripts/core/
cp -rv scripts/deploy-phases/ scripts/core/

# 2. Testing Scripts
echo -e "${GREEN}Migrating testing scripts...${NC}"
cp -v scripts/smoke-test.js scripts/testing/
cp -v scripts/enhanced-smoke-test.js scripts/testing/
cp -v scripts/e2e-staging-test.js scripts/testing/
cp -v scripts/run_tests.sh scripts/testing/
cp -v scripts/run-chaos-tests.sh scripts/testing/
cp -v scripts/test-ai-ml.sh scripts/testing/

# Create a directory for load testing scripts
mkdir -p scripts/testing/load-testing
cp -v scripts/load-testing.sh scripts/testing/load-testing/
cp -rv scripts/load-testing/ scripts/testing/load-testing/
cp -v scripts/load_test.py scripts/testing/load-testing/
cp -rv scripts/performance/ scripts/testing/load-testing/

# 3. Security Scripts
echo -e "${GREEN}Migrating security scripts...${NC}"
cp -v scripts/automated-security-scan.sh scripts/security/
cp -v scripts/security-scanning.sh scripts/security/
cp -v scripts/secret-rotation.sh scripts/security/
cp -v scripts/create-k8s-secrets.sh scripts/security/
cp -v scripts/setup-auth-security.sh scripts/security/
cp -rv scripts/security/* scripts/security/

# 4. Infrastructure Scripts
echo -e "${GREEN}Migrating infrastructure scripts...${NC}"
cp -v scripts/deploy-eks-cluster.sh scripts/infrastructure/
cp -v scripts/setup-production-rds.sh scripts/infrastructure/
cp -v scripts/setup-redis-cluster.sh scripts/infrastructure/
cp -v scripts/deploy-cloudflare-waf.sh scripts/infrastructure/
cp -v scripts/setup-devops-infrastructure.sh scripts/infrastructure/
cp -v scripts/setup-production-environment.sh scripts/infrastructure/
cp -v scripts/setup-datadog-monitoring.sh scripts/infrastructure/
cp -v scripts/configure-dns.sh scripts/infrastructure/
cp -v scripts/configure-ssl-tls.sh scripts/infrastructure/
cp -v scripts/automated-certificate-management.sh scripts/infrastructure/

# 5. Database Scripts
echo -e "${GREEN}Migrating database scripts...${NC}"
cp -v scripts/db-migration.sh scripts/database/
cp -v scripts/check-migrations.sh scripts/database/
cp -v scripts/validate-migrations.js scripts/database/
cp -v scripts/schema-snapshot.sh scripts/database/
cp -v scripts/create-migration.sh scripts/database/
cp -v scripts/configure-database-backups.sh scripts/database/
cp -v scripts/consolidate-migrations.sh scripts/database/

# 6. Documentation Scripts
echo -e "${GREEN}Migrating documentation scripts...${NC}"
cp -v scripts/docs-automation.js scripts/docs/
cp -v scripts/generate-api-docs.js scripts/docs/
cp -v scripts/generate-inline-docs.js scripts/docs/
cp -v scripts/verify-doc-links.js scripts/docs/
cp -v scripts/cleanup-docs.js scripts/docs/
cp -v scripts/adr.js scripts/docs/

# 7. Utility Scripts
echo -e "${GREEN}Migrating utility scripts...${NC}"
cp -v scripts/check-dependencies.js scripts/utils/
cp -v scripts/check-critical-metrics.sh scripts/utils/
cp -v scripts/automated-rollback.sh scripts/utils/
cp -v scripts/generate-encryption-key.js scripts/utils/
cp -v scripts/generate-icons.js scripts/utils/
cp -v scripts/update-dependencies.sh scripts/utils/
cp -v scripts/update-missing-dependencies.js scripts/utils/
cp -v scripts/docker-compose-env.sh scripts/utils/
cp -v scripts/source-env.sh scripts/utils/
cp -v scripts/get-refresh-token.js scripts/utils/
cp -v scripts/setup-dev-environment.sh scripts/utils/
cp -v scripts/install-core-deps.js scripts/utils/
cp -v scripts/install-shadcn.sh scripts/utils/
cp -v scripts/verify-all-scripts.sh scripts/utils/

echo -e "${GREEN}Script migration completed!${NC}"
echo "The scripts have been copied to their new locations according to the consolidation plan."
echo "Next steps:"
echo "1. Test the new structure to ensure all scripts work correctly"
echo "2. Update documentation to reflect the new organization"
echo "3. Create consolidated scripts where needed"
echo "4. After verification, remove the redundant scripts as identified in REDUNDANT-SCRIPTS.md"

echo -e "${YELLOW}Note: Original scripts have not been removed. This script only copies them to new locations.${NC}"
