import { useLocale } from 'next-intl';
import { getLocaleDir } from '../i18n/next-intl-config';

/**
 * A utility hook that provides RTL-related functionality.
 * This hook helps with handling right-to-left languages like Arabic and Hebrew.
 *
 * @returns An object with RTL-related utilities
 */
export function useRtl() {
  const locale = useLocale();
  const dir = getLocaleDir(locale);
  const isRtl = dir === 'rtl';

  /**
   * Conditionally applies RTL-specific classes
   *
   * @param ltrClass - Class to apply in LTR mode
   * @param rtlClass - Class to apply in RTL mode
   * @returns The appropriate class based on the current direction
   */
  const dirClass = (ltrClass: string, rtlClass: string): string => {
    return isRtl ? rtlClass : ltrClass;
  };

  /**
   * Reverses the order of items in an array if in RTL mode
   *
   * @param array - The array to potentially reverse
   * @returns The original array in LTR mode, or a reversed copy in RTL mode
   */
  const dirOrder = <T>(array: T[]): T[] => {
    return isRtl ? [...array].reverse() : array;
  };

  /**
   * Flips a horizontal position value if in RTL mode
   *
   * @param value - The position value (e.g., 'left', 'right')
   * @returns The flipped value in RTL mode, or the original in LTR mode
   */
  const flipPosition = (value: 'left' | 'right'): 'left' | 'right' => {
    if (!isRtl) return value;
    return value === 'left' ? 'right' : 'left';
  };

  /**
   * Flips a margin or padding value if in RTL mode
   *
   * @param property - CSS property like 'ml', 'mr', 'pl', 'pr'
   * @param value - The value to apply (e.g., '4', 'auto')
   * @returns A CSS class with the appropriate direction
   */
  const dirSpacing = (property: 'ml' | 'mr' | 'pl' | 'pr', value: string): string => {
    if (!isRtl) return `${property}-${value}`;

    const flipped = property.startsWith('m')
      ? (property === 'ml' ? 'mr' : 'ml')
      : (property === 'pl' ? 'pr' : 'pl');

    return `${flipped}-${value}`;
  };

  return {
    dir,
    isRtl,
    dirClass,
    dirOrder,
    flipPosition,
    dirSpacing,
  };
}

/**
 * Utility function to get the HTML dir attribute value based on the locale
 *
 * @param locale - The locale code
 * @returns The direction ('ltr' or 'rtl')
 */
export function getHtmlDir(locale: string): 'ltr' | 'rtl' {
  return getLocaleDir(locale);
}

/**
 * Utility function to check if a locale is RTL
 *
 * @param locale - The locale code
 * @returns True if the locale is RTL, false otherwise
 */
export function isRtlLocale(locale: string): boolean {
  return getLocaleDir(locale) === 'rtl';
}
