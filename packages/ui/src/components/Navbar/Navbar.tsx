'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, ChevronDown, Sun, Moon } from 'lucide-react';
import { Button } from '@/components/Button';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';
import { useAccessibility } from '@/components/AccessibilityProvider';
import { cn } from '@/lib/utils';

const navLinks = [
  {
    label: 'Solutions',
    href: '/marketing/solutions',
    children: [
      { label: 'Email Marketing', href: '/marketing/solutions/email' },
      { label: 'Automation', href: '/marketing/solutions/automation' },
      { label: 'Analytics', href: '/marketing/solutions/analytics' },
      { label: 'Templates', href: '/marketing/solutions/templates' },
    ],
  },
  { href: '/marketing/pricing', label: 'Pricing' },
  { href: '/marketing/blog', label: 'Blog' },
  { href: '/marketing/about', label: 'About' },
];

export function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);
  const [scrolled, setScrolled] = useState(false);
  const pathname = usePathname();
  const { highContrast, toggleHighContrast } = useAccessibility();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleDropdownClick = (href: string) => {
    if (openDropdown === href) {
      setOpenDropdown(null);
    } else {
      setOpenDropdown(href);
    }
  };

  return (
    <nav
      className={cn(
        'sticky top-0 z-50 w-full transition-all duration-200',
        scrolled ? 'bg-white/80 shadow backdrop-blur-sm' : 'bg-white'
      )}
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center">
            <Link
              href="/marketing"
              className="flex items-center space-x-2"
              onClick={() => setIsMenuOpen(false)}
            >
              <span className="text-2xl font-bold text-blue-600">Maily</span>
            </Link>

            <div className="hidden md:ml-10 md:flex md:items-center md:space-x-4">
              {navLinks.map((link) => (
                <div key={link.href} className="relative">
                  {link.children ? (
                    <button
                      onClick={() => handleDropdownClick(link.href)}
                      className={cn(
                        'group inline-flex items-center px-3 py-2 text-sm font-medium transition-colors',
                        openDropdown === link.href
                          ? 'text-blue-600'
                          : 'text-gray-700 hover:text-blue-600'
                      )}
                    >
                      {link.label}
                      <ChevronDown
                        className={cn(
                          'ml-1 size-4 transition-transform duration-200',
                          openDropdown === link.href ? 'rotate-180' : ''
                        )}
                      />
                    </button>
                  ) : (
                    <Link
                      href={link.href}
                      className={cn(
                        'px-3 py-2 text-sm font-medium transition-colors',
                        pathname === link.href
                          ? 'text-blue-600'
                          : 'text-gray-700 hover:text-blue-600'
                      )}
                    >
                      {link.label}
                    </Link>
                  )}

                  {link.children && openDropdown === link.href && (
                    <AnimatePresence>
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 10 }}
                        transition={{ duration: 0.2 }}
                        className="absolute left-0 mt-2 w-48 origin-top-left rounded-md bg-white shadow-lg ring-1 ring-black/5 focus:outline-none"
                      >
                        <div className="py-1">
                          {link.children.map((child) => (
                            <Link
                              key={child.href}
                              href={child.href}
                              className={cn(
                                'block px-4 py-2 text-sm',
                                pathname === child.href
                                  ? 'bg-gray-100 text-blue-600'
                                  : 'text-gray-700 hover:bg-gray-50 hover:text-blue-600'
                              )}
                              onClick={() => {
                                setOpenDropdown(null);
                                setIsMenuOpen(false);
                              }}
                            >
                              {child.label}
                            </Link>
                          ))}
                        </div>
                      </motion.div>
                    </AnimatePresence>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="hidden md:flex md:items-center md:space-x-4">
            <LanguageSwitcher />
            <button
              onClick={toggleHighContrast}
              className="rounded-md p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-900"
              aria-label={highContrast ? 'Disable high contrast' : 'Enable high contrast'}
            >
              {highContrast ? (
                <Moon className="size-5" />
              ) : (
                <Sun className="size-5" />
              )}
            </button>
            <Button
              variant="ghost"
              size="sm"
              asChild
            >
              <Link href="https://app.justmaily.com/auth/login">
                Sign in
              </Link>
            </Button>
            <Button
              variant="primary"
              size="sm"
              asChild
            >
              <Link href="https://app.justmaily.com/auth/signup">
                Get started
              </Link>
            </Button>
          </div>

          <div className="flex md:hidden">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="inline-flex items-center justify-center rounded-md p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-500"
              aria-expanded={isMenuOpen}
            >
              <span className="sr-only">
                {isMenuOpen ? 'Close menu' : 'Open menu'}
              </span>
              {isMenuOpen ? (
                <X className="size-6" />
              ) : (
                <Menu className="size-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      <AnimatePresence>
        {isMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="md:hidden"
          >
            <div className="space-y-1 px-4 pb-3 pt-2">
              {navLinks.map((link) => (
                <div key={link.href}>
                  {link.children ? (
                    <>
                      <button
                        onClick={() => handleDropdownClick(link.href)}
                        className="flex w-full items-center justify-between py-2 text-base font-medium text-gray-700"
                      >
                        {link.label}
                        <ChevronDown
                          className={cn(
                            'size-5 transition-transform duration-200',
                            openDropdown === link.href ? 'rotate-180' : ''
                          )}
                        />
                      </button>
                      <AnimatePresence>
                        {openDropdown === link.href && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className="ml-4 space-y-1"
                          >
                            {link.children.map((child) => (
                              <Link
                                key={child.href}
                                href={child.href}
                                className={cn(
                                  'block py-2 text-sm',
                                  pathname === child.href
                                    ? 'text-blue-600'
                                    : 'text-gray-500 hover:text-blue-600'
                                )}
                                onClick={() => {
                                  setOpenDropdown(null);
                                  setIsMenuOpen(false);
                                }}
                              >
                                {child.label}
                              </Link>
                            ))}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </>
                  ) : (
                    <Link
                      href={link.href}
                      className={cn(
                        'block py-2 text-base font-medium',
                        pathname === link.href
                          ? 'text-blue-600'
                          : 'text-gray-700 hover:text-blue-600'
                      )}
                      onClick={() => setIsMenuOpen(false)}
                    >
                      {link.label}
                    </Link>
                  )}
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
