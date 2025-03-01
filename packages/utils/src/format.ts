/**
 * Formatting utility functions for various data types
 */

/**
 * Number formatting options
 */
export interface NumberFormatOptions {
  /**
   * Number of decimal places
   */
  decimals?: number;

  /**
   * Decimal separator
   */
  decimalSeparator?: string;

  /**
   * Thousands separator
   */
  thousandsSeparator?: string;

  /**
   * Include plus sign for positive numbers
   */
  forceSign?: boolean;

  /**
   * Force trailing zeros
   */
  trailingZeros?: boolean;

  /**
   * Currency symbol
   */
  currency?: string;

  /**
   * Currency symbol position ('prefix' or 'suffix')
   */
  currencyPosition?: 'prefix' | 'suffix';

  /**
   * Space between currency symbol and number
   */
  currencySpace?: boolean;
}

/**
 * Format a number with various options
 * @param value Number to format
 * @param options Formatting options
 * @returns Formatted number string
 */
export function formatNumber(
  value: number,
  options: NumberFormatOptions = {}
): string {
  const {
    decimals = 2,
    decimalSeparator = '.',
    thousandsSeparator = ',',
    forceSign = false,
    trailingZeros = false,
    currency,
    currencyPosition = 'prefix',
    currencySpace = true,
  } = options;

  // Handle non-numbers
  if (typeof value !== 'number' || isNaN(value)) {
    return '';
  }

  // Format the number
  const isNegative = value < 0;
  let absValue = Math.abs(value);

  // Calculate parts
  let intPart = Math.floor(absValue).toString();
  let fracPart = '';

  if (decimals > 0) {
    const factor = Math.pow(10, decimals);
    const rounded = Math.round(absValue * factor) / factor;

    fracPart = rounded.toString().split('.')[1] || '';

    // Add trailing zeros if needed
    if (trailingZeros) {
      fracPart = fracPart.padEnd(decimals, '0');
    }
  }

  // Format integer part with thousands separator
  if (thousandsSeparator) {
    intPart = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, thousandsSeparator);
  }

  // Combine parts
  let formatted = intPart;
  if (fracPart) {
    formatted += decimalSeparator + fracPart;
  }

  // Add sign
  if (isNegative) {
    formatted = '-' + formatted;
  } else if (forceSign) {
    formatted = '+' + formatted;
  }

  // Add currency
  if (currency) {
    const space = currencySpace ? ' ' : '';

    if (currencyPosition === 'prefix') {
      formatted = currency + space + formatted;
    } else {
      formatted = formatted + space + currency;
    }
  }

  return formatted;
}

/**
 * Format a number as a percentage
 * @param value Number to format as percentage
 * @param options Formatting options
 * @returns Formatted percentage string
 */
export function formatPercent(
  value: number,
  options: Omit<NumberFormatOptions, 'currency' | 'currencyPosition' | 'currencySpace'> = {}
): string {
  const percentValue = value * 100;
  const formatted = formatNumber(percentValue, options);
  return `${formatted}%`;
}

/**
 * Format a number as currency
 * @param value Number to format as currency
 * @param currencyCode Currency code (USD, EUR, etc.)
 * @param locale Locale for formatting
 * @returns Formatted currency string
 */
export function formatCurrency(
  value: number,
  currencyCode: string = 'USD',
  locale: string = 'en-US'
): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currencyCode,
  }).format(value);
}

/**
 * Format a date with custom format
 * @param date Date to format
 * @param format Format string
 * @param options Formatting options
 * @returns Formatted date string
 */
export function formatDate(
  date: Date | number | string,
  format: string = 'yyyy-MM-dd',
  options: {
    locale?: string;
  } = {}
): string {
  const { locale = 'en-US' } = options;
  const dateObj = date instanceof Date ? date : new Date(date);

  // Handle invalid dates
  if (isNaN(dateObj.getTime())) {
    return '';
  }

  // Format tokens and replacements
  const tokens: Record<string, () => string> = {
    // Year
    yyyy: () => dateObj.getFullYear().toString(),
    yy: () => dateObj.getFullYear().toString().slice(-2),

    // Month
    MMMM: () => dateObj.toLocaleString(locale, { month: 'long' }),
    MMM: () => dateObj.toLocaleString(locale, { month: 'short' }),
    MM: () => (dateObj.getMonth() + 1).toString().padStart(2, '0'),
    M: () => (dateObj.getMonth() + 1).toString(),

    // Day
    dddd: () => dateObj.toLocaleString(locale, { weekday: 'long' }),
    ddd: () => dateObj.toLocaleString(locale, { weekday: 'short' }),
    dd: () => dateObj.getDate().toString().padStart(2, '0'),
    d: () => dateObj.getDate().toString(),

    // Hour
    HH: () => dateObj.getHours().toString().padStart(2, '0'),
    H: () => dateObj.getHours().toString(),
    hh: () => (dateObj.getHours() % 12 || 12).toString().padStart(2, '0'),
    h: () => (dateObj.getHours() % 12 || 12).toString(),

    // Minute
    mm: () => dateObj.getMinutes().toString().padStart(2, '0'),
    m: () => dateObj.getMinutes().toString(),

    // Second
    ss: () => dateObj.getSeconds().toString().padStart(2, '0'),
    s: () => dateObj.getSeconds().toString(),

    // Millisecond
    SSS: () => dateObj.getMilliseconds().toString().padStart(3, '0'),

    // AM/PM
    A: () => dateObj.getHours() < 12 ? 'AM' : 'PM',
    a: () => dateObj.getHours() < 12 ? 'am' : 'pm',
  };

  // Replace tokens with values
  let result = format;

  // Sort tokens by length (to handle overlapping tokens correctly)
  const sortedTokens = Object.keys(tokens).sort((a, b) => b.length - a.length);

  for (const token of sortedTokens) {
    result = result.replace(new RegExp(token, 'g'), tokens[token]());
  }

  return result;
}

/**
 * Format a file size in bytes to a human-readable string
 * @param bytes File size in bytes
 * @param options Formatting options
 * @returns Formatted file size string
 */
export function formatFileSize(
  bytes: number,
  options: {
    decimals?: number;
    binary?: boolean;
  } = {}
): string {
  const { decimals = 2, binary = false } = options;

  if (!bytes) {
    return '0 Bytes';
  }

  const base = binary ? 1024 : 1000;
  const sizes = binary
    ? ['Bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']
    : ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

  const exponent = Math.floor(Math.log(bytes) / Math.log(base));
  const value = bytes / Math.pow(base, exponent);

  return `${value.toFixed(decimals)} ${sizes[exponent]}`;
}

/**
 * Format a duration in milliseconds to a human-readable string
 * @param ms Duration in milliseconds
 * @param options Formatting options
 * @returns Formatted duration string
 */
export function formatDuration(
  ms: number,
  options: {
    format?: string;
    longNames?: boolean;
    delimiters?: {
      default?: string;
      last?: string;
    };
  } = {}
): string {
  const {
    format = 'auto',
    longNames = false,
    delimiters = { default: ', ', last: ' and ' },
  } = options;

  if (!ms || isNaN(ms) || ms < 0) {
    return '';
  }

  // Calculate units
  const seconds = Math.floor((ms / 1000) % 60);
  const minutes = Math.floor((ms / (1000 * 60)) % 60);
  const hours = Math.floor((ms / (1000 * 60 * 60)) % 24);
  const days = Math.floor(ms / (1000 * 60 * 60 * 24));

  // Unit names
  const units = {
    day: { short: 'd', long: 'day', longPlural: 'days' },
    hour: { short: 'h', long: 'hour', longPlural: 'hours' },
    minute: { short: 'm', long: 'minute', longPlural: 'minutes' },
    second: { short: 's', long: 'second', longPlural: 'seconds' },
  };

  // Format parts based on specified format
  const parts: string[] = [];

  if (format === 'auto' || format.includes('d')) {
    if (days > 0) {
      const name = longNames
        ? days === 1
          ? units.day.long
          : units.day.longPlural
        : units.day.short;
      parts.push(`${days}${longNames ? ' ' : ''}${name}`);
    }
  }

  if (format === 'auto' || format.includes('h')) {
    if (hours > 0 || (format !== 'auto' && parts.length > 0)) {
      const name = longNames
        ? hours === 1
          ? units.hour.long
          : units.hour.longPlural
        : units.hour.short;
      parts.push(`${hours}${longNames ? ' ' : ''}${name}`);
    }
  }

  if (format === 'auto' || format.includes('m')) {
    if (minutes > 0 || (format !== 'auto' && parts.length > 0)) {
      const name = longNames
        ? minutes === 1
          ? units.minute.long
          : units.minute.longPlural
        : units.minute.short;
      parts.push(`${minutes}${longNames ? ' ' : ''}${name}`);
    }
  }

  if (format === 'auto' || format.includes('s')) {
    if (seconds > 0 || parts.length === 0 || (format !== 'auto' && parts.length > 0)) {
      const name = longNames
        ? seconds === 1
          ? units.second.long
          : units.second.longPlural
        : units.second.short;
      parts.push(`${seconds}${longNames ? ' ' : ''}${name}`);
    }
  }

  // Join parts with appropriate delimiters
  if (parts.length === 0) {
    return longNames ? '0 seconds' : '0s';
  } else if (parts.length === 1) {
    return parts[0];
  } else {
    const lastPart = parts.pop();
    return parts.join(delimiters.default) + delimiters.last + lastPart;
  }
}

/**
 * Format a phone number based on country format
 * @param phoneNumber Phone number to format
 * @param countryCode Country code
 * @returns Formatted phone number
 */
export function formatPhoneNumber(
  phoneNumber: string,
  countryCode: string = 'US'
): string {
  // Strip all non-numeric characters
  const digits = phoneNumber.replace(/\D/g, '');

  // Format based on country code
  switch (countryCode.toUpperCase()) {
    case 'US':
    case 'CA':
      // Format: (XXX) XXX-XXXX
      if (digits.length === 10) {
        return `(${digits.substring(0, 3)}) ${digits.substring(3, 6)}-${digits.substring(6)}`;
      } else if (digits.length === 11 && digits.startsWith('1')) {
        // Include country code
        return `+1 (${digits.substring(1, 4)}) ${digits.substring(4, 7)}-${digits.substring(7)}`;
      }
      break;

    case 'UK':
      // Format: +44 XXXX XXXXXX
      if (digits.length === 10) {
        return `+44 ${digits.substring(0, 4)} ${digits.substring(4)}`;
      }
      break;

    case 'AU':
      // Format: +61 X XXXX XXXX
      if (digits.length === 9) {
        return `+61 ${digits.substring(0, 1)} ${digits.substring(1, 5)} ${digits.substring(5)}`;
      }
      break;

    // Add more country formats as needed
  }

  // Default: return as-is with country code if more than 10 digits
  if (digits.length > 10) {
    return `+${digits.substring(0, digits.length - 10)} ${digits.substring(digits.length - 10)}`;
  }

  return phoneNumber;
}

/**
 * Format a credit card number with proper spacing
 * @param cardNumber Credit card number to format
 * @returns Formatted credit card number
 */
export function formatCreditCard(cardNumber: string): string {
  // Strip all non-numeric characters
  const digits = cardNumber.replace(/\D/g, '');

  // Determine card type and format accordingly
  if (/^3[47]/.test(digits)) {
    // American Express: XXXX XXXXXX XXXXX
    return digits.replace(/^(\d{4})(\d{6})(\d{5})$/, '$1 $2 $3');
  } else if (/^(30[0-5]|36|38)/.test(digits)) {
    // Diners Club: XXXX XXXX XXXX XX
    return digits.replace(/^(\d{4})(\d{4})(\d{4})(\d{2})$/, '$1 $2 $3 $4');
  } else {
    // Default (Visa, MasterCard, etc.): XXXX XXXX XXXX XXXX
    return digits.replace(/(\d{4})(?=\d)/g, '$1 ').trim();
  }
}

/**
 * Format JSON data as a string with proper indentation
 * @param data Data to format
 * @param options Formatting options
 * @returns Formatted JSON string
 */
export function formatJSON(
  data: any,
  options: {
    indent?: number;
    sortKeys?: boolean;
  } = {}
): string {
  const { indent = 2, sortKeys = false } = options;

  try {
    if (sortKeys) {
      // Sort keys recursively
      const sortObject = (obj: any): any => {
        if (obj === null || typeof obj !== 'object') {
          return obj;
        }

        if (Array.isArray(obj)) {
          return obj.map(sortObject);
        }

        const sorted: Record<string, any> = {};
        Object.keys(obj)
          .sort()
          .forEach((key) => {
            sorted[key] = sortObject(obj[key]);
          });

        return sorted;
      };

      return JSON.stringify(sortObject(data), null, indent);
    } else {
      return JSON.stringify(data, null, indent);
    }
  } catch (e) {
    return '';
  }
}

/**
 * Format a URL with query parameters
 * @param url Base URL
 * @param params Query parameters
 * @returns Formatted URL
 */
export function formatURL(url: string, params: Record<string, any> = {}): string {
  const urlObj = new URL(url);

  // Add query parameters
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      urlObj.searchParams.append(key, String(value));
    }
  });

  return urlObj.toString();
}

/**
 * Format a string template with named placeholders
 * @param template Template string with {placeholder} syntax
 * @param values Values to insert
 * @returns Formatted string
 */
export function formatTemplate(
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
 * Format a list of items as a string
 * @param items List of items
 * @param options Formatting options
 * @returns Formatted list string
 */
export function formatList(
  items: string[],
  options: {
    type?: 'conjunction' | 'disjunction' | 'unit';
    style?: 'long' | 'short' | 'narrow';
    locale?: string;
  } = {}
): string {
  const {
    type = 'conjunction',
    style = 'long',
    locale = 'en-US'
  } = options;

  if (!items || items.length === 0) {
    return '';
  }

  return new Intl.ListFormat(locale, { type, style }).format(items);
}

/**
 * Format a number as a specific unit (e.g., temperature, distance)
 * @param value Number to format
 * @param unit Unit to format as
 * @param options Formatting options
 * @returns Formatted unit string
 */
export function formatUnit(
  value: number,
  unit: string,
  options: {
    locale?: string;
    style?: 'decimal' | 'percent' | 'currency' | 'unit';
    unitDisplay?: 'long' | 'short' | 'narrow';
  } = {}
): string {
  const { locale = 'en-US', unitDisplay = 'short', style = 'unit' } = options;

  try {
    return new Intl.NumberFormat(locale, {
      style,
      unit,
      unitDisplay,
    }).format(value);
  } catch (e) {
    // Fallback if the unit is not supported
    return `${value} ${unit}`;
  }
}
