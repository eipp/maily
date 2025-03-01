/**
 * ID generation utility functions
 */

/**
 * Generate a UUID v4
 * @returns UUID v4 string
 */
export function uuid(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * UUID validation
 * @param id UUID to validate
 * @returns Whether the string is a valid UUID
 */
export function isUuid(id: string): boolean {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(id);
}

/**
 * Generate a short ID (nanoid-style)
 * @param length ID length
 * @param alphabet Characters to use
 * @returns Short unique ID
 */
export function shortId(
  length: number = 21,
  alphabet: string = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
): string {
  let id = '';
  const alphabetLength = alphabet.length;

  for (let i = 0; i < length; i++) {
    id += alphabet.charAt(Math.floor(Math.random() * alphabetLength));
  }

  return id;
}

/**
 * Generate a sequential ID with prefix
 * @param prefix Prefix for the ID
 * @param counter Current counter value
 * @param padding Zero padding for the counter
 * @returns Sequential ID
 */
export function sequentialId(
  prefix: string,
  counter: number,
  padding: number = 6
): string {
  return `${prefix}${counter.toString().padStart(padding, '0')}`;
}

/**
 * Generate a time-based ID
 * @param prefix Prefix for the ID
 * @returns Time-based ID
 */
export function timeId(prefix: string = ''): string {
  const timestamp = Date.now().toString(36);
  const randomPart = Math.random().toString(36).substring(2, 7);
  return `${prefix}${timestamp}${randomPart}`;
}

/**
 * Generate a slug from a string
 * @param input Input string
 * @param separator Separator for words
 * @returns Slug string
 */
export function slugify(
  input: string,
  separator: string = '-'
): string {
  return input
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_]+/g, separator)
    .replace(new RegExp(`${separator}+`, 'g'), separator);
}

/**
 * Generate a hash code for a string
 * @param str String to hash
 * @returns Hash code
 */
export function hashCode(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash |= 0; // Convert to 32-bit integer
  }
  return hash;
}

/**
 * Generate an objectId similar to MongoDB
 * @returns MongoDB-like ObjectId
 */
export function objectId(): string {
  const timestamp = Math.floor(Date.now() / 1000).toString(16).padStart(8, '0');
  const machineId = Math.floor(Math.random() * 16777216).toString(16).padStart(6, '0');
  const processId = Math.floor(Math.random() * 65536).toString(16).padStart(4, '0');
  const counter = Math.floor(Math.random() * 16777216).toString(16).padStart(6, '0');

  return timestamp + machineId + processId + counter;
}

/**
 * Generate a cuid (collision-resistant id)
 * @returns Cuid string
 */
export function cuid(): string {
  const timestamp = Date.now().toString(36);
  const counter = getNextCounter().toString(36);
  const random = Math.random().toString(36).substring(2, 8);
  const fingerprint = getFingerprint();

  return 'c' + timestamp + counter + fingerprint + random;
}

// Counter for cuid
let counter = Math.floor(Math.random() * 1000);

/**
 * Get next counter value for cuid
 * @returns Next counter value
 */
function getNextCounter(): number {
  return counter++;
}

/**
 * Generate fingerprint for cuid
 * @returns Fingerprint string
 */
function getFingerprint(): string {
  // Simple fingerprint generation
  const pad = (str: string, len: number = 2): string => {
    return str.length < len ? pad('0' + str, len) : str;
  };

  // Generate host fingerprint (simplified)
  const hostname = typeof window !== 'undefined'
    ? window.location.host
    : 'nodejs';

  const hostPart = pad(hashCode(hostname).toString(36));
  const processPart = pad(Math.floor(Math.random() * 256).toString(36));

  return hostPart + processPart;
}

/**
 * Generate a unique ID combining multiple sources of randomness
 * @param prefix Optional prefix for the ID
 * @returns Unique ID
 */
export function uniqueId(prefix: string = ''): string {
  return prefix + [
    Date.now().toString(36),
    Math.random().toString(36).substring(2, 15),
    Math.random().toString(36).substring(2, 15),
  ].join('');
}

/**
 * Generate a shareable ID (shorter and URL-friendly)
 * @param length ID length
 * @returns Shareable ID
 */
export function shareableId(length: number = 10): string {
  // Use only URL-friendly characters
  return shortId(length, '23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz');
}

/**
 * Generate a push ID (Firebase-style)
 * @returns Push ID
 */
export function pushId(): string {
  // Characters used in push IDs
  const PUSH_CHARS = '-0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz';

  // Timestamp portion
  let nowValue = Date.now();
  const timeStampChars = new Array(8);

  for (let i = 7; i >= 0; i--) {
    timeStampChars[i] = PUSH_CHARS.charAt(nowValue % 64);
    nowValue = Math.floor(nowValue / 64);
  }

  // Random portion
  const randomChars = new Array(12);

  for (let i = 0; i < 12; i++) {
    randomChars[i] = PUSH_CHARS.charAt(Math.floor(Math.random() * 64));
  }

  return timeStampChars.join('') + randomChars.join('');
}

/**
 * Generate a version 5 UUID (namespace-based)
 * @param name Name to hash
 * @param namespace Namespace UUID
 * @returns UUID v5 string
 */
export function uuidv5(
  name: string,
  namespace: string = '6ba7b810-9dad-11d1-80b4-00c04fd430c8' // DNS namespace
): string {
  // Simple implementation - for production use a full UUID library
  const hash = hashCode(namespace + name);

  // Format as UUID v5
  return 'xxxxxxxx-xxxx-5xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (hash + Math.random() * 16) % 16 | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}
