# CloudFlare Configuration for Maily

This directory contains configuration files and scripts for CloudFlare services used by Maily.

## Components

- **Workers**: CloudFlare Workers for edge computing
  - `api-edge-cache.js`: Caches API responses at the edge
  - `dynamic-content.js`: Serves dynamic content based on user location and preferences

- **WAF Rules**: Web Application Firewall rules to protect Maily from common attacks
  - Rate limiting
  - SQL injection protection
  - XSS protection
  - Path traversal protection
  - Remote file inclusion protection
  - Command injection protection
  - Geolocation-based challenges
  - Bot protection
  - Admin path protection
  - Authentication endpoint protection

## Deployment

### Workers

Workers are deployed using Wrangler, CloudFlare's CLI tool:

```bash
# Install Wrangler
npm install -g wrangler

# Authenticate with CloudFlare
wrangler login

# Deploy API Edge Cache Worker
wrangler deploy -e api-edge-cache

# Deploy Dynamic Content Worker
wrangler deploy -e dynamic-content
```

### WAF Rules

WAF rules are deployed using the `deploy-cloudflare-waf.sh` script:

```bash
# Set required environment variables
export CLOUDFLARE_API_TOKEN="your-api-token"
export CLOUDFLARE_ZONE_ID="your-zone-id"

# Deploy WAF rules
./scripts/deploy-cloudflare-waf.sh
```

## Configuration

### Wrangler Configuration

The `wrangler.toml` file contains configuration for CloudFlare Workers:

- Global settings
- Environment-specific settings (production, staging, development)
- KV namespace bindings
- Environment variables
- Routes and zones

### WAF Rules Configuration

The `waf-rules.json` file contains the WAF rules configuration:

- Rate limiting rules
- Security rules for common attacks
- Geolocation-based rules
- Bot protection rules
- Path-specific protection rules

## Customization

### Adding a New Worker

1. Create a new JavaScript file in the `workers` directory
2. Add a new environment section to `wrangler.toml`
3. Deploy the worker using Wrangler

### Adding a New WAF Rule

1. Add a new rule to `waf-rules.json`
2. Deploy the updated rules using the `deploy-cloudflare-waf.sh` script

## Security Considerations

- Keep your CloudFlare API token secure
- Regularly review and update WAF rules
- Monitor CloudFlare logs for security events
- Test WAF rules in staging before deploying to production
