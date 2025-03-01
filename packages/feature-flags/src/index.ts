/**
 * Feature Flag Management System
 *
 * Provides a centralized way to manage feature flags across the application.
 * Features can be enabled/disabled dynamically based on environment, context,
 * and user criteria.
 */

/**
 * Context for feature flag evaluation
 */
export interface FlagContext {
  /**
   * User ID for user-specific flags
   */
  userId?: string;

  /**
   * User role or roles
   */
  roles?: string | string[];

  /**
   * User groups
   */
  groups?: string[];

  /**
   * User attributes for targeting
   */
  attributes?: Record<string, any>;

  /**
   * Environment (e.g., development, staging, production)
   */
  environment?: string;

  /**
   * Additional context data
   */
  [key: string]: any;
}

/**
 * Feature flag rule definition
 */
export interface FlagRule {
  /**
   * Rule ID
   */
  id: string;

  /**
   * Rule description
   */
  description?: string;

  /**
   * Target environments (if empty, applies to all)
   */
  environments?: string[];

  /**
   * Target user IDs
   */
  userIds?: string[];

  /**
   * Target user roles
   */
  roles?: string[];

  /**
   * Target user groups
   */
  groups?: string[];

  /**
   * Percentage rollout (0-100)
   */
  percentage?: number;

  /**
   * Target attribute conditions
   */
  attributes?: Record<string, any>;

  /**
   * Custom evaluation function
   */
  evaluator?: (context: FlagContext) => boolean;

  /**
   * Flag value when rule matches
   */
  value: boolean | string | number | Record<string, any>;
}

/**
 * Feature flag definition
 */
export interface FeatureFlag {
  /**
   * Flag key (unique identifier)
   */
  key: string;

  /**
   * Flag description
   */
  description?: string;

  /**
   * Default value if no rules match
   */
  defaultValue: boolean | string | number | Record<string, any>;

  /**
   * Evaluation rules
   */
  rules?: FlagRule[];

  /**
   * Flag tags for organization
   */
  tags?: string[];

  /**
   * Flag owner (team or person)
   */
  owner?: string;

  /**
   * Creation date
   */
  createdAt?: Date;

  /**
   * Last modified date
   */
  updatedAt?: Date;
}

/**
 * Feature flag provider interface
 */
export interface FlagProvider {
  /**
   * Get a feature flag by key
   * @param key Flag key
   * @returns Feature flag or undefined if not found
   */
  getFlag(key: string): FeatureFlag | undefined;

  /**
   * Get all feature flags
   * @returns All feature flags
   */
  getAllFlags(): FeatureFlag[];

  /**
   * Evaluate a boolean feature flag
   * @param key Flag key
   * @param context Evaluation context
   * @param defaultValue Default value if flag is not found
   * @returns Flag value
   */
  getBooleanFlag(key: string, context?: FlagContext, defaultValue?: boolean): boolean;

  /**
   * Evaluate a string feature flag
   * @param key Flag key
   * @param context Evaluation context
   * @param defaultValue Default value if flag is not found
   * @returns Flag value
   */
  getStringFlag(key: string, context?: FlagContext, defaultValue?: string): string;

  /**
   * Evaluate a number feature flag
   * @param key Flag key
   * @param context Evaluation context
   * @param defaultValue Default value if flag is not found
   * @returns Flag value
   */
  getNumberFlag(key: string, context?: FlagContext, defaultValue?: number): number;

  /**
   * Evaluate a JSON feature flag
   * @param key Flag key
   * @param context Evaluation context
   * @param defaultValue Default value if flag is not found
   * @returns Flag value
   */
  getJsonFlag<T extends Record<string, any>>(key: string, context?: FlagContext, defaultValue?: T): T;
}

/**
 * Static flag provider using a configuration file or object
 */
export class StaticFlagProvider implements FlagProvider {
  private flags: Record<string, FeatureFlag>;

  /**
   * Create a static flag provider
   * @param flags Feature flags configuration
   */
  constructor(flags: Record<string, FeatureFlag> | FeatureFlag[]) {
    this.flags = Array.isArray(flags)
      ? flags.reduce((acc, flag) => ({ ...acc, [flag.key]: flag }), {})
      : flags;
  }

  /**
   * Get a feature flag by key
   * @param key Flag key
   * @returns Feature flag or undefined if not found
   */
  getFlag(key: string): FeatureFlag | undefined {
    return this.flags[key];
  }

  /**
   * Get all feature flags
   * @returns All feature flags
   */
  getAllFlags(): FeatureFlag[] {
    return Object.values(this.flags);
  }

  /**
   * Evaluate a boolean feature flag
   * @param key Flag key
   * @param context Evaluation context
   * @param defaultValue Default value if flag is not found
   * @returns Flag value
   */
  getBooleanFlag(key: string, context: FlagContext = {}, defaultValue = false): boolean {
    const flag = this.getFlag(key);

    if (!flag) {
      return defaultValue;
    }

    const value = this.evaluateFlag(flag, context);
    return typeof value === 'boolean' ? value : Boolean(value);
  }

  /**
   * Evaluate a string feature flag
   * @param key Flag key
   * @param context Evaluation context
   * @param defaultValue Default value if flag is not found
   * @returns Flag value
   */
  getStringFlag(key: string, context: FlagContext = {}, defaultValue = ''): string {
    const flag = this.getFlag(key);

    if (!flag) {
      return defaultValue;
    }

    const value = this.evaluateFlag(flag, context);
    return String(value);
  }

  /**
   * Evaluate a number feature flag
   * @param key Flag key
   * @param context Evaluation context
   * @param defaultValue Default value if flag is not found
   * @returns Flag value
   */
  getNumberFlag(key: string, context: FlagContext = {}, defaultValue = 0): number {
    const flag = this.getFlag(key);

    if (!flag) {
      return defaultValue;
    }

    const value = this.evaluateFlag(flag, context);
    return typeof value === 'number' ? value : Number(value);
  }

  /**
   * Evaluate a JSON feature flag
   * @param key Flag key
   * @param context Evaluation context
   * @param defaultValue Default value if flag is not found
   * @returns Flag value
   */
  getJsonFlag<T extends Record<string, any>>(key: string, context: FlagContext = {}, defaultValue = {} as T): T {
    const flag = this.getFlag(key);

    if (!flag) {
      return defaultValue;
    }

    const value = this.evaluateFlag(flag, context);
    return typeof value === 'object' ? value as T : defaultValue;
  }

  /**
   * Evaluate a feature flag
   * @param flag Feature flag
   * @param context Evaluation context
   * @returns Evaluated flag value
   */
  private evaluateFlag(flag: FeatureFlag, context: FlagContext): any {
    // If no rules, return default value
    if (!flag.rules || flag.rules.length === 0) {
      return flag.defaultValue;
    }

    // Evaluate rules in order
    for (const rule of flag.rules) {
      if (this.evaluateRule(rule, context)) {
        return rule.value;
      }
    }

    // No matching rules, return default value
    return flag.defaultValue;
  }

  /**
   * Evaluate a feature flag rule
   * @param rule Feature flag rule
   * @param context Evaluation context
   * @returns Whether the rule matches
   */
  private evaluateRule(rule: FlagRule, context: FlagContext): boolean {
    // Check environment
    if (rule.environments && rule.environments.length > 0) {
      if (!context.environment || !rule.environments.includes(context.environment)) {
        return false;
      }
    }

    // Check user IDs
    if (rule.userIds && rule.userIds.length > 0) {
      if (!context.userId || !rule.userIds.includes(context.userId)) {
        return false;
      }
    }

    // Check roles
    if (rule.roles && rule.roles.length > 0) {
      if (!context.roles) {
        return false;
      }

      const userRoles = Array.isArray(context.roles) ? context.roles : [context.roles];

      if (!rule.roles.some(role => userRoles.includes(role))) {
        return false;
      }
    }

    // Check groups
    if (rule.groups && rule.groups.length > 0) {
      if (!context.groups || !rule.groups.some(group => context.groups!.includes(group))) {
        return false;
      }
    }

    // Check percentage rollout
    if (rule.percentage !== undefined) {
      const userId = context.userId || 'anonymous';
      const hash = this.hashString(userId + rule.id);
      const normalizedHash = hash % 100;

      if (normalizedHash >= rule.percentage) {
        return false;
      }
    }

    // Check attributes
    if (rule.attributes && Object.keys(rule.attributes).length > 0) {
      if (!context.attributes) {
        return false;
      }

      for (const [key, value] of Object.entries(rule.attributes)) {
        if (context.attributes[key] !== value) {
          return false;
        }
      }
    }

    // Run custom evaluator if provided
    if (rule.evaluator) {
      return rule.evaluator(context);
    }

    // All checks passed
    return true;
  }

  /**
   * Simple hash function for consistent percentage rollouts
   * @param str String to hash
   * @returns Hash value
   */
  private hashString(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    return Math.abs(hash);
  }
}

/**
 * Feature flag manager
 */
export class FeatureFlagManager {
  private provider: FlagProvider;
  private defaultContext: FlagContext;

  /**
   * Create a feature flag manager
   * @param provider Feature flag provider
   * @param defaultContext Default context for flag evaluation
   */
  constructor(provider: FlagProvider, defaultContext: FlagContext = {}) {
    this.provider = provider;
    this.defaultContext = defaultContext;
  }

  /**
   * Set the feature flag provider
   * @param provider Feature flag provider
   */
  setProvider(provider: FlagProvider): void {
    this.provider = provider;
  }

  /**
   * Set the default context
   * @param context Default context
   */
  setDefaultContext(context: FlagContext): void {
    this.defaultContext = context;
  }

  /**
   * Update the default context
   * @param context Context updates
   */
  updateDefaultContext(context: Partial<FlagContext>): void {
    this.defaultContext = { ...this.defaultContext, ...context };
  }

  /**
   * Check if a feature is enabled
   * @param key Feature flag key
   * @param context Additional context
   * @returns Whether the feature is enabled
   */
  isEnabled(key: string, context: FlagContext = {}): boolean {
    const mergedContext = { ...this.defaultContext, ...context };
    return this.provider.getBooleanFlag(key, mergedContext, false);
  }

  /**
   * Get a feature flag value
   * @param key Feature flag key
   * @param context Additional context
   * @param defaultValue Default value if flag is not found
   * @returns Feature flag value
   */
  getValue<T>(key: string, context: FlagContext = {}, defaultValue?: any): T {
    const mergedContext = { ...this.defaultContext, ...context };
    const flag = this.provider.getFlag(key);

    if (!flag) {
      return defaultValue as T;
    }

    const flagType = typeof flag.defaultValue;

    switch (flagType) {
      case 'boolean':
        return this.provider.getBooleanFlag(key, mergedContext, defaultValue) as unknown as T;
      case 'string':
        return this.provider.getStringFlag(key, mergedContext, defaultValue) as unknown as T;
      case 'number':
        return this.provider.getNumberFlag(key, mergedContext, defaultValue) as unknown as T;
      case 'object':
        return this.provider.getJsonFlag(key, mergedContext, defaultValue) as unknown as T;
      default:
        return defaultValue as T;
    }
  }

  /**
   * Get all feature flags
   * @returns All feature flags
   */
  getAllFlags(): FeatureFlag[] {
    return this.provider.getAllFlags();
  }
}

/**
 * Create a feature flag manager from a static configuration
 * @param flags Feature flags configuration
 * @param defaultContext Default context for flag evaluation
 * @returns Feature flag manager
 */
export function createFeatureFlagManager(
  flags: Record<string, FeatureFlag> | FeatureFlag[],
  defaultContext: FlagContext = {}
): FeatureFlagManager {
  const provider = new StaticFlagProvider(flags);
  return new FeatureFlagManager(provider, defaultContext);
}

/**
 * React hook for accessing feature flags (to be documented for React projects)
 */
export const useFeatureFlag = (/* implementation will depend on React context setup */): void => {
  // This would be implemented in a React-specific version
};

// Default export for convenience
export default {
  FeatureFlagManager,
  StaticFlagProvider,
  createFeatureFlagManager,
};
