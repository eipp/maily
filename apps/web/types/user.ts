/**
 * User type definitions for the application
 * Contains all user-related interfaces and types used throughout the frontend
 */

/**
 * User roles available in the system
 */
export enum UserRole {
  ADMIN = 'ADMIN',
  EDITOR = 'EDITOR',
  USER = 'USER',
  VIEWER = 'VIEWER',
}

/**
 * User permission types - used for fine-grained access control
 */
export enum UserPermission {
  // Campaign permissions
  CREATE_CAMPAIGN = 'campaign:create',
  EDIT_CAMPAIGN = 'campaign:edit',
  DELETE_CAMPAIGN = 'campaign:delete',
  VIEW_CAMPAIGN = 'campaign:view',
  SEND_CAMPAIGN = 'campaign:send',

  // User management permissions
  MANAGE_USERS = 'users:manage',
  INVITE_USERS = 'users:invite',
  DELETE_USERS = 'users:delete',
  VIEW_USERS = 'users:view',

  // Template permissions
  CREATE_TEMPLATE = 'template:create',
  EDIT_TEMPLATE = 'template:edit',
  DELETE_TEMPLATE = 'template:delete',
  VIEW_TEMPLATE = 'template:view',

  // Analytics permissions
  VIEW_ANALYTICS = 'analytics:view',
  EXPORT_ANALYTICS = 'analytics:export',

  // System permissions
  MANAGE_SETTINGS = 'settings:manage',
  VIEW_SETTINGS = 'settings:view',
  MANAGE_BILLING = 'billing:manage',
  VIEW_BILLING = 'billing:view',
}

/**
 * Core user interface representing a user in the system
 */
export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole | string;
  permissions?: UserPermission[] | string[];
  avatar?: string | null;
  organization?: {
    id: string;
    name: string;
    role?: string;
  };
  metadata?: Record<string, any>;
  createdAt?: string | Date;
  updatedAt?: string | Date;
  lastLogin?: string | Date;
  isActive?: boolean;
  isSuspended?: boolean;
  isEmailVerified?: boolean;
  twoFactorEnabled?: boolean;
}

/**
 * User profile - extended user information
 */
export interface UserProfile extends User {
  jobTitle?: string;
  department?: string;
  location?: string;
  phoneNumber?: string;
  bio?: string;
  socialLinks?: {
    twitter?: string;
    linkedin?: string;
    github?: string;
    website?: string;
  };
  preferences?: {
    theme?: 'light' | 'dark' | 'system';
    emailNotifications?: boolean;
    pushNotifications?: boolean;
    weeklyDigest?: boolean;
    timezone?: string;
    language?: string;
  };
}

/**
 * User creation request payload
 */
export interface CreateUserRequest {
  email: string;
  name: string;
  password?: string;
  role: UserRole | string;
  permissions?: UserPermission[] | string[];
  organization?: string;
  metadata?: Record<string, any>;
}

/**
 * User update request payload
 */
export interface UpdateUserRequest {
  name?: string;
  email?: string;
  role?: UserRole | string;
  permissions?: UserPermission[] | string[];
  isActive?: boolean;
  metadata?: Record<string, any>;
}

/**
 * User with auth token
 */
export interface AuthenticatedUser {
  user: User;
  token: string;
  refreshToken?: string;
  tokenExpiry?: number;
}

/**
 * User login credentials
 */
export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

/**
 * Registration information
 */
export interface RegisterData extends LoginCredentials {
  name: string;
  confirmPassword: string;
  termsAccepted: boolean;
  marketingOptIn?: boolean;
}

/**
 * Map of role to permissions
 */
export const DEFAULT_ROLE_PERMISSIONS: Record<UserRole, UserPermission[]> = {
  [UserRole.ADMIN]: Object.values(UserPermission),
  [UserRole.EDITOR]: [
    UserPermission.CREATE_CAMPAIGN,
    UserPermission.EDIT_CAMPAIGN,
    UserPermission.VIEW_CAMPAIGN,
    UserPermission.SEND_CAMPAIGN,
    UserPermission.CREATE_TEMPLATE,
    UserPermission.EDIT_TEMPLATE,
    UserPermission.VIEW_TEMPLATE,
    UserPermission.VIEW_ANALYTICS,
    UserPermission.VIEW_USERS,
    UserPermission.VIEW_SETTINGS,
  ],
  [UserRole.USER]: [
    UserPermission.CREATE_CAMPAIGN,
    UserPermission.EDIT_CAMPAIGN,
    UserPermission.VIEW_CAMPAIGN,
    UserPermission.VIEW_TEMPLATE,
    UserPermission.VIEW_ANALYTICS,
  ],
  [UserRole.VIEWER]: [
    UserPermission.VIEW_CAMPAIGN,
    UserPermission.VIEW_TEMPLATE,
    UserPermission.VIEW_ANALYTICS,
  ],
};
