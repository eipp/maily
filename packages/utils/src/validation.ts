/**
 * Validation utility functions
 */

/**
 * Email validation options
 */
export interface EmailValidationOptions {
  /**
   * Allow local part only (e.g., 'user' instead of 'user@example.com')
   */
  allowLocalOnly?: boolean;

  /**
   * Allow IP domain (e.g., 'user@[127.0.0.1]')
   */
  allowIpDomain?: boolean;

  /**
   * Require TLD (e.g., require '.com' in 'example.com')
   */
  requireTld?: boolean;
}

/**
 * Check if a string is a valid email
 * @param value String to check
 * @param options Validation options
 * @returns Whether string is a valid email
 */
export function isEmail(
  value: string,
  options: EmailValidationOptions = {}
): boolean {
  if (!value || typeof value !== 'string') {
    return false;
  }

  const {
    allowLocalOnly = false,
    allowIpDomain = false,
    requireTld = true,
  } = options;

  // If local part only is allowed and no @ is present
  if (allowLocalOnly && !value.includes('@')) {
    // Validate local part only
    return /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+$/.test(value);
  }

  // Split into local part and domain
  const parts = value.split('@');
  if (parts.length !== 2) {
    return false;
  }

  const [local, domain] = parts;

  // Check local part
  if (!local || local.length > 64 || !/^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+$/.test(local)) {
    return false;
  }

  // Check for consecutive periods
  if (local.includes('..')) {
    return false;
  }

  // Check domain
  if (!domain || domain.length > 255) {
    return false;
  }

  // Check for IP domain
  if (domain.startsWith('[') && domain.endsWith(']')) {
    if (!allowIpDomain) {
      return false;
    }

    // Strip brackets
    const ip = domain.substring(1, domain.length - 1);

    // Check if IPv4
    return isIPv4(ip);
  }

  // Check domain parts
  const domainParts = domain.split('.');
  if (requireTld && domainParts.length < 2) {
    return false;
  }

  for (const part of domainParts) {
    if (!part || part.length > 63 || !/^[a-zA-Z0-9-]+$/.test(part)) {
      return false;
    }

    if (part.startsWith('-') || part.endsWith('-')) {
      return false;
    }
  }

  return true;
}

/**
 * Check if a string is a valid URL
 * @param value String to check
 * @param options URL validation options
 * @returns Whether string is a valid URL
 */
export function isUrl(
  value: string,
  options: {
    requireProtocol?: boolean;
    requireTld?: boolean;
    allowedProtocols?: string[];
  } = {}
): boolean {
  if (!value || typeof value !== 'string') {
    return false;
  }

  const {
    requireProtocol = true,
    requireTld = true,
    allowedProtocols = ['http:', 'https:'],
  } = options;

  try {
    const url = new URL(value);

    // Check protocol
    if (requireProtocol && !url.protocol) {
      return false;
    }

    if (
      requireProtocol &&
      allowedProtocols.length > 0 &&
      !allowedProtocols.includes(url.protocol)
    ) {
      return false;
    }

    // Check host
    if (!url.host) {
      return false;
    }

    // Check TLD
    if (requireTld && !/\.[a-z]{2,}$/i.test(url.hostname)) {
      // Allow IP addresses
      return isIPv4(url.hostname) || isIPv6(url.hostname);
    }

    return true;
  } catch (e) {
    return false;
  }
}

/**
 * Check if a string is a valid IPv4 address
 * @param value String to check
 * @returns Whether string is a valid IPv4 address
 */
export function isIPv4(value: string): boolean {
  if (!value || typeof value !== 'string') {
    return false;
  }

  // Check format
  if (!/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/.test(value)) {
    return false;
  }

  // Check range of each octet
  return value.split('.').every(part => {
    const num = parseInt(part, 10);
    return num >= 0 && num <= 255;
  });
}

/**
 * Check if a string is a valid IPv6 address
 * @param value String to check
 * @returns Whether string is a valid IPv6 address
 */
export function isIPv6(value: string): boolean {
  if (!value || typeof value !== 'string') {
    return false;
  }

  // Basic format check
  if (!/^([0-9a-f]{1,4}:){7}[0-9a-f]{1,4}$/i.test(value)) {
    // Check for abbreviated forms
    if (!/::.+/.test(value) && !/.+::/.test(value)) {
      return false;
    }
  }

  // Try parsing it via the browser's built-in functionality
  try {
    const url = new URL(`http://[${value}]`);
    return url.hostname === `[${value}]`;
  } catch (e) {
    return false;
  }
}

/**
 * Check if a value is a valid date
 * @param value Value to check
 * @returns Whether value is a valid date
 */
export function isDate(value: any): boolean {
  if (value instanceof Date) {
    return !isNaN(value.getTime());
  }

  if (typeof value === 'string' || typeof value === 'number') {
    const date = new Date(value);
    return !isNaN(date.getTime());
  }

  return false;
}

/**
 * Check if a string is a valid UUID
 * @param value String to check
 * @param version UUID version to validate against
 * @returns Whether string is a valid UUID
 */
export function isUUID(value: string, version: 1 | 3 | 4 | 5 = 4): boolean {
  if (!value || typeof value !== 'string') {
    return false;
  }

  let pattern: RegExp;

  switch (version) {
    case 1:
      pattern = /^[0-9a-f]{8}-[0-9a-f]{4}-1[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
      break;
    case 3:
      pattern = /^[0-9a-f]{8}-[0-9a-f]{4}-3[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
      break;
    case 4:
      pattern = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
      break;
    case 5:
      pattern = /^[0-9a-f]{8}-[0-9a-f]{4}-5[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
      break;
    default:
      pattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  }

  return pattern.test(value);
}

/**
 * Check if a string is a valid credit card number
 * @param value String to check
 * @returns Whether string is a valid credit card number
 */
export function isCreditCard(value: string): boolean {
  if (!value || typeof value !== 'string') {
    return false;
  }

  // Remove all non-digits
  const sanitized = value.replace(/[^\d]/g, '');

  if (sanitized.length < 13 || sanitized.length > 19) {
    return false;
  }

  // Luhn algorithm (mod 10)
  let sum = 0;
  let shouldDouble = false;

  for (let i = sanitized.length - 1; i >= 0; i--) {
    let digit = parseInt(sanitized.charAt(i), 10);

    if (shouldDouble) {
      digit *= 2;
      if (digit > 9) {
        digit -= 9;
      }
    }

    sum += digit;
    shouldDouble = !shouldDouble;
  }

  return sum % 10 === 0;
}

/**
 * Check if a string is a valid JSON
 * @param value String to check
 * @returns Whether string is valid JSON
 */
export function isJSON(value: string): boolean {
  if (!value || typeof value !== 'string') {
    return false;
  }

  try {
    JSON.parse(value);
    return true;
  } catch (e) {
    return false;
  }
}

/**
 * Check if a value is empty
 * @param value Value to check
 * @returns Whether value is empty
 */
export function isEmpty(value: any): boolean {
  if (value === null || value === undefined) {
    return true;
  }

  if (typeof value === 'string' || Array.isArray(value)) {
    return value.length === 0;
  }

  if (typeof value === 'object') {
    return Object.keys(value).length === 0;
  }

  return false;
}

/**
 * Check if a string is a valid alpha string (letters only)
 * @param value String to check
 * @param locale Locale to use for letter check
 * @returns Whether string only contains letters
 */
export function isAlpha(value: string, locale: string = 'en-US'): boolean {
  if (!value || typeof value !== 'string') {
    return false;
  }

  try {
    return !/[^p{L}]/u.test(value);
  } catch (e) {
    // Fallback for environments without Unicode property support
    return /^[A-Za-z]+$/.test(value);
  }
}

/**
 * Check if a string is alphanumeric
 * @param value String to check
 * @param locale Locale to use for letter check
 * @returns Whether string only contains letters and numbers
 */
export function isAlphanumeric(value: string, locale: string = 'en-US'): boolean {
  if (!value || typeof value !== 'string') {
    return false;
  }

  try {
    return !/[^p{L}\p{N}]/u.test(value);
  } catch (e) {
    // Fallback for environments without Unicode property support
    return /^[A-Za-z0-9]+$/.test(value);
  }
}

/**
 * Check if a string is numeric
 * @param value String to check
 * @param options Numeric validation options
 * @returns Whether string is numeric
 */
export function isNumeric(
  value: string,
  options: {
    allowDecimal?: boolean;
    allowNegative?: boolean;
    allowThousandsSeparator?: boolean;
  } = {}
): boolean {
  if (!value || typeof value !== 'string') {
    return false;
  }

  const {
    allowDecimal = true,
    allowNegative = true,
    allowThousandsSeparator = false,
  } = options;

  let sanitized = value;

  // Handle thousands separator
  if (allowThousandsSeparator) {
    sanitized = sanitized.replace(/,/g, '');
  }

  // Check for negative numbers
  if (allowNegative && sanitized.startsWith('-')) {
    sanitized = sanitized.substring(1);
  } else if (!allowNegative && sanitized.includes('-')) {
    return false;
  }

  // Check for decimal point
  if (allowDecimal) {
    const parts = sanitized.split('.');
    if (parts.length > 2) {
      return false;
    }

    sanitized = sanitized.replace('.', '');
  } else if (sanitized.includes('.')) {
    return false;
  }

  return /^\d+$/.test(sanitized);
}

/**
 * Check if a string is a valid phone number
 * @param value String to check
 * @param locale Phone locale (country code)
 * @returns Whether string is a valid phone number
 */
export function isPhoneNumber(value: string, locale: string = 'US'): boolean {
  if (!value || typeof value !== 'string') {
    return false;
  }

  // Remove common separators
  const sanitized = value.replace(/[\s\-\(\)\.]/g, '');

  // Basic validation patterns by locale
  const patterns: Record<string, RegExp> = {
    US: /^(\+?1)?[2-9]\d{9}$/,
    UK: /^(\+?44|0)7\d{9}$/,
    AU: /^(\+?61|0)[2378]\d{8}$/,
    CA: /^(\+?1)?[2-9]\d{9}$/,
    IN: /^(\+?91|0)?[6789]\d{9}$/,
    // Add more country codes as needed
  };

  const pattern = patterns[locale] || patterns.US;
  return pattern.test(sanitized);
}

/**
 * Validate a password
 * @param value Password to check
 * @param options Password validation options
 * @returns Whether password is valid
 */
export function isStrongPassword(
  value: string,
  options: {
    minLength?: number;
    minLowercase?: number;
    minUppercase?: number;
    minNumbers?: number;
    minSymbols?: number;
  } = {}
): boolean {
  if (!value || typeof value !== 'string') {
    return false;
  }

  const {
    minLength = 8,
    minLowercase = 1,
    minUppercase = 1,
    minNumbers = 1,
    minSymbols = 1,
  } = options;

  // Check minimum length
  if (value.length < minLength) {
    return false;
  }

  // Count character types
  const lowercaseCount = (value.match(/[a-z]/g) || []).length;
  const uppercaseCount = (value.match(/[A-Z]/g) || []).length;
  const numberCount = (value.match(/[0-9]/g) || []).length;
  const symbolCount = (value.match(/[^a-zA-Z0-9]/g) || []).length;

  return (
    lowercaseCount >= minLowercase &&
    uppercaseCount >= minUppercase &&
    numberCount >= minNumbers &&
    symbolCount >= minSymbols
  );
}

/**
 * Validation result with error message
 */
export interface ValidationResult {
  /**
   * Whether validation passed
   */
  valid: boolean;

  /**
   * Error message (if validation failed)
   */
  message?: string;
}

/**
 * Type-safe validator functions
 */
export interface Validator<T> {
  /**
   * Validate a value
   * @param value Value to validate
   * @returns Validation result
   */
  (value: T): ValidationResult;
}

/**
 * Create a required validator
 * @param message Error message
 * @returns Validator function
 */
export function required<T>(message: string = 'This field is required'): Validator<T> {
  return (value: T): ValidationResult => {
    if (value === null || value === undefined) {
      return { valid: false, message };
    }

    if (typeof value === 'string' && value.trim() === '') {
      return { valid: false, message };
    }

    if (Array.isArray(value) && value.length === 0) {
      return { valid: false, message };
    }

    return { valid: true };
  };
}

/**
 * Create a minimum length validator
 * @param min Minimum length
 * @param message Error message
 * @returns Validator function
 */
export function minLength(
  min: number,
  message: string = `Minimum length is ${min} characters`
): Validator<string> {
  return (value: string): ValidationResult => {
    if (!value) {
      return { valid: true };
    }

    return {
      valid: value.length >= min,
      message,
    };
  };
}

/**
 * Create a maximum length validator
 * @param max Maximum length
 * @param message Error message
 * @returns Validator function
 */
export function maxLength(
  max: number,
  message: string = `Maximum length is ${max} characters`
): Validator<string> {
  return (value: string): ValidationResult => {
    if (!value) {
      return { valid: true };
    }

    return {
      valid: value.length <= max,
      message,
    };
  };
}

/**
 * Create a pattern validator
 * @param pattern RegExp pattern
 * @param message Error message
 * @returns Validator function
 */
export function pattern(
  pattern: RegExp,
  message: string = 'Invalid format'
): Validator<string> {
  return (value: string): ValidationResult => {
    if (!value) {
      return { valid: true };
    }

    return {
      valid: pattern.test(value),
      message,
    };
  };
}

/**
 * Create an email validator
 * @param message Error message
 * @param options Email validation options
 * @returns Validator function
 */
export function email(
  message: string = 'Invalid email address',
  options: EmailValidationOptions = {}
): Validator<string> {
  return (value: string): ValidationResult => {
    if (!value) {
      return { valid: true };
    }

    return {
      valid: isEmail(value, options),
      message,
    };
  };
}

/**
 * Create a URL validator
 * @param message Error message
 * @param options URL validation options
 * @returns Validator function
 */
export function url(
  message: string = 'Invalid URL',
  options: {
    requireProtocol?: boolean;
    requireTld?: boolean;
    allowedProtocols?: string[];
  } = {}
): Validator<string> {
  return (value: string): ValidationResult => {
    if (!value) {
      return { valid: true };
    }

    return {
      valid: isUrl(value, options),
      message,
    };
  };
}

/**
 * Run multiple validators on a value
 * @param value Value to validate
 * @param validators Validators to run
 * @returns First failed validation or { valid: true }
 */
export function validate<T>(
  value: T,
  validators: Validator<T>[]
): ValidationResult {
  for (const validator of validators) {
    const result = validator(value);
    if (!result.valid) {
      return result;
    }
  }

  return { valid: true };
}
