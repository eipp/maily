'use client';

import { useState, useEffect, lazy, Suspense } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import dynamic from 'next/dynamic';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, ChevronDown } from 'lucide-react';
import { Button } from '@/components/Button';

// Dynamically import analytics service to reduce initial load time
const analyticsService = dynamic(() => import('@/services/analytics').then(mod => mod.analyticsService), {
  ssr: false,
  loading: () => null,
});

// Lazy load non-critical icon
const ArrowRight = dynamic(() => import('lucide-react').then(mod => mod.ArrowRight), {
  loading: () => <span className="w-4 h-4" />,
});

const navItems = [
  {
    name: 'Solutions',
    href: '#',
    children: [
      {
        name: 'Email Marketing',
        href: '/features#email-marketing',
        description: 'Build and send beautiful email campaigns',
        icon: '📧',
      },
      {
        name: 'Automation',
        href: '/features#automation',
        description: 'Automate your email workflows',
        icon: '⚡',
      },
      {
        name: 'Analytics',
        href: '/features#analytics',
        description: 'Track and optimize performance',
        icon: '📊',
      },
      {
        name: 'Templates',
        href: '/features#templates',
        description: 'Pre-built email templates',
        icon: '🎨',
      },
    ],
  },
  { name: 'Pricing', href: '/pricing' },
  { name: 'Features', href: '/features' },
  { name: 'Blog', href: '/blog' },
];

const dropdownVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 },
};

const mobileMenuVariants = {
  hidden: { opacity: 0, height: 0 },
  visible: { opacity: 1, height: 'auto' },
  exit: { opacity: 0, height: 0 },
};

export function MarketingNav() {
  const [isOpen, setIsOpen] = useState(false);
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);
  const [scrolled, setScrolled] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleNavigation = (href: string) => {
    analyticsService.trackEvent('navigation_click', { path: href });
    setIsOpen(false);
    setOpenDropdown(null);
  };

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className={`fixed left-0 right-0 top-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'bg-white/90 shadow-md backdrop-blur-lg dark:bg-gray-900/90 shadow-gray-200/20 dark:shadow-black/20'
          : 'bg-white dark:bg-gray-900'
      }`}
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo with subtle animation */}
          <Link
            href="/"
            className="group flex items-center"
            onClick={() => handleNavigation('/')}
          >
            <motion.span 
              className="text-2xl font-bold bg-gradient-to-r from-primary-600 to-primary-500 bg-clip-text text-transparent dark:from-primary-500 dark:to-primary-400"
              whileHover={{ scale: 1.05 }}
              transition={{ type: "spring", stiffness: 400, damping: 10 }}
            >
              Maily
            </motion.span>
            <motion.span 
              className="ml-1 text-xs font-semibold text-gray-500 dark:text-gray-400"
              animate={{ opacity: [0, 1], y: [5, 0] }}
              transition={{ delay: 0.3, duration: 0.5 }}
            >
              BETA
            </motion.span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex md:items-center md:space-x-6">
            {navItems.map((item) => (
              <div key={item.name} className="relative">
                {item.children ? (
                  <button
                    onClick={() => setOpenDropdown(openDropdown === item.name ? null : item.name)}
                    className="group flex items-center space-x-1 rounded-md px-3 py-2 text-sm font-medium text-gray-700 hover:text-primary-600 dark:text-gray-300 dark:hover:text-primary-500"
                  >
                    <span>{item.name}</span>
                    <ChevronDown
                      className={`h-4 w-4 transition-transform duration-200 ${
                        openDropdown === item.name ? 'rotate-180' : ''
                      }`}
                    />
                  </button>
                ) : (
                  <Link
                    href={item.href}
                    onClick={() => handleNavigation(item.href)}
                    className={`rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                      pathname === item.href
                        ? 'text-primary-600 dark:text-primary-500'
                        : 'text-gray-700 hover:text-primary-600 dark:text-gray-300 dark:hover:text-primary-500'
                    }`}
                  >
                    {item.name}
                  </Link>
                )}

                {/* Dropdown Menu */}
                <AnimatePresence>
                  {item.children && openDropdown === item.name && (
                    <motion.div
                      initial="hidden"
                      animate="visible"
                      exit="exit"
                      variants={dropdownVariants}
                      className="absolute left-0 top-full mt-2 w-80 rounded-lg bg-white p-4 shadow-lg ring-1 ring-black ring-opacity-5 dark:bg-gray-800"
                    >
                      <div className="grid gap-4">
                        {item.children.map((child) => (
                          <Link
                            key={child.name}
                            href={child.href}
                            onClick={() => handleNavigation(child.href)}
                            className="group grid grid-cols-[auto,1fr] gap-4 rounded-md p-3 hover:bg-gray-50 dark:hover:bg-gray-700/50"
                          >
                            <span className="text-2xl">{child.icon}</span>
                            <div>
                              <div className="flex items-center justify-between">
                                <span className="font-medium text-gray-900 dark:text-white">
                                  {child.name}
                                </span>
                                <ArrowRight className="h-4 w-4 opacity-0 transition-all group-hover:translate-x-1 group-hover:opacity-100" />
                              </div>
                              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                                {child.description}
                              </p>
                            </div>
                          </Link>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}

            {/* CTA Buttons with enhanced styling and animations */}
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleNavigation('/auth/login')}
                asChild
                className="relative overflow-hidden transition-all duration-300 hover:text-primary-600 dark:hover:text-primary-400"
              >
                <Link href="/auth/login">
                  <span className="relative z-10">Sign in</span>
                  <span className="absolute inset-0 bg-primary-50 dark:bg-primary-900/30 scale-x-0 transform origin-left transition-transform duration-300 ease-out group-hover:scale-x-100"></span>
                </Link>
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => handleNavigation('/auth/signup')}
                asChild
                className="relative overflow-hidden shadow-lg hover:shadow-primary-600/20 transition-all duration-300 bg-gradient-to-r from-primary-600 to-primary-500 hover:-translate-y-0.5"
              >
                <Link href="/auth/signup">
                  <span className="relative z-10 flex items-center">
                    Get started
                    <svg className="ml-1 h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                    </svg>
                  </span>
                  <span className="absolute inset-0 bg-gradient-to-r from-primary-500 to-primary-400 opacity-0 transition-opacity duration-300 group-hover:opacity-100"></span>
                </Link>
              </Button>
            </div>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="rounded-md p-2 text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800 md:hidden"
          >
            <span className="sr-only">Toggle menu</span>
            {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial="hidden"
            animate="visible"
            exit="exit"
            variants={mobileMenuVariants}
            className="border-t dark:border-gray-800 md:hidden"
          >
            <div className="space-y-1 px-4 pb-3 pt-2">
              {navItems.map((item) => (
                <div key={item.name}>
                  {item.children ? (
                    <>
                      <button
                        onClick={() => setOpenDropdown(openDropdown === item.name ? null : item.name)}
                        className="flex w-full items-center justify-between py-2 text-base font-medium text-gray-700 dark:text-gray-300"
                      >
                        {item.name}
                        <ChevronDown
                          className={`h-5 w-5 transition-transform duration-200 ${
                            openDropdown === item.name ? 'rotate-180' : ''
                          }`}
                        />
                      </button>
                      <AnimatePresence>
                        {openDropdown === item.name && (
                          <motion.div
                            initial="hidden"
                            animate="visible"
                            exit="exit"
                            variants={dropdownVariants}
                            className="ml-4 space-y-2"
                          >
                            {item.children.map((child) => (
                              <Link
                                key={child.name}
                                href={child.href}
                                onClick={() => handleNavigation(child.href)}
                                className="flex items-center space-x-2 py-2 text-sm text-gray-600 hover:text-primary-600 dark:text-gray-400 dark:hover:text-primary-500"
                              >
                                <span>{child.icon}</span>
                                <span>{child.name}</span>
                              </Link>
                            ))}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </>
                  ) : (
                    <Link
                      href={item.href}
                      onClick={() => handleNavigation(item.href)}
                      className="block py-2 text-base font-medium text-gray-700 hover:text-primary-600 dark:text-gray-300 dark:hover:text-primary-500"
                    >
                      {item.name}
                    </Link>
                  )}
                </div>
              ))}
              <div className="mt-4 space-y-3">
                <Button variant="outline" fullWidth onClick={() => handleNavigation('/auth/login')} asChild>
                  <Link href="/auth/login">Sign in</Link>
                </Button>
                <Button variant="primary" fullWidth onClick={() => handleNavigation('/auth/signup')} asChild>
                  <Link href="/auth/signup">Get started</Link>
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.nav>
  );
}
