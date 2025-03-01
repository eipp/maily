'use client';

import { useRouter } from 'next/navigation';
import { usePathname } from 'next/navigation';
import { useCallback, useState } from 'react';
import { Button } from '@/components/Button';
import { Check, ChevronDown, Globe } from 'lucide-react';
import * as Popover from '@radix-ui/react-popover';
import { motion, AnimatePresence } from 'framer-motion';

interface Language {
  code: string;
  name: string;
  flag: string;
}

const languages: Language[] = [
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'it', name: 'Italiano', flag: '🇮🇹' },
];

export function LanguageSwitcher() {
  const router = useRouter();
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState<Language>(
    languages.find((lang) => lang.code === 'en') || languages[0]
  );

  const handleLanguageChange = useCallback(
    (language: Language) => {
      setSelectedLanguage(language);
      setIsOpen(false);

      // Update the URL with the new locale
      const newPath = pathname.replace(/^\/[a-z]{2}/, `/${language.code}`);
      router.push(newPath);

      // Optionally, you can reload the page to ensure all content is updated
      // window.location.href = newPath;
    },
    [router, pathname]
  );

  return (
    <Popover.Root open={isOpen} onOpenChange={setIsOpen}>
      <Popover.Trigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="gap-2 px-2 hover:bg-gray-100 dark:hover:bg-gray-800"
        >
          <Globe className="size-4" />
          <span className="hidden sm:inline">{selectedLanguage.name}</span>
          <span className="inline sm:hidden">{selectedLanguage.flag}</span>
          <ChevronDown
            className={`size-4 transition-transform duration-200 ${
              isOpen ? 'rotate-180' : ''
            }`}
          />
        </Button>
      </Popover.Trigger>

      <AnimatePresence>
        {isOpen && (
          <Popover.Portal forceMount>
            <Popover.Content
              side="bottom"
              align="end"
              sideOffset={8}
              asChild
              className="z-50"
            >
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.15 }}
                className="w-48 overflow-hidden rounded-lg border border-gray-200 bg-white shadow-lg dark:border-gray-800 dark:bg-gray-900"
              >
                <div className="p-1">
                  {languages.map((language) => (
                    <button
                      key={language.code}
                      onClick={() => handleLanguageChange(language)}
                      className={`flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm ${
                        selectedLanguage.code === language.code
                          ? 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-white'
                          : 'text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800/50'
                      }`}
                    >
                      <span className="flex h-5 w-5 items-center justify-center text-base">
                        {language.flag}
                      </span>
                      <span className="flex-1 text-left">{language.name}</span>
                      {selectedLanguage.code === language.code && (
                        <Check className="size-4" />
                      )}
                    </button>
                  ))}
                </div>
              </motion.div>
            </Popover.Content>
          </Popover.Portal>
        )}
      </AnimatePresence>
    </Popover.Root>
  );
}
