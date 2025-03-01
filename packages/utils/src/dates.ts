/**
 * Date utility module for consistent date formatting and manipulation
 */

/**
 * Format a date using Intl.DateTimeFormat
 * @param date - The date to format
 * @param options - Intl.DateTimeFormatOptions
 * @param locale - The locale to use (default: 'en-US')
 * @returns Formatted date string
 */
export function formatDate(
  date: Date | string | number,
  options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  },
  locale = 'en-US'
): string {
  const dateObj = date instanceof Date ? date : new Date(date);
  return new Intl.DateTimeFormat(locale, options).format(dateObj);
}

/**
 * Format a date as a relative time (e.g., "2 hours ago", "in 3 days")
 * @param date - The date to format
 * @param locale - The locale to use (default: 'en-US')
 * @returns Relative time string
 */
export function formatRelativeTime(
  date: Date | string | number,
  locale = 'en-US'
): string {
  const dateObj = date instanceof Date ? date : new Date(date);
  const now = new Date();
  const diffInMs = dateObj.getTime() - now.getTime();
  const diffInSecs = Math.floor(diffInMs / 1000);
  const diffInMins = Math.floor(diffInSecs / 60);
  const diffInHours = Math.floor(diffInMins / 60);
  const diffInDays = Math.floor(diffInHours / 24);

  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' });

  if (Math.abs(diffInDays) > 30) {
    return formatDate(dateObj);
  } else if (Math.abs(diffInDays) >= 1) {
    return rtf.format(diffInDays, 'day');
  } else if (Math.abs(diffInHours) >= 1) {
    return rtf.format(diffInHours, 'hour');
  } else if (Math.abs(diffInMins) >= 1) {
    return rtf.format(diffInMins, 'minute');
  } else {
    return rtf.format(diffInSecs, 'second');
  }
}

/**
 * Add time to a date
 * @param date - The date to modify
 * @param amount - The amount to add
 * @param unit - The unit (years, months, days, hours, minutes, seconds)
 * @returns New date with time added
 */
export function addTime(
  date: Date,
  amount: number,
  unit: 'years' | 'months' | 'days' | 'hours' | 'minutes' | 'seconds'
): Date {
  const result = new Date(date);

  switch (unit) {
    case 'years':
      result.setFullYear(result.getFullYear() + amount);
      break;
    case 'months':
      result.setMonth(result.getMonth() + amount);
      break;
    case 'days':
      result.setDate(result.getDate() + amount);
      break;
    case 'hours':
      result.setHours(result.getHours() + amount);
      break;
    case 'minutes':
      result.setMinutes(result.getMinutes() + amount);
      break;
    case 'seconds':
      result.setSeconds(result.getSeconds() + amount);
      break;
  }

  return result;
}

/**
 * Get the difference between two dates in the specified unit
 * @param date1 - The first date
 * @param date2 - The second date (default: current date/time)
 * @param unit - The unit to return the difference in
 * @returns The difference in the specified unit
 */
export function getDateDiff(
  date1: Date | string | number,
  date2: Date | string | number = new Date(),
  unit: 'years' | 'months' | 'days' | 'hours' | 'minutes' | 'seconds' | 'milliseconds'
): number {
  const d1 = date1 instanceof Date ? date1 : new Date(date1);
  const d2 = date2 instanceof Date ? date2 : new Date(date2);
  const diffMs = d1.getTime() - d2.getTime();

  switch (unit) {
    case 'years':
      return d1.getFullYear() - d2.getFullYear();
    case 'months':
      return (d1.getFullYear() - d2.getFullYear()) * 12 + (d1.getMonth() - d2.getMonth());
    case 'days':
      return Math.floor(diffMs / (1000 * 60 * 60 * 24));
    case 'hours':
      return Math.floor(diffMs / (1000 * 60 * 60));
    case 'minutes':
      return Math.floor(diffMs / (1000 * 60));
    case 'seconds':
      return Math.floor(diffMs / 1000);
    case 'milliseconds':
    default:
      return diffMs;
  }
}

/**
 * Check if a date is between two other dates
 * @param date - The date to check
 * @param startDate - The start date of the range
 * @param endDate - The end date of the range
 * @param inclusive - Whether to include the start and end dates (default: true)
 * @returns True if the date is in the range, false otherwise
 */
export function isDateInRange(
  date: Date | string | number,
  startDate: Date | string | number,
  endDate: Date | string | number,
  inclusive = true
): boolean {
  const d = date instanceof Date ? date : new Date(date);
  const start = startDate instanceof Date ? startDate : new Date(startDate);
  const end = endDate instanceof Date ? endDate : new Date(endDate);

  if (inclusive) {
    return d >= start && d <= end;
  } else {
    return d > start && d < end;
  }
}

/**
 * Get the start of a time period for a date
 * @param date - The date to get the start for
 * @param unit - The unit (day, week, month, year)
 * @returns Date at the start of the specified unit
 */
export function getStartOf(
  date: Date,
  unit: 'day' | 'week' | 'month' | 'year'
): Date {
  const result = new Date(date);

  switch (unit) {
    case 'day':
      result.setHours(0, 0, 0, 0);
      break;
    case 'week':
      const day = result.getDay();
      result.setDate(result.getDate() - day);
      result.setHours(0, 0, 0, 0);
      break;
    case 'month':
      result.setDate(1);
      result.setHours(0, 0, 0, 0);
      break;
    case 'year':
      result.setMonth(0, 1);
      result.setHours(0, 0, 0, 0);
      break;
  }

  return result;
}

/**
 * Get the end of a time period for a date
 * @param date - The date to get the end for
 * @param unit - The unit (day, week, month, year)
 * @returns Date at the end of the specified unit
 */
export function getEndOf(
  date: Date,
  unit: 'day' | 'week' | 'month' | 'year'
): Date {
  const result = new Date(date);

  switch (unit) {
    case 'day':
      result.setHours(23, 59, 59, 999);
      break;
    case 'week':
      const day = result.getDay();
      result.setDate(result.getDate() + (6 - day));
      result.setHours(23, 59, 59, 999);
      break;
    case 'month':
      result.setMonth(result.getMonth() + 1, 0);
      result.setHours(23, 59, 59, 999);
      break;
    case 'year':
      result.setFullYear(result.getFullYear() + 1, 0, 0);
      result.setDate(0);
      result.setHours(23, 59, 59, 999);
      break;
  }

  return result;
}

/**
 * Parse a date string in ISO format
 * @param dateString - The ISO date string to parse
 * @returns Parsed Date object
 */
export function parseISODate(dateString: string): Date {
  return new Date(dateString);
}

/**
 * Format a date as ISO string (YYYY-MM-DD)
 * @param date - The date to format
 * @returns ISO formatted date string
 */
export function toISODateString(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

/**
 * Get a list of date objects for each day in a date range
 * @param startDate - Start date of the range
 * @param endDate - End date of the range
 * @returns Array of Date objects for each day in the range
 */
export function getDatesInRange(
  startDate: Date | string | number,
  endDate: Date | string | number
): Date[] {
  const start = startDate instanceof Date ? startDate : new Date(startDate);
  const end = endDate instanceof Date ? endDate : new Date(endDate);

  // Set to beginning of day
  start.setHours(0, 0, 0, 0);
  end.setHours(0, 0, 0, 0);

  const dates: Date[] = [];
  let currentDate = new Date(start);

  while (currentDate <= end) {
    dates.push(new Date(currentDate));
    currentDate.setDate(currentDate.getDate() + 1);
  }

  return dates;
}
