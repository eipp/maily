/**
 * Feature Flag Management System
 *
 * A robust system for managing feature flags across the application
 * with support for environment-based, user-based, and percentage-based rollouts.
 */

interface FeatureFlagConfig {
  /** Flag name (unique identifier) */
  name: string;
  /** Description of the feature for documentation */
  description: string;
  /** Whether the flag is enabled by default */
  defaultValue: boolean;
  /** Environment-specific overrides */
  environments?: Record<string, boolean>;
  /** User or account-based targeting */
  userTargeting?: {
    /** List of user/account IDs that should have the feature enabled */
    enabledForUsers?: string[];
    /** List of user/account IDs that should have the feature disabled */
    disabledForUsers?: string[];
    /** Group names that should have the feature enabled */
    enabledForGroups?: string[];
  };
  /** Percentage-based rollout (0-100) */
  rolloutPercentage?: number;
  /** Whether the flag is in development (only enabled in non-production) */
  development?: boolean;
  /** Timeout for flag (ISO date string) - after this date, defaultValue is used */
  expiresAt?: string;
}

/**
 * Context provided to feature flag evaluation
 */
interface FeatureFlagContext {
  /** Current environment (e.g., 'development', 'staging', 'production') */
  environment: string;
  /** Current user or account ID (if available) */
  userId?: string;
  /** User groups or roles (if available) */
  userGroups?: string[];
}

/**
 * Feature flag management class
 */
export class FeatureFlags {
  private flags: Map<string, FeatureFlagConfig> = new Map();
  private context: FeatureFlagContext;

  /**
   * Initialize the feature flag system
   * @param context - The feature flag context
   * @param flags - Initial feature flag configurations
   */
  constructor(context: FeatureFlagContext, flags: FeatureFlagConfig[] = []) {
    this.context = context;

    // Initialize flags
    flags.forEach(flag => {
      this.flags.set(flag.name, flag);
    });
  }

  /**
   * Update the current context
   * @param context - New or updated context values
   */
  updateContext(context: Partial<FeatureFlagContext>): void {
    this.context = { ...this.context, ...context };
  }

  /**
   * Register a new feature flag
   * @param flag - The feature flag configuration
   */
  registerFlag(flag: FeatureFlagConfig): void {
    this.flags.set(flag.name, flag);
  }

  /**
   * Update an existing feature flag
   * @param name - The name of the flag to update
   * @param updates - The updates to apply
   */
  updateFlag(name: string, updates: Partial<FeatureFlagConfig>): void {
    const existing = this.flags.get(name);
    if (!existing) {
      throw new Error(`Feature flag '${name}' not found`);
    }

    this.flags.set(name, { ...existing, ...updates });
  }

  /**
   * Remove a feature flag
   * @param name - The name of the flag to remove
   */
  removeFlag(name: string): void {
    this.flags.delete(name);
  }

  /**
   * Check if a feature flag is enabled
   * @param name - The name of the feature flag
   * @returns Whether the feature is enabled
   */
  isEnabled(name: string): boolean {
    const flag = this.flags.get(name);

    // If flag doesn't exist, return false
    if (!flag) {
      console.warn(`Feature flag '${name}' does not exist`);
      return false;
    }

    // Check if flag is expired
    if (flag.expiresAt && new Date(flag.expiresAt) < new Date()) {
      return flag.defaultValue;
    }

    // Check environment-specific override
    if (flag.environments && flag.environments[this.context.environment] !== undefined) {
      return flag.environments[this.context.environment];
    }

    // Check development flag
    if (flag.development && this.context.environment === 'production') {
      return false;
    }

    // Check user targeting
    if (flag.userTargeting && this.context.userId) {
      // Explicit user disable overrides everything
      if (flag.userTargeting.disabledForUsers?.includes(this.context.userId)) {
        return false;
      }

      // Check if user is explicitly enabled
      if (flag.userTargeting.enabledForUsers?.includes(this.context.userId)) {
        return true;
      }

      // Check user groups
      if (flag.userTargeting.enabledForGroups && this.context.userGroups) {
        for (const group of flag.userTargeting.enabledForGroups) {
          if (this.context.userGroups.includes(group)) {
            return true;
          }
        }
      }
    }

    // Check percentage rollout
    if (flag.rolloutPercentage !== undefined && this.context.userId) {
      // Use a deterministic hash of the user ID for consistent rollout
      const hash = this.hashString(this.context.userId + name);
      const normalizedHash = hash % 100;

      return normalizedHash < flag.rolloutPercentage;
    }

    // Default to the flag's default value
    return flag.defaultValue;
  }

  /**
   * Get all registered feature flags
   * @returns All feature flag configurations
   */
  getAllFlags(): FeatureFlagConfig[] {
    return Array.from(this.flags.values());
  }

  /**
   * Get a specific feature flag configuration
   * @param name - The name of the feature flag
   * @returns The feature flag configuration
   */
  getFlag(name: string): FeatureFlagConfig | undefined {
    return this.flags.get(name);
  }

  /**
   * Convert feature flags to JSON for storage
   * @returns JSON string representation of all flags
   */
  toJSON(): string {
    return JSON.stringify(Array.from(this.flags.values()));
  }

  /**
   * Load feature flags from JSON
   * @param json - JSON string representation of flags
   */
  fromJSON(json: string): void {
    try {
      const flags = JSON.parse(json) as FeatureFlagConfig[];
      this.flags.clear();
      flags.forEach(flag => this.flags.set(flag.name, flag));
    } catch (error) {
      console.error('Failed to parse feature flags JSON', error);
    }
  }

  /**
   * Generate a simple hash from a string (for percentage-based rollout)
   * @param str - String to hash
   * @returns Numeric hash
   */
  private hashString(str: string): number {
    let hash = 0;
    if (str.length === 0) return hash;

    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }

    return Math.abs(hash);
  }
}

/**
 * Create a feature flag instance with the given context and initial flags
 * @param context - Feature flag context
 * @param initialFlags - Initial feature flag configurations
 * @returns Feature flag manager instance
 */
export function createFeatureFlags(
  context: FeatureFlagContext,
  initialFlags: FeatureFlagConfig[] = []
): FeatureFlags {
  return new FeatureFlags(context, initialFlags);
}

// Export interfaces for use in other files
export type { FeatureFlagConfig, FeatureFlagContext };
