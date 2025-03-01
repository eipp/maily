import { format } from 'date-fns';

/**
 * Formats a date object into a human-readable string.
 *
 * @param {Date} date - The date object to format
 * @param {string} [formatString='MMM dd, yyyy'] - The format string using date-fns format tokens
 * @returns {string} The formatted date string or 'Invalid Date' if parsing fails
 * @example
 * ```ts
 * formatDate(new Date('2024-02-24')) // Returns 'Feb 24, 2024'
 * formatDate(new Date('2024-02-24'), 'yyyy-MM-dd') // Returns '2024-02-24'
 * ```
 */
export function formatDate(date: Date, formatString: string = 'MMM dd, yyyy'): string {
  try {
    return format(date, formatString);
  } catch (error) {
    return 'Invalid Date';
  }
}

/**
 * Formats a number as a currency string with proper symbol placement and decimal handling.
 *
 * @param {number} amount - The amount to format
 * @param {string} [currency='USD'] - The currency code (e.g., 'USD', 'EUR', 'GBP')
 * @returns {string} The formatted currency string
 * @example
 * ```ts
 * formatCurrency(1234.56) // Returns '$1,234.56'
 * formatCurrency(-1234.56, 'EUR') // Returns '-€1,234.56'
 * ```
 */
export function formatCurrency(amount: number, currency: string = 'USD'): string {
  const formatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  // Handle negative numbers separately to ensure correct symbol placement
  if (amount < 0) {
    return '-' + formatter.format(Math.abs(amount));
  }
  return formatter.format(amount);
}

/**
 * Formats a file size in bytes to a human-readable string with appropriate units.
 *
 * @param {number} bytes - The size in bytes
 * @returns {string} The formatted file size string with units
 * @example
 * ```ts
 * formatFileSize(1024) // Returns '1.0 KB'
 * formatFileSize(1234567) // Returns '1.2 MB'
 * ```
 */
export function formatFileSize(bytes: number): string {
  if (bytes < 0) return 'Invalid size';
  if (bytes === 0) return '0 B';

  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const k = 1024;
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  if (i === 0) return `${bytes} ${units[i]}`;
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${units[i]}`;
}

/**
 * Truncates text to a specified length while preserving whole words.
 *
 * @param {string} text - The text to truncate
 * @param {number} maxLength - Maximum length of the truncated text
 * @param {string} [ellipsis='...'] - The ellipsis string to append
 * @returns {string} The truncated text with ellipsis
 * @example
 * ```ts
 * truncateText('This is a long text', 10) // Returns 'This is...'
 * truncateText('Short', 10) // Returns 'Short'
 * ```
 */
export function truncateText(text: string, maxLength: number, ellipsis: string = '...'): string {
  if (!text || text.length <= maxLength) return text;

  // Find the last space within maxLength to avoid cutting words
  const lastSpace = text.substring(0, maxLength).lastIndexOf(' ');
  const truncateIndex = lastSpace > 0 ? lastSpace : maxLength;

  return text.substring(0, truncateIndex) + ellipsis;
}

/**
 * Formats a number as a percentage with specified decimal places.
 *
 * @param {number} value - The value to format as percentage (0.1 = 10%)
 * @param {number} [decimals=1] - Number of decimal places to show
 * @param {boolean} [includeSign=false] - Whether to include the plus sign for positive values
 * @returns {string} The formatted percentage string
 * @example
 * ```ts
 * formatPercentage(0.1234) // Returns '12.3%'
 * formatPercentage(0.1234, 2) // Returns '12.34%'
 * formatPercentage(0.1234, 1, true) // Returns '+12.3%'
 * ```
 */
export function formatPercentage(
  value: number,
  decimals: number = 1,
  includeSign: boolean = false
): string {
  const percentage = value * 100;
  const formatted = percentage.toFixed(decimals);
  const sign = includeSign && percentage > 0 ? '+' : '';
  return `${sign}${formatted}%`;
}

/**
 * Formats a phone number string into a standardized format.
 * Supports US phone numbers by default.
 *
 * @param {string} phone - The phone number to format
 * @param {string} [format='US'] - The format to use (currently only 'US' is supported)
 * @returns {string} The formatted phone number
 * @example
 * ```ts
 * formatPhoneNumber('1234567890') // Returns '(123) 456-7890'
 * formatPhoneNumber('11234567890') // Returns '+1 (123) 456-7890'
 * ```
 */
export function formatPhoneNumber(phone: string, format: string = 'US'): string {
  // Remove all non-numeric characters
  const cleaned = phone.replace(/\D/g, '');

  if (format === 'US') {
    if (cleaned.length === 10) {
      return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
    } else if (cleaned.length === 11 && cleaned.startsWith('1')) {
      return `+1 (${cleaned.slice(1, 4)}) ${cleaned.slice(4, 7)}-${cleaned.slice(7)}`;
    }
  }

  return phone; // Return original if format not supported or invalid length
}

/**
 * Formats and validates an email address.
 * Trims whitespace and converts to lowercase.
 *
 * @param {string} email - The email address to format
 * @param {boolean} [validate=true] - Whether to validate the email format
 * @returns {string} The formatted email address or empty string if invalid
 * @example
 * ```ts
 * formatEmail(' User@Example.com ') // Returns 'user@example.com'
 * formatEmail('invalid-email', true) // Returns ''
 * ```
 */
export function formatEmail(email: string, validate: boolean = true): string {
  const formatted = email.trim().toLowerCase();

  if (validate) {
    // Basic email validation regex
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(formatted) ? formatted : '';
  }

  return formatted;
}
