'use client';

import { useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Button } from '@/components/Button';
import { Input } from '@/components/Input';
import { Twitter, Github, Linkedin, Mail, ExternalLink } from 'lucide-react';
import { analyticsService } from '@/services/analytics';

const footerSections = [
  {
    title: 'Product',
    links: [
      { name: 'Features', href: '/#features' },
      { name: 'Pricing', href: '/pricing' },
      { name: 'Dashboard', href: '/dashboard' },
      { name: 'Get Started', href: '/auth/signup' },
    ],
  },
  {
    title: 'Company',
    links: [
      { name: 'About', href: '/about' },
      { name: 'Blog', href: '/blog' },
      { name: 'Contact', href: '/contact' },
      { name: 'Support', href: '/support' },
    ],
  },
  {
    title: 'Resources',
    links: [
      { name: 'Documentation', href: '/docs' },
      { name: 'API Reference', href: '/api' },
      { name: 'Status', href: '/status' },
      { name: 'Help Center', href: '/help' },
    ],
  },
  {
    title: 'Legal',
    links: [
      { name: 'Privacy', href: '/legal/privacy' },
      { name: 'Terms', href: '/legal/terms' },
      { name: 'Security', href: '/legal/security' },
      { name: 'GDPR', href: '/legal/gdpr' },
    ],
  },
];

const socialLinks = [
  { name: 'Twitter', href: 'https://twitter.com', icon: Twitter },
  { name: 'GitHub', href: 'https://github.com', icon: Github },
  { name: 'LinkedIn', href: 'https://linkedin.com', icon: Linkedin },
];

export function MarketingFooter() {
  const [email, setEmail] = useState('');
  const [subscribeStatus, setSubscribeStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');

  const handleSubscribe = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email || subscribeStatus === 'loading') return;

    try {
      setSubscribeStatus('loading');

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

      // Track the event in analytics
      analyticsService.trackEvent('newsletter_subscribe', { email });

      setSubscribeStatus('success');
      setEmail('');

      setTimeout(() => setSubscribeStatus('idle'), 3000);
    } catch (error) {
      console.error('Newsletter subscription error:', error);
      setSubscribeStatus('error');
      setTimeout(() => setSubscribeStatus('idle'), 3000);
    }
  };

  return (
    <footer className="border-t bg-gray-900 text-gray-300">
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
            <form onSubmit={handleSubscribe} className="mt-4 lg:mt-0">
              <div className="flex gap-x-3">
                <Input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                  className="flex-1 bg-gray-700 text-white placeholder-gray-400"
                  required
                />
                <Button
                  type="submit"
                  variant="primary"
                  leftIcon={<Mail className="h-4 w-4" />}
                  isLoading={subscribeStatus === 'loading'}
                >
                  Subscribe
                </Button>
              </div>
              {subscribeStatus === 'success' && (
                <motion.p
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-2 text-sm text-green-400"
                >
                  Thanks for subscribing!
                </motion.p>
              )}
              {subscribeStatus === 'error' && (
                <motion.p
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-2 text-sm text-red-400"
                >
                  Something went wrong. Please try again.
                </motion.p>
              )}
            </form>
          </div>
        </div>

        {/* Main Footer Content */}
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4 lg:gap-12">
          {footerSections.map((section) => (
            <div key={section.title}>
              <h3 className="text-lg font-semibold text-white">{section.title}</h3>
              <ul className="mt-4 space-y-3">
                {section.links.map((link) => (
                  <li key={link.name}>
                    <Link
                      href={link.href}
                      className="group flex items-center text-sm text-gray-400 transition hover:text-white"
                    >
                      {link.name}
                      {link.href.startsWith('http') && (
                        <ExternalLink className="ml-1 h-3 w-3 opacity-0 transition-opacity group-hover:opacity-100" />
                      )}
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
            <div className="flex items-center space-x-4">
              <Link href="/" className="text-2xl font-bold text-white">
                Maily
              </Link>
              <span className="text-gray-500">
                © {new Date().getFullYear()} Maily. All rights reserved.
              </span>
            </div>
            <div className="flex space-x-6">
              {socialLinks.map((social) => {
                const Icon = social.icon;
                return (
                  <a
                    key={social.name}
                    href={social.href}
                    className="text-gray-400 transition hover:text-white"
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={() => analyticsService.trackEvent('social_link_click', { platform: social.name })}
                  >
                    <span className="sr-only">{social.name}</span>
                    <Icon className="h-6 w-6" />
                  </a>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
