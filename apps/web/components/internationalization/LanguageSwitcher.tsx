import React, { useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useTransition } from 'react';
import { locales, getLocaleName, getLocaleDir } from '../../i18n/next-intl-config';
import { useLocale } from 'next-intl';

interface LanguageSwitcherProps {
  className?: string;
  dropdownClassName?: string;
  buttonClassName?: string;
}

/**
 * A language switcher component that allows users to change the application language.
 * This component displays the current language and provides a dropdown to select a different language.
 */
const LanguageSwitcher: React.FC<LanguageSwitcherProps> = ({
  className = '',
  dropdownClassName = '',
  buttonClassName = '',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const router = useRouter();
  const pathname = usePathname();
  const locale = useLocale();
  const [isPending, startTransition] = useTransition();

  // Toggle the dropdown
  const toggleDropdown = () => {
    setIsOpen(!isOpen);
  };

  // Close the dropdown when clicking outside
  const closeDropdown = () => {
    setIsOpen(false);
  };

  // Change the language
  const changeLanguage = (newLocale: string) => {
    // Close the dropdown
    setIsOpen(false);

    // Only change if the locale is different
    if (newLocale !== locale && pathname) {
      startTransition(() => {
        // Navigate to the same path with the new locale
        // This assumes you're using the Next.js Internationalized Routing
        const newPath = pathname.replace(`/${locale}`, `/${newLocale}`);
        router.push(newPath);
      });
    }
  };

  return (
    <div className={`relative ${className}`}>
      <button
        type="button"
        className={`flex items-center space-x-1 ${buttonClassName} ${isPending ? 'opacity-50' : ''}`}
        onClick={toggleDropdown}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        disabled={isPending}
      >
        <span>{getLocaleName(locale)}</span>
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? 'transform rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <>
          {/* Backdrop to detect clicks outside */}
          <div className="fixed inset-0 z-10" onClick={closeDropdown} />

          {/* Dropdown menu */}
          <div
            className={`absolute z-20 mt-2 w-48 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 ${dropdownClassName}`}
            role="listbox"
            aria-labelledby="language-switcher"
          >
            <div className="py-1" role="none">
              {locales.map((localeOption) => (
                <button
                  key={localeOption}
                  className={`block w-full text-left px-4 py-2 text-sm ${
                    localeOption === locale
                      ? 'bg-blue-100 text-blue-900'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                  role="option"
                  aria-selected={localeOption === locale}
                  onClick={() => changeLanguage(localeOption)}
                  dir={getLocaleDir(localeOption)}
                >
                  {getLocaleName(localeOption)}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default LanguageSwitcher;
