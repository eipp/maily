/**
 * Format a date into a human-readable string
 * @param date The date to format
 * @param locale The locale to use for formatting (defaults to browser locale)
 * @returns Formatted date string
 */
export const formatDate = (date: Date, locale?: string): string => {
  try {
    // Format date as: "Jan 1, 2023, 12:00 PM"
    return new Intl.DateTimeFormat(locale, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: 'numeric',
      hour12: true,
    }).format(date);
  } catch (error) {
    console.error('Error formatting date:', error);
    // Fallback to a simple date format
    return date.toLocaleString();
  }
};

/**
 * Format a date relative to now (e.g., "2 hours ago", "yesterday", etc.)
 * @param date The date to format
 * @param locale The locale to use for formatting (defaults to browser locale)
 * @returns Relative time string
 */
export const formatRelativeTime = (date: Date, locale?: string): string => {
  try {
    const now = new Date();
    const diffInMs = now.getTime() - date.getTime();
    const diffInSecs = Math.floor(diffInMs / 1000);
    const diffInMins = Math.floor(diffInSecs / 60);
    const diffInHours = Math.floor(diffInMins / 60);
    const diffInDays = Math.floor(diffInHours / 24);

    // For very recent times
    if (diffInSecs < 60) {
      return 'just now';
    }

    // For times within the last hour
    if (diffInMins < 60) {
      return `${diffInMins} ${diffInMins === 1 ? 'minute' : 'minutes'} ago`;
    }

    // For times within the last day
    if (diffInHours < 24) {
      return `${diffInHours} ${diffInHours === 1 ? 'hour' : 'hours'} ago`;
    }

    // For times within the last week
    if (diffInDays < 7) {
      return `${diffInDays} ${diffInDays === 1 ? 'day' : 'days'} ago`;
    }

    // For older times, use the standard date format
    return formatDate(date, locale);
  } catch (error) {
    console.error('Error formatting relative time:', error);
    return formatDate(date, locale);
  }
};
