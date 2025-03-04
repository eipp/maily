/** 
 * Next.js configuration (redirected to standardized config)
 * 
 * This file imports the standardized Next.js configuration from the centralized location.
 * All configuration should be defined in config/app/web/next.config.js.
 */

const path = require('path');
const standardConfigPath = path.join(__dirname, '../../config/app/web/next.config.js');

// Display a warning that this is using the standardized config
console.log('\x1b[33m%s\x1b[0m', `Using standardized Next.js configuration from ${standardConfigPath}`);

// Import and re-export the standardized config
module.exports = require(standardConfigPath);