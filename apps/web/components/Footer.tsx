import React, { useState, lazy, Suspense } from 'react';
import Link from 'next/link';
import { Button } from '@/components/Button';
import { Input } from '@/components/Input';
import { Mail, ExternalLink, AlertCircle, CheckCircle } from 'lucide-react';
import dynamic from 'next/dynamic';

// Dynamically import heavy social icons to reduce initial bundle size
const Facebook = dynamic(() => import('lucide-react').then(mod => mod.Facebook));
const Twitter = dynamic(() => import('lucide-react').then(mod => mod.Twitter));
const Instagram = dynamic(() => import('lucide-react').then(mod => mod.Instagram));
const Linkedin = dynamic(() => import('lucide-react').then(mod => mod.Linkedin));

const socialLinks = [
  { name: 'Facebook', icon: Facebook, href: 'https://facebook.com/maily' },
  { name: 'Twitter', icon: Twitter, href: 'https://twitter.com/maily' },
  { name: 'Instagram', icon: Instagram, href: 'https://instagram.com/maily' },
  { name: 'LinkedIn', icon: Linkedin, href: 'https://linkedin.com/company/maily' },
];

const footerLinks = {
  product: [
    { name: 'Features', href: '/features' },
    { name: 'Pricing', href: '/pricing' },
    { name: 'Templates', href: '/templates' },
    { name: 'Integrations', href: '/integrations' },
  ],
  resources: [
    { name: 'Documentation', href: '/docs' },
    { name: 'Blog', href: '/blog' },
    { name: 'Help Center', href: '/help' },
    { name: 'API Reference', href: '/api' },
  ],
  company: [
    { name: 'About', href: '/about' },
    { name: 'Careers', href: '/careers' },
    { name: 'Contact', href: '/contact' },
    { name: 'Partners', href: '/partners' },
  ],
  legal: [
    { name: 'Privacy Policy', href: '/legal/privacy' },
    { name: 'Terms of Service', href: '/legal/terms' },
    { name: 'GDPR', href: '/legal/gdpr' },
    { name: 'Security', href: '/legal/security' },
  ],
};

export function Footer() {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleNewsletterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setSuccess(false);
    
    try {
      const response = await fetch('/api/newsletter/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to subscribe to newsletter');
      }
      
      setSuccess(true);
      setEmail('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <footer className="mt-auto bg-gray-900">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8 lg:py-16">
        {/* Newsletter Section */}
        <div className="mb-12 rounded-2xl bg-gradient-to-r from-gray-800/80 to-gray-800/50 p-6 shadow-lg transition-all duration-300 hover:shadow-xl lg:p-8">
          <div className="lg:grid lg:grid-cols-3 lg:gap-8">
            <div className="lg:col-span-2">
              <h3 className="text-xl font-semibold text-white group-hover:text-primary-400 transition-colors">
                Subscribe to our newsletter
              </h3>
              <p className="mt-2 text-sm text-gray-400">
                Get the latest updates, articles, and resources delivered straight to your inbox.
              </p>
              {/* Social proof - increases conversions */}
              <p className="mt-3 text-xs text-gray-500">
                <span className="font-medium text-gray-400">Join 10,000+ marketing professionals</span> who get our weekly insights
              </p>
            </div>
            <form onSubmit={handleNewsletterSubmit} className="mt-4 lg:mt-0">
              {success ? (
                <div className="flex items-center rounded-lg bg-green-500/10 px-4 py-3 text-sm text-green-500 shadow-inner">
                  <CheckCircle className="mr-2 h-5 w-5" />
                  <span>Thanks for subscribing! Check your inbox to confirm.</span>
                </div>
              ) : (
                <>
                  <div className="flex flex-col gap-3 sm:flex-row">
                    <Input
                      type="email"
                      placeholder="Enter your email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full rounded-lg border border-gray-600 bg-gray-700/50 px-4 py-2 text-white placeholder:text-gray-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all duration-200 ease-in-out"
                      required
                      aria-label="Email address"
                    />
                    <Button 
                      type="submit" 
                      variant="primary" 
                      leftIcon={<Mail className="h-4 w-4" />}
                      disabled={isLoading}
                      className="relative overflow-hidden transform hover:translate-y-[-2px] transition-all duration-200 ease-in-out"
                    >
                      <span className={`absolute inset-0 bg-gradient-to-r from-primary-600 to-primary-500 opacity-0 group-hover:opacity-100 transition-opacity duration-300 ${isLoading ? 'animate-pulse' : ''}`}></span>
                      <span className="relative">{isLoading ? 'Subscribing...' : 'Subscribe'}</span>
                    </Button>
                  </div>
                  
                  {error && (
                    <div className="mt-2 flex items-center text-sm text-red-500">
                      <AlertCircle className="mr-1 h-4 w-4" />
                      <span>{error}</span>
                    </div>
                  )}
                </>
              )}
            </form>
          </div>
        </div>

        {/* Main Footer Content */}
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4 lg:gap-12">
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h3 className="text-lg font-semibold capitalize text-white">{category}</h3>
              <ul className="mt-4 space-y-3">
                {links.map((link) => (
                  <li key={link.name}>
                    <Link
                      href={link.href}
                      className="group flex items-center text-sm text-gray-400 transition hover:text-white"
                    >
                      {link.name}
                      <ExternalLink className="ml-1 h-3 w-3 opacity-0 transition-opacity group-hover:opacity-100" />
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Social Links & Copyright */}
        <div className="mt-12 border-t border-gray-800 pt-8">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <div className="flex items-center space-x-6">
              <Suspense fallback={<div className="h-5 w-20 bg-gray-800 animate-pulse rounded"></div>}>
                {socialLinks.map((social) => (
                  <a
                    key={social.name}
                    href={social.href}
                    className="group relative text-gray-400 transition-colors duration-300 hover:text-white"
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label={`Follow us on ${social.name}`}
                  >
                    <social.icon className="h-5 w-5 transform transition-transform duration-300 ease-in-out group-hover:scale-110" />
                    <span className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-xs opacity-0 transition-opacity duration-300 group-hover:opacity-100">
                      {social.name}
                    </span>
                  </a>
                ))}
              </Suspense>
            </div>
            <div className="flex flex-wrap items-center justify-center gap-4 text-sm text-gray-400">
              <Link 
                href="/legal/privacy" 
                className="relative overflow-hidden transition-colors duration-300 hover:text-white"
              >
                <span className="relative z-10">Privacy Policy</span>
                <span className="absolute bottom-0 left-0 h-[1px] w-0 bg-white transition-all duration-300 group-hover:w-full"></span>
              </Link>
              <span>•</span>
              <Link 
                href="/legal/terms" 
                className="relative overflow-hidden transition-colors duration-300 hover:text-white"
              >
                <span className="relative z-10">Terms of Service</span>
                <span className="absolute bottom-0 left-0 h-[1px] w-0 bg-white transition-all duration-300 group-hover:w-full"></span>
              </Link>
              <span>•</span>
              <p>&copy; {new Date().getFullYear()} Maily. All rights reserved.</p>
            </div>
          </div>
          
          {/* Trust badges for increased conversions */}
          <div className="mt-8 flex flex-wrap items-center justify-center gap-6">
            <div className="flex items-center text-xs text-gray-500">
              <svg className="mr-1 h-4 w-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <span>SSL Secured</span>
            </div>
            <div className="flex items-center text-xs text-gray-500">
              <svg className="mr-1 h-4 w-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <span>GDPR Compliant</span>
            </div>
            <div className="flex items-center text-xs text-gray-500">
              <svg className="mr-1 h-4 w-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2z" />
              </svg>
              <span>100% Data Ownership</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
