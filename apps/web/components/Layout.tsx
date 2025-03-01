'use client';

import React, { Suspense } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { usePathname } from 'next/navigation';
import { Navbar } from './Navbar';
import { Footer } from './Footer';
import { ErrorBoundary } from './ErrorBoundary';
import { AccessibilityProvider } from './AccessibilityProvider';
import { PrivacyProvider } from './PrivacyContext';

interface LayoutProps {
  children: React.ReactNode;
}

const pageTransition = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
};

function LoadingFallback() {
  return (
    <div className="flex min-h-[400px] items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  );
}

export function Layout({ children }: LayoutProps) {
  const pathname = usePathname();

  return (
    <ErrorBoundary fallback={<div>Something went wrong loading the page.</div>}>
      <AccessibilityProvider>
        <PrivacyProvider>
          <div className="flex min-h-screen flex-col">
            <Navbar />
            <main className="grow">
              <Suspense fallback={<LoadingFallback />}>
                <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                  {children}
                </div>
              </Suspense>
            </main>
            <Footer />
          </div>
        </PrivacyProvider>
      </AccessibilityProvider>
    </ErrorBoundary>
  );
}
