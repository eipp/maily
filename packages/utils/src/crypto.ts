/**
 * Cryptography utility functions
 */

/**
 * Hash algorithm options
 */
export enum HashAlgorithm {
  SHA1 = 'SHA-1',
  SHA256 = 'SHA-256',
  SHA384 = 'SHA-384',
  SHA512 = 'SHA-512',
  MD5 = 'MD5',
}

/**
 * Generate a hash of a string using Web Crypto API
 * @param data Data to hash
 * @param algorithm Hash algorithm to use
 * @returns Promise resolving to hash as hex string
 */
export async function hash(
  data: string,
  algorithm: HashAlgorithm = HashAlgorithm.SHA256
): Promise<string> {
  // Use TextEncoder to convert string to Uint8Array
  const encoder = new TextEncoder();
  const dataBuffer = encoder.encode(data);

  // Hash the data
  const hashBuffer = await crypto.subtle.digest(algorithm, dataBuffer);

  // Convert buffer to byte array
  const hashArray = Array.from(new Uint8Array(hashBuffer));

  // Convert bytes to hex string
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

/**
 * Generate a simple hash code (non-cryptographic)
 * @param data String to hash
 * @returns Hash code
 */
export function simpleHash(data: string): number {
  let hash = 0;

  if (data.length === 0) {
    return hash;
  }

  for (let i = 0; i < data.length; i++) {
    const char = data.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }

  return hash;
}

/**
 * Compare two strings in constant time
 * @param a First string
 * @param b Second string
 * @returns Whether strings are equal
 */
export function constantTimeCompare(a: string, b: string): boolean {
  if (a.length !== b.length) {
    return false;
  }

  let result = 0;
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }

  return result === 0;
}

/**
 * Generate a random token
 * @param length Token length
 * @returns Random token
 */
export function generateToken(length: number = 32): string {
  const array = new Uint8Array(length);
  crypto.getRandomValues(array);

  return Array.from(array)
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}

/**
 * Generate a random string using crypto-secure random values
 * @param length String length
 * @param charset Character set to use
 * @returns Random string
 */
export function randomString(
  length: number = 16,
  charset: string = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
): string {
  const array = new Uint8Array(length);
  crypto.getRandomValues(array);

  const charsetLength = charset.length;
  return Array.from(array)
    .map(b => charset.charAt(b % charsetLength))
    .join('');
}

/**
 * HMAC signing options
 */
export interface HmacOptions {
  /**
   * Hash algorithm to use
   */
  algorithm?: HashAlgorithm;

  /**
   * Output format
   */
  format?: 'hex' | 'base64';
}

/**
 * Create an HMAC signature
 * @param message Message to sign
 * @param key Signing key
 * @param options HMAC options
 * @returns Promise resolving to HMAC signature
 */
export async function hmacSign(
  message: string,
  key: string,
  options: HmacOptions = {}
): Promise<string> {
  const { algorithm = HashAlgorithm.SHA256, format = 'hex' } = options;

  // Create key from password
  const encoder = new TextEncoder();
  const keyData = encoder.encode(key);
  const messageData = encoder.encode(message);

  // Import the key
  const cryptoKey = await crypto.subtle.importKey(
    'raw',
    keyData,
    { name: 'HMAC', hash: { name: algorithm } },
    false,
    ['sign']
  );

  // Sign the message
  const signature = await crypto.subtle.sign('HMAC', cryptoKey, messageData);

  // Format output
  if (format === 'hex') {
    const hashArray = Array.from(new Uint8Array(signature));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  } else {
    // base64
    return btoa(String.fromCharCode(...new Uint8Array(signature)));
  }
}

/**
 * Verify an HMAC signature
 * @param message Original message
 * @param signature Signature to verify
 * @param key Signing key
 * @param options HMAC options
 * @returns Promise resolving to verification result
 */
export async function hmacVerify(
  message: string,
  signature: string,
  key: string,
  options: HmacOptions = {}
): Promise<boolean> {
  const computedSignature = await hmacSign(message, key, options);
  return constantTimeCompare(signature, computedSignature);
}

/**
 * Generate a base64 string from a UTF-8 string
 * @param str String to encode
 * @returns Base64-encoded string
 */
export function base64Encode(str: string): string {
  // Use TextEncoder for UTF-8 encoding
  const encoder = new TextEncoder();
  const data = encoder.encode(str);

  // Convert to base64
  return btoa(String.fromCharCode(...data));
}

/**
 * Decode a base64 string to a UTF-8 string
 * @param base64 Base64-encoded string
 * @returns Decoded UTF-8 string
 */
export function base64Decode(base64: string): string {
  // Decode base64 to binary string
  const binaryString = atob(base64);

  // Convert to Uint8Array
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }

  // Decode UTF-8
  const decoder = new TextDecoder();
  return decoder.decode(bytes);
}

/**
 * Base64 URL-safe encode a string
 * @param str String to encode
 * @returns Base64 URL-safe string
 */
export function base64UrlEncode(str: string): string {
  return base64Encode(str)
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

/**
 * Decode a Base64 URL-safe string
 * @param base64url Base64 URL-safe string
 * @returns Decoded string
 */
export function base64UrlDecode(base64url: string): string {
  // Restore missing padding
  let base64 = base64url.replace(/-/g, '+').replace(/_/g, '/');
  const pad = base64.length % 4;
  if (pad) {
    base64 += '='.repeat(4 - pad);
  }

  return base64Decode(base64);
}

/**
 * Generate a secure password
 * @param options Password generation options
 * @returns Secure password
 */
export function generatePassword(
  options: {
    length?: number;
    includeUppercase?: boolean;
    includeLowercase?: boolean;
    includeNumbers?: boolean;
    includeSymbols?: boolean;
    excludeSimilarCharacters?: boolean;
  } = {}
): string {
  const {
    length = 16,
    includeUppercase = true,
    includeLowercase = true,
    includeNumbers = true,
    includeSymbols = true,
    excludeSimilarCharacters = false,
  } = options;

  // Define character sets
  let uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  let lowercase = 'abcdefghijklmnopqrstuvwxyz';
  let numbers = '0123456789';
  let symbols = '!@#$%^&*()_+~`|}{[]:;?><,./-=';

  // Remove similar characters if requested
  if (excludeSimilarCharacters) {
    uppercase = uppercase.replace(/[IO]/g, '');
    lowercase = lowercase.replace(/[l]/g, '');
    numbers = numbers.replace(/[10]/g, '');
  }

  // Build charset based on options
  let charset = '';
  if (includeUppercase) charset += uppercase;
  if (includeLowercase) charset += lowercase;
  if (includeNumbers) charset += numbers;
  if (includeSymbols) charset += symbols;

  // Default to alphanumeric if nothing selected
  if (!charset) {
    charset = uppercase + lowercase + numbers;
  }

  // Generate password
  return randomString(length, charset);
}

/**
 * Check password strength
 * @param password Password to check
 * @returns Score (0-4) and feedback
 */
export function checkPasswordStrength(
  password: string
): { score: number; feedback: string } {
  if (!password) {
    return { score: 0, feedback: 'Password is empty' };
  }

  let score = 0;
  const feedback: string[] = [];

  // Length check
  if (password.length < 8) {
    feedback.push('Password is too short');
  } else {
    score += Math.min(2, Math.floor(password.length / 10));
  }

  // Character variety checks
  if (/[a-z]/.test(password)) score += 1;
  if (/[A-Z]/.test(password)) score += 1;
  if (/[0-9]/.test(password)) score += 1;
  if (/[^a-zA-Z0-9]/.test(password)) score += 1;

  // Bonus for mixing character types
  const varietyCount = [
    /[a-z]/.test(password),
    /[A-Z]/.test(password),
    /[0-9]/.test(password),
    /[^a-zA-Z0-9]/.test(password),
  ].filter(Boolean).length;

  if (varietyCount >= 3) score += 1;

  // Check character variety
  if (!(/[a-z]/.test(password))) feedback.push('Add lowercase letters');
  if (!(/[A-Z]/.test(password))) feedback.push('Add uppercase letters');
  if (!(/[0-9]/.test(password))) feedback.push('Add numbers');
  if (!(/[^a-zA-Z0-9]/.test(password))) feedback.push('Add special characters');

  // Normalize score to 0-4 range
  score = Math.min(4, score);

  // Generate feedback based on score
  let mainFeedback: string;
  if (score === 0) mainFeedback = 'Very weak';
  else if (score === 1) mainFeedback = 'Weak';
  else if (score === 2) mainFeedback = 'Fair';
  else if (score === 3) mainFeedback = 'Good';
  else mainFeedback = 'Strong';

  return {
    score,
    feedback: feedback.length ? `${mainFeedback}. ${feedback.join('. ')}` : mainFeedback,
  };
}
