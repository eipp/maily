/**
 * Date utility functions
 */

/**
 * Date format options
 */
export interface DateFormatOptions {
  /**
   * Date format string
   */
  format?: string;

  /**
   * Timezone (IANA time zone, e.g., 'America/New_York')
   */
  timezone?: string;

  /**
   * Locale for internationalization
   */
  locale?: string;
}

/**
 * Format a date using Intl.DateTimeFormat
 * @param date Date to format
 * @param options Format options
 * @returns Formatted date string
 */
export function formatDate(
  date: Date | string | number,
  options: Intl.DateTimeFormatOptions & { locale?: string } = {}
): string {
  const { locale = 'en-US', ...formatOptions } = options;
  const dateObj = typeof date === 'object' ? date : new Date(date);

  return new Intl.DateTimeFormat(locale, formatOptions).format(dateObj);
}

/**
 * Add days to a date
 * @param date Base date
 * @param days Number of days to add
 * @returns New date
 */
export function addDays(date: Date, days: number): Date {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
}

/**
 * Add months to a date
 * @param date Base date
 * @param months Number of months to add
 * @returns New date
 */
export function addMonths(date: Date, months: number): Date {
  const result = new Date(date);
  result.setMonth(result.getMonth() + months);
  return result;
}

/**
 * Add years to a date
 * @param date Base date
 * @param years Number of years to add
 * @returns New date
 */
export function addYears(date: Date, years: number): Date {
  const result = new Date(date);
  result.setFullYear(result.getFullYear() + years);
  return result;
}

/**
 * Add hours to a date
 * @param date Base date
 * @param hours Number of hours to add
 * @returns New date
 */
export function addHours(date: Date, hours: number): Date {
  const result = new Date(date);
  result.setHours(result.getHours() + hours);
  return result;
}

/**
 * Add minutes to a date
 * @param date Base date
 * @param minutes Number of minutes to add
 * @returns New date
 */
export function addMinutes(date: Date, minutes: number): Date {
  const result = new Date(date);
  result.setMinutes(result.getMinutes() + minutes);
  return result;
}

/**
 * Add seconds to a date
 * @param date Base date
 * @param seconds Number of seconds to add
 * @returns New date
 */
export function addSeconds(date: Date, seconds: number): Date {
  const result = new Date(date);
  result.setSeconds(result.getSeconds() + seconds);
  return result;
}

/**
 * Get the start of a day
 * @param date Date to get start of day for
 * @returns Date at start of day (00:00:00.000)
 */
export function startOfDay(date: Date): Date {
  const result = new Date(date);
  result.setHours(0, 0, 0, 0);
  return result;
}

/**
 * Get the end of a day
 * @param date Date to get end of day for
 * @returns Date at end of day (23:59:59.999)
 */
export function endOfDay(date: Date): Date {
  const result = new Date(date);
  result.setHours(23, 59, 59, 999);
  return result;
}

/**
 * Get the start of a month
 * @param date Date to get start of month for
 * @returns Date at start of month
 */
export function startOfMonth(date: Date): Date {
  const result = new Date(date);
  result.setDate(1);
  result.setHours(0, 0, 0, 0);
  return result;
}

/**
 * Get the end of a month
 * @param date Date to get end of month for
 * @returns Date at end of month
 */
export function endOfMonth(date: Date): Date {
  const result = new Date(date);
  result.setMonth(result.getMonth() + 1);
  result.setDate(0);
  result.setHours(23, 59, 59, 999);
  return result;
}

/**
 * Get the start of a year
 * @param date Date to get start of year for
 * @returns Date at start of year
 */
export function startOfYear(date: Date): Date {
  const result = new Date(date);
  result.setMonth(0, 1);
  result.setHours(0, 0, 0, 0);
  return result;
}

/**
 * Get the end of a year
 * @param date Date to get end of year for
 * @returns Date at end of year
 */
export function endOfYear(date: Date): Date {
  const result = new Date(date);
  result.setMonth(11, 31);
  result.setHours(23, 59, 59, 999);
  return result;
}

/**
 * Calculate difference between dates in days
 * @param dateLeft First date
 * @param dateRight Second date
 * @returns Difference in days
 */
export function diffInDays(dateLeft: Date, dateRight: Date): number {
  const diffTime = Math.abs(dateLeft.getTime() - dateRight.getTime());
  return Math.floor(diffTime / (1000 * 60 * 60 * 24));
}

/**
 * Calculate difference between dates in hours
 * @param dateLeft First date
 * @param dateRight Second date
 * @returns Difference in hours
 */
export function diffInHours(dateLeft: Date, dateRight: Date): number {
  const diffTime = Math.abs(dateLeft.getTime() - dateRight.getTime());
  return Math.floor(diffTime / (1000 * 60 * 60));
}

/**
 * Calculate difference between dates in minutes
 * @param dateLeft First date
 * @param dateRight Second date
 * @returns Difference in minutes
 */
export function diffInMinutes(dateLeft: Date, dateRight: Date): number {
  const diffTime = Math.abs(dateLeft.getTime() - dateRight.getTime());
  return Math.floor(diffTime / (1000 * 60));
}

/**
 * Format a relative time (e.g., "2 hours ago")
 * @param date Date to format
 * @param baseDate Base date for comparison (defaults to now)
 * @param locale Locale to use
 * @returns Relative time string
 */
export function formatRelative(
  date: Date | string | number,
  baseDate: Date = new Date(),
  locale: string = 'en-US'
): string {
  const dateObj = typeof date === 'object' ? date : new Date(date);
  const formatter = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' });

  const diffInSeconds = Math.floor((dateObj.getTime() - baseDate.getTime()) / 1000);
  const diffInMinutes = Math.floor(diffInSeconds / 60);
  const diffInHours = Math.floor(diffInMinutes / 60);
  const diffInDays = Math.floor(diffInHours / 24);
  const diffInMonths = Math.floor(diffInDays / 30);
  const diffInYears = Math.floor(diffInDays / 365);

  if (Math.abs(diffInYears) >= 1) {
    return formatter.format(diffInYears, 'year');
  } else if (Math.abs(diffInMonths) >= 1) {
    return formatter.format(diffInMonths, 'month');
  } else if (Math.abs(diffInDays) >= 1) {
    return formatter.format(diffInDays, 'day');
  } else if (Math.abs(diffInHours) >= 1) {
    return formatter.format(diffInHours, 'hour');
  } else if (Math.abs(diffInMinutes) >= 1) {
    return formatter.format(diffInMinutes, 'minute');
  } else {
    return formatter.format(diffInSeconds, 'second');
  }
}

/**
 * Check if a date is before another date
 * @param date Date to check
 * @param dateToCompare Date to compare against
 * @returns Whether date is before dateToCompare
 */
export function isBefore(date: Date, dateToCompare: Date): boolean {
  return date.getTime() < dateToCompare.getTime();
}

/**
 * Check if a date is after another date
 * @param date Date to check
 * @param dateToCompare Date to compare against
 * @returns Whether date is after dateToCompare
 */
export function isAfter(date: Date, dateToCompare: Date): boolean {
  return date.getTime() > dateToCompare.getTime();
}

/**
 * Check if a date is between two other dates
 * @param date Date to check
 * @param startDate Start of range
 * @param endDate End of range
 * @param inclusive Whether to include start and end dates
 * @returns Whether date is in range
 */
export function isBetween(
  date: Date,
  startDate: Date,
  endDate: Date,
  inclusive: boolean = true
): boolean {
  const dateTime = date.getTime();
  const startTime = startDate.getTime();
  const endTime = endDate.getTime();

  return inclusive
    ? dateTime >= startTime && dateTime <= endTime
    : dateTime > startTime && dateTime < endTime;
}

/**
 * Parse a date string using custom format
 * This is a basic implementation - for more complex parsing,
 * consider using a dedicated library like date-fns
 * @param dateString Date string to parse
 * @param format Format string
 * @returns Parsed date or null if invalid
 */
export function parseDate(dateString: string, format: string): Date | null {
  // Simple format implementation
  // Supports: yyyy, MM, dd, HH, mm, ss
  const formatTokens = {
    yyyy: '\\d{4}',
    MM: '\\d{2}',
    dd: '\\d{2}',
    HH: '\\d{2}',
    mm: '\\d{2}',
    ss: '\\d{2}',
  };

  // Create a regex pattern from the format
  let pattern = format.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const tokens: string[] = [];

  for (const [token, regex] of Object.entries(formatTokens)) {
    if (format.includes(token)) {
      pattern = pattern.replace(token, `(${regex})`);
      tokens.push(token);
    }
  }

  // Try to match the pattern
  const regExp = new RegExp(`^${pattern}$`);
  const match = dateString.match(regExp);

  if (!match) {
    return null;
  }

  // Extract values
  const values: Record<string, number> = {};
  for (let i = 0; i < tokens.length; i++) {
    values[tokens[i]] = parseInt(match[i + 1], 10);
  }

  // Set default values
  const year = values.yyyy || new Date().getFullYear();
  const month = values.MM !== undefined ? values.MM - 1 : 0;
  const day = values.dd || 1;
  const hours = values.HH || 0;
  const minutes = values.mm || 0;
  const seconds = values.ss || 0;

  // Create date object
  const result = new Date(year, month, day, hours, minutes, seconds);

  // Validate the date
  if (
    result.getFullYear() !== year ||
    result.getMonth() !== month ||
    result.getDate() !== day ||
    result.getHours() !== hours ||
    result.getMinutes() !== minutes ||
    result.getSeconds() !== seconds
  ) {
    return null;
  }

  return result;
}

/**
 * Get the weekday number (0-6, where 0 is Sunday)
 * @param date Date to get weekday for
 * @returns Weekday number
 */
export function getWeekday(date: Date): number {
  return date.getDay();
}

/**
 * Check if a date is a weekend (Saturday or Sunday)
 * @param date Date to check
 * @returns Whether date is a weekend
 */
export function isWeekend(date: Date): boolean {
  const day = date.getDay();
  return day === 0 || day === 6;
}

/**
 * Check if a date is a weekday (Monday-Friday)
 * @param date Date to check
 * @returns Whether date is a weekday
 */
export function isWeekday(date: Date): boolean {
  return !isWeekend(date);
}

/**
 * Get the quarter of the year (1-4)
 * @param date Date to check
 * @returns Quarter number
 */
export function getQuarter(date: Date): number {
  return Math.floor(date.getMonth() / 3) + 1;
}

/**
 * Get days in month
 * @param date Date to get days in month for
 * @returns Number of days in the month
 */
export function getDaysInMonth(date: Date): number {
  return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
}

/**
 * Check if a year is a leap year
 * @param year Year to check
 * @returns Whether year is a leap year
 */
export function isLeapYear(year: number): boolean {
  return (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0;
}

/**
 * Get ISO string without timezone information
 * @param date Date to format
 * @returns ISO date string without timezone
 */
export function toISODateString(date: Date): string {
  return date.toISOString().split('T')[0];
}

/**
 * Get ISO string with local timezone
 * @param date Date to format
 * @returns ISO date string with local timezone
 */
export function toLocalISOString(date: Date): string {
  const pad = (num: number) => String(num).padStart(2, '0');

  return (
    date.getFullYear() +
    '-' + pad(date.getMonth() + 1) +
    '-' + pad(date.getDate()) +
    'T' + pad(date.getHours()) +
    ':' + pad(date.getMinutes()) +
    ':' + pad(date.getSeconds()) +
    '.' + String(date.getMilliseconds()).padStart(3, '0')
  );
}
