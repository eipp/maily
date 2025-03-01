import { getRequestConfig } from 'next-intl/server';
import { notFound } from 'next/navigation';

// Define the supported locales
export const locales = ['en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'ar', 'he', 'ja', 'zh'];

// Define the default locale
export const defaultLocale = 'en';

// Define the locale metadata
export const localeMetadata = {
  en: { name: 'English', dir: 'ltr' },
  es: { name: 'Español', dir: 'ltr' },
  fr: { name: 'Français', dir: 'ltr' },
  de: { name: 'Deutsch', dir: 'ltr' },
  it: { name: 'Italiano', dir: 'ltr' },
  pt: { name: 'Português', dir: 'ltr' },
  nl: { name: 'Nederlands', dir: 'ltr' },
  ar: { name: 'العربية', dir: 'rtl' },
  he: { name: 'עברית', dir: 'rtl' },
  ja: { name: '日本語', dir: 'ltr' },
  zh: { name: '中文', dir: 'ltr' },
};

// Configuration for next-intl
export default getRequestConfig(async ({ locale }) => {
  // Validate that the locale is supported
  if (!locales.includes(locale as any)) {
    notFound();
  }

  // Load the messages for the locale
  let messages;
  try {
    messages = (await import(`../locales/${locale}/translation.json`)).default;
  } catch (error) {
    console.error(`Could not load messages for locale: ${locale}`, error);
    // Fallback to default locale if messages can't be loaded
    messages = (await import(`../locales/${defaultLocale}/translation.json`)).default;
  }

  return {
    messages,
    timeZone: 'UTC',
    now: new Date(),
  };
});

// Helper function to get the direction for a locale
export function getLocaleDir(locale: string): 'ltr' | 'rtl' {
  return (localeMetadata[locale as keyof typeof localeMetadata]?.dir as 'ltr' | 'rtl') || 'ltr';
}

// Helper function to get the display name for a locale
export function getLocaleName(locale: string): string {
  return localeMetadata[locale as keyof typeof localeMetadata]?.name || locale;
}
