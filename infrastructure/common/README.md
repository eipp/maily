# Common Infrastructure Components

This directory contains common infrastructure components that are shared across different environments and deployments in the Maily platform.

## Contents

- **templates/** - Reusable infrastructure templates
- **scripts/** - Common infrastructure management scripts
- **modules/** - Shared Terraform modules
- **policies/** - Security and compliance policies
- **monitoring/** - Common monitoring configurations

## Usage

The components in this directory are designed to be referenced and used by environment-specific infrastructure configurations. They provide a single source of truth for common infrastructure patterns and ensure consistency across different environments.

### Terraform Modules

The Terraform modules in this directory follow these design principles:
- Encapsulate a single infrastructure pattern
- Accept variables for customization
- Provide sensible defaults
- Include documentation with examples
- Follow Terraform best practices

Example usage:

```hcl
module "redis_cluster" {
  source = "../../common/modules/redis_cluster"
  
  name = "production-redis"
  node_count = 3
  instance_type = "cache.r5.large"
  vpc_id = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
}
```

### Security Policies

The security policies in this directory define common security controls and configurations that should be applied consistently across all environments. These include:

- Network policies
- Access control policies
- Encryption requirements
- Audit logging configurations
- Compliance controls

## Adding New Components

When adding new common components:
1. Ensure they are truly common and shared across environments
2. Document their purpose and usage
3. Follow infrastructure as code best practices
4. Include appropriate tests and validation
5. Consider versioning for major changes