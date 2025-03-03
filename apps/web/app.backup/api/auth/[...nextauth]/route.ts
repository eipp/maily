import NextAuth, { NextAuthOptions } from 'next-auth';
import Auth0Provider from 'next-auth/providers/auth0';
import CredentialsProvider from 'next-auth/providers/credentials';
import { JWT } from 'next-auth/jwt';
import { refreshAccessToken, extractRolesFromToken } from '@/lib/auth';
import config from '@/lib/config';

/**
 * NextAuth.js options
 */
export const authOptions: NextAuthOptions = {
  providers: [
    // Auth0 provider
    Auth0Provider({
      clientId: process.env.AUTH0_CLIENT_ID || '',
      clientSecret: process.env.AUTH0_CLIENT_SECRET || '',
      issuer: `https://${process.env.AUTH0_DOMAIN}`,
      authorization: {
        params: {
          scope: 'openid profile email offline_access',
          audience: process.env.AUTH0_AUDIENCE,
        },
      },
    }),
    
    // Credentials provider for API key authentication
    CredentialsProvider({
      id: 'api-key',
      name: 'API Key',
      credentials: {
        apiKey: { label: 'API Key', type: 'password' },
      },
      async authorize(credentials) {
        if (!credentials?.apiKey) return null;
        
        try {
          // Validate API key with backend
          const response = await fetch(`${config.urls.api}/auth/validate-api-key`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ apiKey: credentials.apiKey }),
          });
          
          if (!response.ok) return null;
          
          const data = await response.json();
          
          return {
            id: data.id,
            email: data.email,
            name: data.name,
            isAdmin: data.is_admin,
            apiKey: credentials.apiKey,
          };
        } catch (error) {
          console.error('API key validation error:', error);
          return null;
        }
      },
    }),
  ],
  
  session: {
    strategy: 'jwt',
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  
  pages: {
    signIn: '/login',
    signOut: '/logout',
    error: '/auth/error',
  },
  
  callbacks: {
    async jwt({ token, account, user }) {
      // Initial sign in
      if (account && user) {
        // For Auth0 provider
        if (account.provider === 'auth0') {
          const roles = extractRolesFromToken(account.id_token || '');
          
          return {
            ...token,
            accessToken: account.access_token,
            refreshToken: account.refresh_token,
            accessTokenExpires: account.expires_at ? account.expires_at * 1000 : 0,
            user: {
              ...user,
              roles,
              isAdmin: roles.includes('admin'),
            },
          };
        }
        
        // For API key provider
        if (account.provider === 'api-key') {
          return {
            ...token,
            accessToken: user.apiKey,
            user: {
              ...user,
              roles: user.isAdmin ? ['admin', 'editor', 'user'] : ['user'],
            },
          };
        }
      }
      
      // Return previous token if the access token has not expired yet
      if (Date.now() < (token.accessTokenExpires as number)) {
        return token;
      }
      
      // Access token has expired, try to refresh it
      if (token.refreshToken) {
        return refreshAccessToken(token as JWT);
      }
      
      return token;
    },
    
    async session({ session, token }) {
      if (token.user) {
        session.user = token.user as any;
      }
      
      session.accessToken = token.accessToken as string;
      session.error = token.error as string | undefined;
      
      return session;
    },
  },
  
  debug: process.env.NODE_ENV === 'development',
};

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
