'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useTheme } from 'next-themes';
import { Menu, X, Moon, Sun, ChevronRight } from 'lucide-react';

type NavItem = {
  label: string;
  href: string;
  isExternal?: boolean;
  children?: NavItem[];
};

type FloatingHeaderProps = {
  navItems: NavItem[];
  logoUrl?: string;
  logoText?: string;
  className?: string;
  buttonText?: string;
  buttonHref?: string;
  buttonVariant?: 'primary' | 'secondary' | 'outline';
  hideOnScroll?: boolean;
};

export default function FloatingHeader({
  navItems,
  logoUrl,
  logoText = 'Maily',
  className = '',
  buttonText = 'Sign Up',
  buttonHref = '/auth/register',
  buttonVariant = 'primary',
  hideOnScroll = true,
}: FloatingHeaderProps) {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [expandedItems, setExpandedItems] = useState<string[]>([]);
  const { theme, setTheme } = useTheme();
  const [headerVisible, setHeaderVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);

  // Handle scroll effects
  useEffect(() => {
    let ticking = false;
    let lastKnownScrollY = window.scrollY;
    
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      
      if (!ticking) {
        window.requestAnimationFrame(() => {
          // Detect if scrolled past a threshold (e.g., 50px)
          const isCurrentlyScrolled = currentScrollY > 50;
          setIsScrolled(isCurrentlyScrolled);
          
          // Hide header on scroll down, show on scroll up if hideOnScroll is true
          if (hideOnScroll) {
            if (currentScrollY > lastKnownScrollY && currentScrollY > 150) {
              setHeaderVisible(false);
            } else {
              setHeaderVisible(true);
            }
          }
          
          setLastScrollY(currentScrollY);
          ticking = false;
        });
        
        ticking = true;
      }
      
      lastKnownScrollY = currentScrollY;
    };
    
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [hideOnScroll, lastScrollY]);

  // Close mobile menu on resize to desktop size
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 768 && isMobileMenuOpen) {
        setIsMobileMenuOpen(false);
      }
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isMobileMenuOpen]);
  
  // Toggle theme
  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };
  
  // Toggle mobile menu
  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
    setExpandedItems([]);
  };
  
  // Toggle submenu item expansion
  const toggleExpanded = (label: string) => {
    setExpandedItems(prev => 
      prev.includes(label)
        ? prev.filter(item => item !== label)
        : [...prev, label]
    );
  };
  
  const getButtonClasses = () => {
    switch (buttonVariant) {
      case 'primary':
        return 'bg-gradient-to-r from-primary to-primary-600 text-white hover:opacity-90 transition-opacity';
      case 'secondary':
        return 'bg-secondary text-white hover:bg-secondary-600 transition-colors';
      case 'outline':
        return 'border border-primary text-primary hover:bg-primary/10 transition-colors';
      default:
        return 'bg-gradient-to-r from-primary to-primary-600 text-white hover:opacity-90 transition-opacity';
    }
  };

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled ? 'py-3' : 'py-5'
      } ${
        headerVisible ? 'translate-y-0' : '-translate-y-full'
      } ${className}`}
    >
      {/* Background with backdrop blur - glass morphism effect */}
      <div 
        className={`absolute inset-0 backdrop-blur-lg transition-opacity duration-300 ${
          isScrolled 
            ? 'bg-background/80 dark:bg-background-dark/80 shadow-lg' 
            : 'bg-transparent'
        }`} 
      />
      
      <div className="container mx-auto px-4 md:px-6 relative z-10">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link 
            href="/" 
            className="flex items-center gap-2 text-2xl font-medium text-foreground dark:text-foreground-dark transition-colors"
          >
            {logoUrl && (
              <img 
                src={logoUrl} 
                alt={`${logoText} logo`} 
                className="h-8 w-auto" 
              />
            )}
            <span className="font-semibold tracking-tight">{logoText}</span>
          </Link>
          
          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => (
              <div key={item.label} className="relative group">
                <Link
                  href={item.href}
                  className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors hover:bg-accent/10 dark:hover:bg-accent-dark/20 ${
                    item.children ? 'pr-7' : ''
                  }`}
                  target={item.isExternal ? '_blank' : undefined}
                  rel={item.isExternal ? 'noopener noreferrer' : undefined}
                >
                  {item.label}
                  {item.children && (
                    <ChevronRight className="h-4 w-4 absolute right-1 top-1/2 -translate-y-1/2 transition-transform group-hover:rotate-90" />
                  )}
                </Link>
                
                {/* Dropdown for desktop */}
                {item.children && (
                  <div className="absolute left-0 pt-2 w-48 hidden group-hover:block">
                    <div className="backdrop-blur-lg bg-background/95 dark:bg-background-dark/95 rounded-lg shadow-lg border border-border dark:border-border-dark overflow-hidden">
                      {item.children.map((child) => (
                        <Link
                          key={child.label}
                          href={child.href}
                          className="block px-4 py-2 text-sm hover:bg-accent/20 dark:hover:bg-accent-dark/20 transition-colors"
                          target={child.isExternal ? '_blank' : undefined}
                          rel={child.isExternal ? 'noopener noreferrer' : undefined}
                        >
                          {child.label}
                        </Link>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </nav>
          
          {/* Right side buttons */}
          <div className="flex items-center gap-2">
            {/* Theme toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-full hover:bg-accent/10 dark:hover:bg-accent-dark/20 transition-colors"
              aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            >
              {theme === 'dark' ? (
                <Sun className="h-5 w-5" />
              ) : (
                <Moon className="h-5 w-5" />
              )}
            </button>
            
            {/* Sign up/CTA button */}
            <Link
              href={buttonHref}
              className={`hidden md:inline-flex items-center px-4 py-2 text-sm font-medium rounded-lg ${getButtonClasses()}`}
            >
              {buttonText}
            </Link>
            
            {/* Mobile menu toggle */}
            <button
              onClick={toggleMobileMenu}
              className="md:hidden p-2 rounded-full hover:bg-accent/10 dark:hover:bg-accent-dark/20 transition-colors"
              aria-label="Toggle menu"
              aria-expanded={isMobileMenuOpen}
            >
              {isMobileMenuOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>
      </div>
      
      {/* Mobile menu */}
      <div
        className={`md:hidden fixed inset-x-0 top-[calc(var(--header-height,72px)-1px)] bottom-0 bg-background/95 dark:bg-background-dark/95 backdrop-blur-xl z-40 transform transition-transform duration-300 ease-in-out ${
          isMobileMenuOpen ? 'translate-y-0' : 'translate-y-full'
        }`}
      >
        <nav className="container h-full mx-auto px-4 py-6 overflow-y-auto">
          <div className="flex flex-col space-y-1">
            {navItems.map((item) => (
              <div key={item.label} className="py-1">
                {item.children ? (
                  <div>
                    <button
                      onClick={() => toggleExpanded(item.label)}
                      className="flex items-center justify-between w-full px-3 py-2 text-lg font-medium rounded-lg hover:bg-accent/10 dark:hover:bg-accent-dark/20"
                    >
                      {item.label}
                      <ChevronRight
                        className={`h-5 w-5 transition-transform ${
                          expandedItems.includes(item.label) ? 'rotate-90' : ''
                        }`}
                      />
                    </button>
                    
                    {expandedItems.includes(item.label) && (
                      <div className="ml-4 mt-1 space-y-1 border-l-2 border-border dark:border-border-dark pl-4">
                        {item.children.map((child) => (
                          <Link
                            key={child.label}
                            href={child.href}
                            className="block px-3 py-2 text-base rounded-lg hover:bg-accent/10 dark:hover:bg-accent-dark/20"
                            onClick={toggleMobileMenu}
                            target={child.isExternal ? '_blank' : undefined}
                            rel={child.isExternal ? 'noopener noreferrer' : undefined}
                          >
                            {child.label}
                          </Link>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <Link
                    href={item.href}
                    className="block px-3 py-2 text-lg font-medium rounded-lg hover:bg-accent/10 dark:hover:bg-accent-dark/20"
                    onClick={toggleMobileMenu}
                    target={item.isExternal ? '_blank' : undefined}
                    rel={item.isExternal ? 'noopener noreferrer' : undefined}
                  >
                    {item.label}
                  </Link>
                )}
              </div>
            ))}
            
            {/* Mobile CTA button */}
            <div className="pt-6">
              <Link
                href={buttonHref}
                className={`w-full inline-flex items-center justify-center px-4 py-3 text-base font-medium rounded-lg ${getButtonClasses()}`}
                onClick={toggleMobileMenu}
              >
                {buttonText}
              </Link>
            </div>
          </div>
        </nav>
      </div>
    </header>
  );
} 