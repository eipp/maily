import { LDClient, initialize } from 'launchdarkly-js-client-sdk';
import { analyticsService } from './analytics';

interface FeatureFlag {
  name: string;
  defaultValue: boolean;
  description: string;
}

class FeatureFlagsService {
  private client: LDClient | null = null;
  private initialized = false;
  private readonly flags: FeatureFlag[] = [
    {
      name: 'new_campaign_editor',
      defaultValue: false,
      description: 'Enable new campaign editor interface',
    },
    {
      name: 'advanced_analytics',
      defaultValue: false,
      description: 'Enable advanced analytics features',
    },
    {
      name: 'ai_suggestions',
      defaultValue: false,
      description: 'Enable AI-powered content suggestions',
    },
    {
      name: 'multi_language',
      defaultValue: false,
      description: 'Enable multi-language support',
    },
    {
      name: 'a_b_testing',
      defaultValue: false,
      description: 'Enable A/B testing features',
    },
  ];

  /**
   * Initialize LaunchDarkly client
   */
  async init(userId: string, userAttributes: Record<string, any> = {}) {
    if (this.initialized) return;

    this.client = initialize(process.env.NEXT_PUBLIC_LAUNCHDARKLY_CLIENT_ID!, {
      key: userId,
      ...userAttributes,
      anonymous: !userId,
    });

    await this.client.waitForInitialization();
    this.setupFlagChangeListeners();
    this.initialized = true;
  }

  /**
   * Check if a feature is enabled
   */
  isEnabled(flagName: string): boolean {
    if (!this.client) return this.getDefaultValue(flagName);
    return this.client.variation(flagName, this.getDefaultValue(flagName));
  }

  /**
   * Get all feature flags
   */
  getAllFlags(): Record<string, boolean> {
    if (!this.client) {
      return this.flags.reduce(
        (acc, flag) => ({
          ...acc,
          [flag.name]: flag.defaultValue,
        }),
        {}
      );
    }
    return this.client.allFlags();
  }

  /**
   * Get feature flag details
   */
  getFlagDetails(flagName: string): FeatureFlag | undefined {
    return this.flags.find(flag => flag.name === flagName);
  }

  /**
   * Track feature flag evaluation
   */
  private trackFlagEvaluation(flagName: string, value: boolean) {
    analyticsService.trackEvent('feature_flag_evaluation', {
      flag_name: flagName,
      value,
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * Set up listeners for flag changes
   */
  private setupFlagChangeListeners() {
    if (!this.client) return;

    this.flags.forEach(flag => {
      this.client!.on(`change:${flag.name}`, value => {
        this.trackFlagEvaluation(flag.name, value);

        // Emit custom event for UI updates
        const event = new CustomEvent('featureFlagChanged', {
          detail: { flagName: flag.name, value },
        });
        window.dispatchEvent(event);
      });
    });
  }

  /**
   * Get default value for a flag
   */
  private getDefaultValue(flagName: string): boolean {
    const flag = this.flags.find(f => f.name === flagName);
    return flag?.defaultValue ?? false;
  }

  /**
   * Check if client is initialized
   */
  isInitialized(): boolean {
    return this.initialized;
  }

  /**
   * Update user context
   */
  async updateUser(userId: string, userAttributes: Record<string, any> = {}) {
    if (!this.client) return;
    await this.client.identify({
      key: userId,
      ...userAttributes,
    });
  }

  /**
   * Clean up resources
   */
  dispose() {
    if (this.client) {
      this.client.close();
      this.client = null;
      this.initialized = false;
    }
  }
}

export const featureFlagsService = new FeatureFlagsService();
