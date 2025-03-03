#!/bin/bash
# setup-cicd-pipeline.sh
# Script to set up the CI/CD pipeline for Maily

set -e

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
  echo "GitHub CLI (gh) is not installed. Please install it first."
  echo "Visit: https://cli.github.com/"
  exit 1
fi

# Check if user is authenticated with GitHub CLI
if ! gh auth status &> /dev/null; then
  echo "You are not authenticated with GitHub CLI. Please run 'gh auth login' first."
  exit 1
fi

# Get the current repository
REPO=$(git remote get-url origin | sed -E 's/.*github.com[:/]([^/]+\/[^/]+)(\.git)?$/\1/')

if [ -z "$REPO" ]; then
  echo "Could not determine GitHub repository. Please make sure you're in a Git repository with a GitHub remote."
  exit 1
fi

echo "Setting up CI/CD pipeline for repository: $REPO"

# Create GitHub Actions secrets
echo "Setting up GitHub Actions secrets..."

# AWS credentials
read -p "Enter AWS Access Key ID: " AWS_ACCESS_KEY_ID
read -sp "Enter AWS Secret Access Key: " AWS_SECRET_ACCESS_KEY
echo

# Slack webhook URL
read -p "Enter Slack Webhook URL (optional, press Enter to skip): " SLACK_WEBHOOK_URL

# Set GitHub secrets
echo "Setting GitHub secrets..."
echo "Setting AWS_ACCESS_KEY_ID..."
gh secret set AWS_ACCESS_KEY_ID -b "$AWS_ACCESS_KEY_ID" -R "$REPO"

echo "Setting AWS_SECRET_ACCESS_KEY..."
gh secret set AWS_SECRET_ACCESS_KEY -b "$AWS_SECRET_ACCESS_KEY" -R "$REPO"

if [ -n "$SLACK_WEBHOOK_URL" ]; then
  echo "Setting SLACK_WEBHOOK_URL..."
  gh secret set SLACK_WEBHOOK_URL -b "$SLACK_WEBHOOK_URL" -R "$REPO"
fi

# Create GitHub environments
echo "Creating GitHub environments..."

# Create staging environment
echo "Creating 'staging' environment..."
gh api repos/$REPO/environments/staging --method PUT

# Create production environment with protection rules
echo "Creating 'production' environment with protection rules..."
gh api repos/$REPO/environments/production --method PUT -f reviewers='[]' -f deployment_branch_policy='{"protected_branches":true,"custom_branch_policies":false}'

echo "CI/CD pipeline setup completed successfully!"
echo
echo "Next steps:"
echo "1. Push your code to GitHub to trigger the CI/CD pipeline"
echo "2. Configure branch protection rules in GitHub repository settings"
echo "3. Set up required reviewers for the production environment"
echo
echo "You can manually trigger a deployment using GitHub Actions workflow dispatch:"
echo "gh workflow run ci-cd.yml -f environment=staging"

# Check for dry-run mode
DRY_RUN=false
for arg in "$@"; do
  if [[ "$arg" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "Running in dry-run mode. No changes will be made."
  fi
done

