import React from 'react';
import Link from 'next/link';
import { Button } from '@/components/Button';
import { Input } from '@/components/Input';
import { Facebook, Twitter, Instagram, Linkedin, Mail, ExternalLink } from 'lucide-react';

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
    { name: 'Privacy', href: '/privacy' },
    { name: 'Terms', href: '/terms' },
    { name: 'GDPR', href: '/gdpr' },
    { name: 'Security', href: '/security' },
  ],
};

export function Footer() {
  const handleNewsletterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implement newsletter subscription
  };

  return (
    <footer className="mt-auto bg-gray-900">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8 lg:py-16">
        {/* Newsletter Section */}
        <div className="mb-12 rounded-2xl bg-gray-800/50 p-6 lg:p-8">
          <div className="lg:grid lg:grid-cols-3 lg:gap-8">
            <div className="lg:col-span-2">
              <h3 className="text-xl font-semibold text-white">
                Subscribe to our newsletter
              </h3>
              <p className="mt-2 text-sm text-gray-400">
                Get the latest updates, articles, and resources delivered straight to your inbox.
              </p>
            </div>
            <form onSubmit={handleNewsletterSubmit} className="mt-4 lg:mt-0">
              <div className="flex gap-x-3">
                <Input
                  type="email"
                  placeholder="Enter your email"
                  className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 placeholder:text-gray-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-700"
                  required
                />
                <Button type="submit" variant="primary" leftIcon={<Mail className="h-4 w-4" />}>
                  Subscribe
                </Button>
              </div>
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
            <div className="flex items-center space-x-2">
              <Facebook className="size-3 text-gray-400 hover:text-gray-500" />
              <Twitter className="size-3 text-gray-400 hover:text-gray-500" />
              <Instagram className="size-3 text-gray-400 hover:text-gray-500" />
            </div>
            <p className="text-sm text-gray-400">
              &copy; {new Date().getFullYear()} Maily. All rights reserved.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
