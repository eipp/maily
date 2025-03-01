/**
 * String utility functions
 */

/**
 * Capitalize the first letter of a string
 * @param str String to capitalize
 * @returns Capitalized string
 */
export function capitalize(str: string): string {
  if (!str || str.length === 0) {
    return str;
  }

  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Convert a string to camelCase
 * @param str String to convert
 * @returns Camel-cased string
 */
export function camelCase(str: string): string {
  return str
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, ' ')
    .replace(/\s(.)/g, (_, c) => c.toUpperCase())
    .replace(/^\w/, c => c.toLowerCase());
}

/**
 * Convert a string to snake_case
 * @param str String to convert
 * @returns Snake-cased string
 */
export function snakeCase(str: string): string {
  return str
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s-]+/g, '_')
    .replace(/([A-Z])/g, (_, c) => '_' + c.toLowerCase())
    .replace(/^_+/, '')
    .toLowerCase();
}

/**
 * Convert a string to kebab-case
 * @param str String to convert
 * @returns Kebab-cased string
 */
export function kebabCase(str: string): string {
  return str
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_]+/g, '-')
    .replace(/([A-Z])/g, (_, c) => '-' + c.toLowerCase())
    .replace(/^-+/, '')
    .toLowerCase();
}

/**
 * Convert a string to PascalCase
 * @param str String to convert
 * @returns Pascal-cased string
 */
export function pascalCase(str: string): string {
  return str
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, ' ')
    .replace(/\s(.)/g, (_, c) => c.toUpperCase())
    .replace(/^\w/, c => c.toUpperCase());
}

/**
 * Convert a string to Title Case
 * @param str String to convert
 * @param excludeWords Words to exclude from capitalization (e.g., 'of', 'the')
 * @returns Title-cased string
 */
export function titleCase(str: string, excludeWords: string[] = []): string {
  const lowerCaseWords = new Set(excludeWords.map(w => w.toLowerCase()));

  return str
    .toLowerCase()
    .split(/\s+/)
    .map((word, index) => {
      if (index > 0 && lowerCaseWords.has(word)) {
        return word;
      }
      return capitalize(word);
    })
    .join(' ');
}

/**
 * Truncate a string to a maximum length
 * @param str String to truncate
 * @param maxLength Maximum length
 * @param suffix Suffix to add when truncated
 * @returns Truncated string
 */
export function truncate(
  str: string,
  maxLength: number,
  suffix: string = '...'
): string {
  if (!str || str.length <= maxLength) {
    return str;
  }

  return str.slice(0, maxLength - suffix.length) + suffix;
}

/**
 * Pad a string to a certain length
 * @param str String to pad
 * @param length Target length
 * @param char Character to pad with
 * @param right Whether to pad on the right side (default: left)
 * @returns Padded string
 */
export function pad(
  str: string,
  length: number,
  char: string = ' ',
  right: boolean = false
): string {
  if (str.length >= length) {
    return str;
  }

  const padding = char.repeat(length - str.length);
  return right ? str + padding : padding + str;
}

/**
 * Generate a random string
 * @param length String length
 * @param chars Characters to use
 * @returns Random string
 */
export function randomString(
  length: number,
  chars: string = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
): string {
  let result = '';
  const charsLength = chars.length;

  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * charsLength));
  }

  return result;
}

/**
 * Count occurrences of a substring in a string
 * @param str String to search in
 * @param substring Substring to count
 * @param caseSensitive Whether to be case-sensitive
 * @returns Number of occurrences
 */
export function countOccurrences(
  str: string,
  substring: string,
  caseSensitive: boolean = true
): number {
  if (!str || !substring) {
    return 0;
  }

  const source = caseSensitive ? str : str.toLowerCase();
  const target = caseSensitive ? substring : substring.toLowerCase();

  let count = 0;
  let pos = source.indexOf(target);

  while (pos !== -1) {
    count++;
    pos = source.indexOf(target, pos + 1);
  }

  return count;
}

/**
 * Escape HTML special characters
 * @param html HTML string to escape
 * @returns Escaped HTML string
 */
export function escapeHtml(html: string): string {
  return html
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Unescape HTML special characters
 * @param html Escaped HTML string
 * @returns Unescaped HTML string
 */
export function unescapeHtml(html: string): string {
  return html
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#039;/g, "'");
}

/**
 * Strip HTML tags from a string
 * @param html HTML string
 * @returns Plain text string
 */
export function stripHtml(html: string): string {
  return html.replace(/<[^>]*>/g, '');
}

/**
 * Get character count by category (letters, digits, etc.)
 * @param str String to analyze
 * @returns Character count by category
 */
export function charStats(str: string): {
  total: number;
  letters: number;
  uppercase: number;
  lowercase: number;
  digits: number;
  spaces: number;
  symbols: number;
} {
  const stats = {
    total: str.length,
    letters: 0,
    uppercase: 0,
    lowercase: 0,
    digits: 0,
    spaces: 0,
    symbols: 0,
  };

  for (let i = 0; i < str.length; i++) {
    const char = str.charAt(i);

    if (/[a-zA-Z]/.test(char)) {
      stats.letters++;

      if (/[A-Z]/.test(char)) {
        stats.uppercase++;
      } else {
        stats.lowercase++;
      }
    } else if (/\d/.test(char)) {
      stats.digits++;
    } else if (/\s/.test(char)) {
      stats.spaces++;
    } else {
      stats.symbols++;
    }
  }

  return stats;
}

/**
 * Reverse a string
 * @param str String to reverse
 * @returns Reversed string
 */
export function reverse(str: string): string {
  return str.split('').reverse().join('');
}

/**
 * Check if a string is a palindrome
 * @param str String to check
 * @param ignoreCase Whether to ignore case
 * @param ignoreSpaces Whether to ignore spaces
 * @returns Whether string is a palindrome
 */
export function isPalindrome(
  str: string,
  ignoreCase: boolean = true,
  ignoreSpaces: boolean = true
): boolean {
  let processed = str;

  if (ignoreCase) {
    processed = processed.toLowerCase();
  }

  if (ignoreSpaces) {
    processed = processed.replace(/\s+/g, '');
  }

  const reversed = reverse(processed);
  return processed === reversed;
}

/**
 * Format a string with named placeholders
 * @param template Template string with {placeholder} syntax
 * @param values Values to insert
 * @returns Formatted string
 */
export function format(
  template: string,
  values: Record<string, any>
): string {
  return template.replace(
    /{([^{}]*)}/g,
    (match, key) => {
      const value = values[key];
      return value !== undefined ? String(value) : match;
    }
  );
}

/**
 * Split a string into chunks of a given size
 * @param str String to split
 * @param size Chunk size
 * @returns Array of chunks
 */
export function chunkString(str: string, size: number): string[] {
  const chunks: string[] = [];

  for (let i = 0; i < str.length; i += size) {
    chunks.push(str.slice(i, i + size));
  }

  return chunks;
}

/**
 * Normalize a string by removing diacritics
 * @param str String to normalize
 * @returns Normalized string
 */
export function removeDiacritics(str: string): string {
  return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
}

/**
 * Calculate levenshtein distance between two strings
 * @param a First string
 * @param b Second string
 * @returns Edit distance
 */
export function levenshtein(a: string, b: string): number {
  if (a.length === 0) return b.length;
  if (b.length === 0) return a.length;

  const matrix: number[][] = [];

  // Initialize matrix
  for (let i = 0; i <= b.length; i++) {
    matrix[i] = [i];
  }

  for (let j = 0; j <= a.length; j++) {
    matrix[0][j] = j;
  }

  // Calculate distances
  for (let i = 1; i <= b.length; i++) {
    for (let j = 1; j <= a.length; j++) {
      const cost = a[j - 1] === b[i - 1] ? 0 : 1;

      matrix[i][j] = Math.min(
        matrix[i - 1][j] + 1,     // deletion
        matrix[i][j - 1] + 1,     // insertion
        matrix[i - 1][j - 1] + cost // substitution
      );
    }
  }

  return matrix[b.length][a.length];
}

/**
 * Calculate similarity between two strings (0-1)
 * @param a First string
 * @param b Second string
 * @returns Similarity score (0-1)
 */
export function similarity(a: string, b: string): number {
  const distance = levenshtein(a, b);
  const maxLength = Math.max(a.length, b.length);

  return maxLength === 0 ? 1 : 1 - distance / maxLength;
}

/**
 * Convert a string to slug format
 * @param str String to convert
 * @returns Slug string
 */
export function slugify(str: string): string {
  return removeDiacritics(str)
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')    // Remove all non-word chars
    .replace(/[\s_-]+/g, '-')     // Replace spaces, underscores, and hyphens with a single hyphen
    .replace(/^-+|-+$/g, '');     // Remove leading/trailing hyphens
}

/**
 * Convert a number of bytes to a human-readable string
 * @param bytes Number of bytes
 * @param decimals Number of decimal places
 * @returns Human-readable size string
 */
export function formatBytes(bytes: number, decimals: number = 2): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i];
}

/**
 * Extract URLs from a string
 * @param str String to extract URLs from
 * @returns Array of URLs
 */
export function extractUrls(str: string): string[] {
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  return str.match(urlRegex) || [];
}

/**
 * Extract email addresses from a string
 * @param str String to extract emails from
 * @returns Array of email addresses
 */
export function extractEmails(str: string): string[] {
  const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
  return str.match(emailRegex) || [];
}

/**
 * Wrap text to a specified line length
 * @param text Text to wrap
 * @param lineLength Maximum line length
 * @param breakChar Character to use for line breaks
 * @returns Wrapped text
 */
export function wordWrap(
  text: string,
  lineLength: number = 80,
  breakChar: string = '\n'
): string {
  const regex = new RegExp(`.{1,${lineLength}}(\\s|$)`, 'g');
  return text.replace(regex, (substr) => substr.trim() + breakChar);
}

/**
 * Highlight text by wrapping occurrences with markers
 * @param text Full text
 * @param query Search query
 * @param beforeMark Text before highlight
 * @param afterMark Text after highlight
 * @param caseSensitive Whether to be case-sensitive
 * @returns Highlighted text
 */
export function highlight(
  text: string,
  query: string,
  beforeMark: string = '<mark>',
  afterMark: string = '</mark>',
  caseSensitive: boolean = false
): string {
  if (!query || !text) {
    return text;
  }

  const flags = caseSensitive ? 'g' : 'gi';
  const regex = new RegExp(query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), flags);

  return text.replace(regex, `${beforeMark}$&${afterMark}`);
}

/**
 * Generate a random password
 * @param length Password length
 * @param options Password generation options
 * @returns Random password
 */
export function generatePassword(
  length: number = 12,
  options: {
    uppercase?: boolean;
    lowercase?: boolean;
    numbers?: boolean;
    symbols?: boolean;
  } = {}
): string {
  const {
    uppercase = true,
    lowercase = true,
    numbers = true,
    symbols = true,
  } = options;

  const uppercaseChars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  const lowercaseChars = 'abcdefghijklmnopqrstuvwxyz';
  const numberChars = '0123456789';
  const symbolChars = '!@#$%^&*()-_=+[]{}|;:,.<>?';

  let chars = '';
  if (uppercase) chars += uppercaseChars;
  if (lowercase) chars += lowercaseChars;
  if (numbers) chars += numberChars;
  if (symbols) chars += symbolChars;

  if (chars.length === 0) {
    chars = uppercaseChars + lowercaseChars;
  }

  return randomString(length, chars);
}
