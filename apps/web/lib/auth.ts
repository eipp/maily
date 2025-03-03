/**
 * Authentication utilities for JustMaily
 */
import { JWT } from 'next-auth/jwt';
import config from './config';

// Types
export type UserRole = 'user' | 'editor' | 'admin';

export interface User {
  id: string;
  email: string;
  name?: string;
  image?: string;
  roles: UserRole[];
  isAdmin: boolean;
}

export interface Session {
  user: User;
  accessToken: string;
  refreshToken?: string;
  error?: string;
}

/**
 * Check if a user has a specific role
 */
export function hasRole(user: User | undefined | null, role: UserRole): boolean {
  if (!user) return false;
  return user.roles.includes(role) || user.isAdmin;
}

/**
 * Check if a user has admin privileges
 */
export function isAdmin(user: User | undefined | null): boolean {
  if (!user) return false;
  return user.isAdmin;
}

/**
 * Get the Auth0 login URL
 */
export function getLoginUrl(redirectUri?: string): string {
  const params = new URLSearchParams({
    response_type: 'code',
    client_id: process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID || '',
    redirect_uri: redirectUri || `${config.urls.app}/api/auth/callback/auth0`,
    scope: 'openid profile email',
  });

  return `https://${process.env.NEXT_PUBLIC_AUTH0_DOMAIN}/authorize?${params.toString()}`;
}

/**
 * Get the Auth0 logout URL
 */
export function getLogoutUrl(redirectUri?: string): string {
  const params = new URLSearchParams({
    client_id: process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID || '',
    returnTo: redirectUri || config.urls.app,
  });

  return `https://${process.env.NEXT_PUBLIC_AUTH0_DOMAIN}/v2/logout?${params.toString()}`;
}

/**
 * Refresh an access token using the refresh token
 */
export async function refreshAccessToken(token: JWT): Promise<JWT> {
  try {
    const response = await fetch(`https://${process.env.NEXT_PUBLIC_AUTH0_DOMAIN}/oauth/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        grant_type: 'refresh_token',
        client_id: process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID,
        client_secret: process.env.AUTH0_CLIENT_SECRET,
        refresh_token: token.refreshToken,
      }),
    });

    const refreshedTokens = await response.json();

    if (!response.ok) {
      throw refreshedTokens;
    }

    return {
      ...token,
      accessToken: refreshedTokens.access_token,
      accessTokenExpires: Date.now() + refreshedTokens.expires_in * 1000,
      refreshToken: refreshedTokens.refresh_token ?? token.refreshToken,
    };
  } catch (error) {
    console.error('Error refreshing access token:', error);
    
    return {
      ...token,
      error: 'RefreshAccessTokenError',
    };
  }
}

/**
 * Parse JWT token to extract user information
 */
export function parseJwt(token: string): any {
  try {
    return JSON.parse(atob(token.split('.')[1]));
  } catch (e) {
    return null;
  }
}

/**
 * Extract roles from Auth0 token
 */
export function extractRolesFromToken(token: string): UserRole[] {
  try {
    const decoded = parseJwt(token);
    if (!decoded) return [];
    
    // Auth0 stores roles in different places depending on the token type
    const permissions = decoded.permissions || [];
    const roles = decoded.roles || decoded['https://justmaily.com/roles'] || [];
    
    // Map Auth0 roles to our application roles
    const userRoles: UserRole[] = [];
    
    if (roles.includes('admin') || permissions.includes('admin')) {
      userRoles.push('admin');
    }
    
    if (roles.includes('editor') || permissions.includes('write:campaigns')) {
      userRoles.push('editor');
    }
    
    // Everyone gets the user role
    userRoles.push('user');
    
    return userRoles;
  } catch (e) {
    console.error('Error extracting roles from token:', e);
    return ['user'];
  }
}
