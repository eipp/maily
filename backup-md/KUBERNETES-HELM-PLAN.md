# Kubernetes Helm Chart Migration Plan

This document outlines the plan for migrating the Kubernetes YAML configurations to Helm charts for better maintainability and standardization.

## Current Status

The repository currently contains multiple Kubernetes YAML files with significant duplication:

1. **Multiple Deployment Files**:
   - `/kubernetes/deployments/` contains 8+ deployment files
   - Many deployments have `.bak` versions with nearly identical content
   - Service-specific configurations duplicated across environments

2. **Redundant Service and Ingress Definitions**:
   - `/kubernetes/services/` contains redundant service definitions
   - `/kubernetes/ingress/` contains multiple ingress configurations
   - Network policies duplicated for each service

3. **Monitoring and Security Resources**:
   - `/kubernetes/monitoring/` contains Prometheus and Grafana configurations
   - Security-related resources scattered across directories

4. **Partial Helm Implementation**:
   - Partial Helm chart exists in `/infrastructure/helm/maily/`
   - Limited use of templating and values substitution

## Migration Goals

1. **Eliminate Configuration Duplication**:
   - Consolidate duplicate YAML files into templated resources
   - Use Helm's template capabilities for environment-specific values
   - Remove `.bak` files after migration verification

2. **Standardize Deployment Structure**:
   - Consistent resource naming conventions
   - Standardized label and selector schemes
   - Uniform pod specification patterns

3. **Environment-Specific Configuration**:
   - Separate values files for production, staging, and development
   - Clear override patterns for environment-specific settings
   - Secret management integration

4. **Improved Maintainability**:
   - Self-documenting templates with comments
   - Modular chart structure for easier updates
   - Helm test support for deployment verification

## Implementation Plan

### 1. Complete the Helm Chart Structure

**Task**: Enhance and complete the Helm chart structure.

- [ ] Standardize the `/infrastructure/helm/maily/` chart structure
- [ ] Define consistent templates for all resource types
- [ ] Create helpers for common patterns
- [ ] Document chart structure and conventions

### 2. Migrate Core Services

**Task**: Create templates for core service components.

- [ ] Convert API service deployments to templates
- [ ] Create AI service templates
- [ ] Implement web application templates
- [ ] Add worker service templates
- [ ] Create standardized service definitions

### 3. Implement Networking Resources

**Task**: Migrate and standardize networking configurations.

- [ ] Create ingress template with environment overrides
- [ ] Standardize network policy templates
- [ ] Implement service mesh configurations (if applicable)
- [ ] Add DNS configuration management

### 4. Monitoring and Security Integration

**Task**: Integrate monitoring and security resources.

- [ ] Create Prometheus configuration templates
- [ ] Implement Grafana dashboard management
- [ ] Add security resource templates
- [ ] Integrate secret management

### 5. Deployment Pipeline Integration

**Task**: Update CI/CD pipelines to use Helm charts.

- [ ] Create chart versioning scheme
- [ ] Update deployment scripts to use Helm
- [ ] Implement chart testing in CI
- [ ] Create rollback mechanisms

## Migration Strategy

1. **Phase 1**: Create base Helm chart structure
2. **Phase 2**: Migrate one service at a time, starting with less critical services
3. **Phase 3**: Add production safeguards (readiness probes, resources, etc.)
4. **Phase 4**: Integrate monitoring and security
5. **Phase 5**: Update CI/CD pipelines

## Testing Strategy

1. **Chart Validation**: Use `helm lint` and `helm template` to validate charts
2. **Staging Deployment**: Test each chart in staging environment
3. **Comparison Testing**: Compare rendered templates with existing YAML
4. **Upgrade Testing**: Test upgrade paths from current deployment

## Implementation Schedule

- Week 1: Complete Helm chart structure
- Week 2: Migrate core services
- Week 3: Implement networking resources
- Week 4: Add monitoring and security integration
- Week 5: Update CI/CD pipelines

## Acceptance Criteria

1. All Kubernetes resources defined in Helm charts
2. No redundant YAML files in the repository
3. Environment-specific values separated in values files
4. Deployment pipeline fully integrated with Helm
5. Documentation for chart usage and customization

## Long-Term Maintenance

1. **Chart Versioning**: Implement semantic versioning for charts
2. **Dependency Management**: Track external chart dependencies
3. **Chart Museum**: Consider setting up a private chart repository
4. **Upgrade Procedures**: Document and test upgrade procedures