import crypto from 'crypto';

// The encryption key should be stored as an environment variable
// This is a 32-byte key (256 bits) encoded as base64
const ENCRYPTION_KEY = process.env.ENCRYPTION_KEY;

if (!ENCRYPTION_KEY) {
  console.error('ENCRYPTION_KEY environment variable is not set!');
  // In production, you might want to throw an error here
}

// Convert the base64 key to a Buffer
const getKeyBuffer = () => {
  if (!ENCRYPTION_KEY) {
    throw new Error('Encryption key is not configured');
  }
  return Buffer.from(ENCRYPTION_KEY, 'base64');
};

/**
 * Encrypts a string using AES-256-GCM
 * @param text The text to encrypt
 * @returns The encrypted text as a base64 string with IV and auth tag
 */
export async function encrypt(text: string): Promise<string> {
  // Generate a random initialization vector
  const iv = crypto.randomBytes(16);

  // Create a cipher using AES-256-GCM
  const cipher = crypto.createCipheriv('aes-256-gcm', getKeyBuffer(), iv);

  // Encrypt the text
  let encrypted = cipher.update(text, 'utf8', 'base64');
  encrypted += cipher.final('base64');

  // Get the authentication tag
  const authTag = cipher.getAuthTag();

  // Combine the IV, encrypted text, and auth tag
  // Format: base64(iv):base64(authTag):base64(encryptedText)
  return `${iv.toString('base64')}:${authTag.toString('base64')}:${encrypted}`;
}

/**
 * Decrypts a string that was encrypted using encrypt()
 * @param encryptedText The encrypted text (format: base64(iv):base64(authTag):base64(encryptedText))
 * @returns The decrypted text
 */
export async function decrypt(encryptedText: string): Promise<string> {
  // Split the encrypted text into its components
  const [ivBase64, authTagBase64, encryptedBase64] = encryptedText.split(':');

  if (!ivBase64 || !authTagBase64 || !encryptedBase64) {
    throw new Error('Invalid encrypted text format');
  }

  // Convert the components from base64 to buffers
  const iv = Buffer.from(ivBase64, 'base64');
  const authTag = Buffer.from(authTagBase64, 'base64');

  // Create a decipher
  const decipher = crypto.createDecipheriv('aes-256-gcm', getKeyBuffer(), iv);

  // Set the auth tag
  decipher.setAuthTag(authTag);

  // Decrypt the text
  let decrypted = decipher.update(encryptedBase64, 'base64', 'utf8');
  decrypted += decipher.final('utf8');

  return decrypted;
}

/**
 * Generates a secure encryption key for use with this module
 * This should be run once to generate a key, which should then be stored as an environment variable
 * @returns A base64-encoded 32-byte key
 */
export function generateEncryptionKey(): string {
  return crypto.randomBytes(32).toString('base64');
}
