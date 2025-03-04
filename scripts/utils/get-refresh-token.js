#!/usr/bin/env node

/**
 * OAuth Refresh Token Generator
 *
 * This script helps obtain OAuth refresh tokens for various platforms.
 * It's a one-time setup tool to get the necessary tokens for Nango integration.
 *
 * Usage:
 *   node get-refresh-token.js --platform=linkedin
 *
 * Supported platforms:
 *   - linkedin
 *   - twitter
 *   - gmail
 *   - outlook
 */

const express = require('express');
const axios = require('axios');
const open = require('open');
const crypto = require('crypto');
const dotenv = require('dotenv');
const path = require('path');
const fs = require('fs');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');

// Load environment variables
dotenv.config();

// Parse command line arguments
const argv = yargs(hideBin(process.argv))
  .option('platform', {
    alias: 'p',
    description: 'Platform to get refresh token for',
    type: 'string',
    choices: ['linkedin', 'twitter', 'gmail', 'outlook'],
    demandOption: true
  })
  .help()
  .alias('help', 'h')
  .argv;

// Platform configurations
const platformConfigs = {
  linkedin: {
    name: 'LinkedIn',
    authUrl: 'https://www.linkedin.com/oauth/v2/authorization',
    tokenUrl: 'https://www.linkedin.com/oauth/v2/accessToken',
    clientId: process.env.LINKEDIN_CLIENT_ID,
    clientSecret: process.env.LINKEDIN_CLIENT_SECRET,
    scopes: ['r_liteprofile', 'r_emailaddress', 'w_member_social', 'r_organization_social'],
    redirectUri: 'http://localhost:3333/callback',
    responseType: 'code',
    grantType: 'authorization_code',
  },
  twitter: {
    name: 'Twitter',
    authUrl: 'https://twitter.com/i/oauth2/authorize',
    tokenUrl: 'https://api.twitter.com/2/oauth2/token',
    clientId: process.env.TWITTER_CLIENT_ID,
    clientSecret: process.env.TWITTER_CLIENT_SECRET,
    scopes: ['tweet.read', 'tweet.write', 'users.read', 'follows.read'],
    redirectUri: 'http://localhost:3333/callback',
    responseType: 'code',
    grantType: 'authorization_code',
    codeChallenge: true,
  },
  gmail: {
    name: 'Gmail',
    authUrl: 'https://accounts.google.com/o/oauth2/v2/auth',
    tokenUrl: 'https://oauth2.googleapis.com/token',
    clientId: process.env.GMAIL_CLIENT_ID,
    clientSecret: process.env.GMAIL_CLIENT_SECRET,
    scopes: ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/contacts.readonly'],
    redirectUri: 'http://localhost:3333/callback',
    responseType: 'code',
    grantType: 'authorization_code',
    accessType: 'offline',
    prompt: 'consent',
  },
  outlook: {
    name: 'Outlook',
    authUrl: 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
    tokenUrl: 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
    clientId: process.env.OUTLOOK_CLIENT_ID,
    clientSecret: process.env.OUTLOOK_CLIENT_SECRET,
    scopes: ['offline_access', 'Mail.Read', 'Mail.Send', 'Contacts.Read'],
    redirectUri: 'http://localhost:3333/callback',
    responseType: 'code',
    grantType: 'authorization_code',
  },
};

// Get platform config
const platform = argv.platform;
const config = platformConfigs[platform];

if (!config) {
  console.error(`Unsupported platform: ${platform}`);
  process.exit(1);
}

// Check for required environment variables
if (!config.clientId || !config.clientSecret) {
  console.error(`Missing environment variables for ${config.name}. Please set ${platform.toUpperCase()}_CLIENT_ID and ${platform.toUpperCase()}_CLIENT_SECRET in your .env file.`);
  process.exit(1);
}

// Create Express app
const app = express();
const PORT = 3333;

// Generate PKCE code verifier and challenge (for platforms that require it)
const codeVerifier = crypto.randomBytes(64).toString('hex');
const codeChallenge = crypto.createHash('sha256').update(codeVerifier).digest('base64')
  .replace(/\+/g, '-')
  .replace(/\//g, '_')
  .replace(/=/g, '');

// Generate state parameter to prevent CSRF
const state = crypto.randomBytes(16).toString('hex');

// Build authorization URL
function buildAuthUrl() {
  const params = new URLSearchParams({
    client_id: config.clientId,
    redirect_uri: config.redirectUri,
    response_type: config.responseType,
    scope: config.scopes.join(' '),
    state: state,
  });

  // Add platform-specific parameters
  if (config.codeChallenge) {
    params.append('code_challenge', codeChallenge);
    params.append('code_challenge_method', 'S256');
  }

  if (config.accessType) {
    params.append('access_type', config.accessType);
  }

  if (config.prompt) {
    params.append('prompt', config.prompt);
  }

  return `${config.authUrl}?${params.toString()}`;
}

// Handle callback
app.get('/callback', async (req, res) => {
  const { code, state: returnedState, error } = req.query;

  // Check for errors
  if (error) {
    res.send(`<h1>Error</h1><p>${error}</p>`);
    return;
  }

  // Verify state parameter
  if (returnedState !== state) {
    res.send('<h1>Error</h1><p>Invalid state parameter. Possible CSRF attack.</p>');
    return;
  }

  try {
    // Exchange authorization code for tokens
    const tokenParams = new URLSearchParams({
      client_id: config.clientId,
      client_secret: config.clientSecret,
      code: code,
      redirect_uri: config.redirectUri,
      grant_type: config.grantType,
    });

    // Add code verifier for PKCE
    if (config.codeChallenge) {
      tokenParams.append('code_verifier', codeVerifier);
    }

    const tokenResponse = await axios.post(config.tokenUrl, tokenParams.toString(), {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    const { access_token, refresh_token, expires_in } = tokenResponse.data;

    // Display tokens
    res.send(`
      <h1>${config.name} OAuth Successful</h1>
      <p>You can now close this window and return to the terminal.</p>
      <script>window.close();</script>
    `);

    // Log tokens to console
    console.log('\n=== OAuth Flow Completed Successfully ===');
    console.log(`Platform: ${config.name}`);
    console.log(`Access Token: ${access_token}`);
    console.log(`Refresh Token: ${refresh_token}`);
    console.log(`Expires In: ${expires_in} seconds`);
    console.log('\nAdd these values to your Nango configuration:');
    console.log(`NANGO_${platform.toUpperCase()}_REFRESH_TOKEN=${refresh_token}`);

    // Save to .env.local
    const envLocalPath = path.join(process.cwd(), '.env.local');
    let envContent = '';

    try {
      if (fs.existsSync(envLocalPath)) {
        envContent = fs.readFileSync(envLocalPath, 'utf8');
      }
    } catch (err) {
      // File doesn't exist, will create it
    }

    // Add or update the refresh token
    const envVarName = `NANGO_${platform.toUpperCase()}_REFRESH_TOKEN`;
    const envVarRegex = new RegExp(`^${envVarName}=.*$`, 'm');

    if (envVarRegex.test(envContent)) {
      // Update existing variable
      envContent = envContent.replace(envVarRegex, `${envVarName}=${refresh_token}`);
    } else {
      // Add new variable
      envContent += `\n${envVarName}=${refresh_token}`;
    }

    fs.writeFileSync(envLocalPath, envContent);
    console.log(`\nRefresh token saved to ${envLocalPath}`);

    // Exit after a short delay
    setTimeout(() => {
      process.exit(0);
    }, 1000);
  } catch (error) {
    console.error('Error exchanging code for tokens:', error.response?.data || error.message);
    res.send(`<h1>Error</h1><p>Failed to exchange code for tokens: ${error.message}</p>`);
  }
});

// Start server and open browser
app.listen(PORT, () => {
  console.log(`\n=== ${config.name} OAuth Flow ===`);
  console.log(`Server running at http://localhost:${PORT}`);
  console.log('Opening browser for authorization...');

  const authUrl = buildAuthUrl();
  console.log(`\nAuthorization URL: ${authUrl}\n`);

  // Open browser
  open(authUrl).catch(() => {
    console.log('Could not open browser automatically. Please open the URL manually.');
  });
});
