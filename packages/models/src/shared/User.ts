/**
 * Standardized User model for use across all Maily services
 * 
 * This model represents user data and is intended to be used by any service
 * that needs to interact with user information.
 */

import { z } from 'zod';

/**
 * User roles available in the system
 */
export enum UserRole {
  ADMIN = 'admin',
  EDITOR = 'editor',
  VIEWER = 'viewer',
  ANALYST = 'analyst',
}

/**
 * User status states
 */
export enum UserStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended',
  PENDING_VERIFICATION = 'pending_verification',
}

/**
 * User preferences schema definition
 */
export const UserPreferencesSchema = z.object({
  theme: z.enum(['light', 'dark', 'system']).default('system'),
  emailFrequency: z.enum(['daily', 'weekly', 'monthly', 'none']).default('weekly'),
  timezone: z.string().default('UTC'),
  notificationSettings: z.object({
    email: z.boolean().default(true),
    inApp: z.boolean().default(true),
    mobile: z.boolean().default(false),
  }).optional(),
  defaultLanguage: z.string().default('en'),
});

/**
 * User model schema definition
 */
export const UserSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  firstName: z.string().min(1).max(100),
  lastName: z.string().min(1).max(100),
  fullName: z.string().min(1).max(200).optional(),
  status: z.nativeEnum(UserStatus).default(UserStatus.PENDING_VERIFICATION),
  roles: z.array(z.nativeEnum(UserRole)).default([UserRole.VIEWER]),
  createdAt: z.date(),
  updatedAt: z.date(),
  lastLogin: z.date().optional(),
  preferences: UserPreferencesSchema.optional(),
  metadata: z.record(z.string(), z.any()).optional(),
  // Fields used for authentication
  auth: z.object({
    authId: z.string().optional(), // External auth provider ID
    provider: z.enum(['email', 'google', 'microsoft', 'github']).default('email'),
    isEmailVerified: z.boolean().default(false),
    passwordLastChanged: z.date().optional(),
    mfaEnabled: z.boolean().default(false),
  }).optional(),
  organizationId: z.string().uuid().optional(),
});

/**
 * Type definitions derived from the schemas
 */
export type UserPreferences = z.infer<typeof UserPreferencesSchema>;
export type User = z.infer<typeof UserSchema>;

/**
 * Helper functions for working with User objects
 */
export const UserHelpers = {
  /**
   * Creates the full name from first and last name
   */
  getFullName: (user: User): string => {
    return `${user.firstName} ${user.lastName}`;
  },

  /**
   * Check if user has a specific role
   */
  hasRole: (user: User, role: UserRole): boolean => {
    return user.roles.includes(role);
  },

  /**
   * Check if user is active
   */
  isActive: (user: User): boolean => {
    return user.status === UserStatus.ACTIVE;
  },

  /**
   * Creates a default user object
   */
  createDefault: (email: string, firstName: string, lastName: string): User => {
    return {
      id: crypto.randomUUID(),
      email,
      firstName,
      lastName,
      fullName: `${firstName} ${lastName}`,
      status: UserStatus.PENDING_VERIFICATION,
      roles: [UserRole.VIEWER],
      createdAt: new Date(),
      updatedAt: new Date(),
      auth: {
        provider: 'email',
        isEmailVerified: false,
        mfaEnabled: false
      }
    };
  }
};

export default User;