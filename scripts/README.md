# Maily Scripts

This directory contains utility scripts for managing and maintaining the Maily project.

## Documentation Scripts

### Documentation Consolidation Scripts

These scripts assist with the documentation consolidation process:

#### `verify-doc-links.js`

Verifies internal links between markdown documentation files:
- Checks that all document links point to existing files
- Verifies that heading links (`#heading-references`) point to valid headings
- Generates a report of any broken links

Usage:
```bash
node scripts/verify-doc-links.js
```

#### `cleanup-docs.js`

Helps with cleanup of deprecated documentation files after consolidation:
- Reads the file removal list from `docs/documentation-consolidation-progress.md`
- Archives files to a `docs/archive` directory instead of deleting them
- Generates a detailed report of the cleanup process

Usage:
```bash
node scripts/cleanup-docs.js
```

#### `complete-docs-consolidation.sh`

Automates the entire documentation consolidation completion process. This shell script:

- Runs link verification to check for broken references
- Archives deprecated files based on the consolidation progress document
- Builds the documentation portal with the updated navigation
- Performs a final verification to ensure everything is working

Usage:
```
./scripts/complete-docs-consolidation.sh
```

#### update-consolidation-progress.js

Updates the documentation consolidation progress tracking document. This script:

- Marks all in-progress consolidation tasks as completed with today's date
- Moves completed items from the "In-Progress" to the "Completed" section
- Updates progress metrics to reflect 100% completion
- Changes the overall status from "In Progress" to "Completed"

Usage:
```
node scripts/update-consolidation-progress.js
```

## Development Scripts

[Existing development scripts documentation...]

## Deployment Scripts

[Existing deployment scripts documentation...]

## Maintenance Scripts

[Existing maintenance scripts documentation...]

## OAuth Refresh Token Generator

The `get-refresh-token.js` script helps you obtain OAuth refresh tokens for various platforms. These tokens are used by Nango to authenticate with third-party services.

### Prerequisites

Before using the script, install the required dependencies:

```bash
cd scripts
npm install
```

### Usage

To get a refresh token for a specific platform:

```bash
node get-refresh-token.js --platform=<platform>
```

Or using the npm script:

```bash
npm run get-token -- --platform=<platform>
```

Replace `<platform>` with one of the supported platforms:
- `linkedin`
- `twitter`
- `gmail`
- `outlook`

### Example

```bash
# Get a refresh token for LinkedIn
node get-refresh-token.js --platform=linkedin
```

### How It Works

1. The script starts a local web server on port 3333
2. It opens your default browser to the platform's OAuth authorization page
3. After you authorize the application, the platform redirects back to the local server
4. The script exchanges the authorization code for access and refresh tokens
5. The refresh token is displayed in the console and saved to `.env.local`

### Environment Variables

Before running the script, make sure you have the following environment variables set in your `.env` file:

For LinkedIn:
```
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
```

For Twitter:
```
TWITTER_CLIENT_ID=your_twitter_client_id
TWITTER_CLIENT_SECRET=your_twitter_client_secret
```

For Gmail:
```
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret
```

For Outlook:
```
OUTLOOK_CLIENT_ID=your_outlook_client_id
OUTLOOK_CLIENT_SECRET=your_outlook_client_secret
```

### Troubleshooting

1. **"Could not open browser automatically"**: If the script can't open your browser, manually copy and paste the authorization URL displayed in the console.

2. **"Missing environment variables"**: Make sure you've set the required client ID and secret in your `.env` file.

3. **"Invalid redirect URI"**: Ensure that the redirect URI (`http://localhost:3333/callback`) is registered in the developer console for the platform you're using.

4. **"Access denied"**: Check that your application has the necessary permissions and that you're using the correct account.
