import { useRouter } from 'next/router';
import { useCallback } from 'react';

const languages = [
  { code: 'en', name: 'English' },
  { code: 'es', name: 'Español' },
  { code: 'fr', name: 'Français' },
];

export function LanguageSwitcher() {
  const router = useRouter();
  const { pathname, asPath, query } = router;

  const handleLanguageChange = useCallback((languageCode: string) => {
    router.push({ pathname, query }, asPath, { locale: languageCode });
  }, [router, pathname, asPath, query]);

  return (
    <div className="relative inline-block text-left">
      <select
        value={router.locale}
        onChange={(e) => handleLanguageChange(e.target.value)}
        className="block w-full rounded-md border-gray-300 py-2 pl-3 pr-10 text-base focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
        aria-label="Select language"
      >
        {languages.map((language) => (
          <option key={language.code} value={language.code}>
            {language.name}
          </option>
        ))}
      </select>
    </div>
  );
} 