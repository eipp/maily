import { z } from 'zod';
import { AppConfigSchema, AppConfig } from '../types/AppConfig';

/**
 * Validation result interface
 */
export interface ValidationResult {
  /**
   * Whether the validation was successful
   */
  valid: boolean;
  
  /**
   * Validation errors, if any
   */
  errors?: Array<{
    path: string;
    message: string;
  }>;
  
  /**
   * The validated configuration, if validation was successful
   */
  config?: AppConfig;
}

/**
 * Validates a configuration object against the application schema
 * 
 * @param config - The configuration object to validate
 * @returns A validation result indicating success or failure
 */
export function validateConfig(config: unknown): ValidationResult {
  try {
    // Parse and validate the configuration
    const validatedConfig = AppConfigSchema.parse(config);
    
    return {
      valid: true,
      config: validatedConfig,
    };
  } catch (error) {
    if (error instanceof z.ZodError) {
      // Format validation errors
      const errors = error.errors.map(err => ({
        path: err.path.join('.'),
        message: err.message,
      }));
      
      return {
        valid: false,
        errors,
      };
    }
    
    // Handle unexpected errors
    return {
      valid: false,
      errors: [{
        path: '',
        message: error instanceof Error ? error.message : 'Unknown validation error',
      }],
    };
  }
}

/**
 * Validates a configuration object and throws an error if validation fails
 * 
 * @param config - The configuration object to validate
 * @returns The validated configuration
 * @throws Error if validation fails
 */
export function validateConfigStrict(config: unknown): AppConfig {
  const result = validateConfig(config);
  
  if (!result.valid) {
    throw new Error(`Configuration validation failed: ${JSON.stringify(result.errors)}`);
  }
  
  return result.config as AppConfig;
}

/**
 * Validates a partial configuration object against the application schema
 * 
 * @param config - The partial configuration object to validate
 * @returns A validation result indicating success or failure
 */
export function validatePartialConfig(config: unknown): ValidationResult {
  try {
    // Parse and validate the partial configuration
    const partialSchema = AppConfigSchema.deepPartial();
    const validatedConfig = partialSchema.parse(config);
    
    return {
      valid: true,
      config: validatedConfig as unknown as AppConfig,
    };
  } catch (error) {
    if (error instanceof z.ZodError) {
      // Format validation errors
      const errors = error.errors.map(err => ({
        path: err.path.join('.'),
        message: err.message,
      }));
      
      return {
        valid: false,
        errors,
      };
    }
    
    // Handle unexpected errors
    return {
      valid: false,
      errors: [{
        path: '',
        message: error instanceof Error ? error.message : 'Unknown validation error',
      }],
    };
  }
}