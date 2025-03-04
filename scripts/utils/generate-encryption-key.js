#!/usr/bin/env node

/**
 * This script generates a secure encryption key for use with the API key encryption.
 * Run this script with: node scripts/generate-encryption-key.js
 */

const crypto = require('crypto');

// Generate a 32-byte (256-bit) key and encode it as base64
const encryptionKey = crypto.randomBytes(32).toString('base64');

console.log('Generated Encryption Key:');
console.log(encryptionKey);
console.log('\nAdd this to your .env file as:');
console.log(`ENCRYPTION_KEY="${encryptionKey}"`);
console.log('\nKeep this key secure and do not share it!');
console.log('If you lose this key, you will not be able to decrypt any stored API keys.');
