analyimport React, { ReactNode } from 'react';
import Link from 'next/link';
import SkipNavLink, { SkipNavTarget } from '../../components/accessibility/SkipNavLink';

interface AccessibilityShowcaseLayoutProps {
  children: ReactNode;
}

/**
 * Layout component for the accessibility showcase
 * This layout includes a skip navigation link and a simple header with navigation
 */
export default function AccessibilityShowcaseLayout({ children }: AccessibilityShowcaseLayoutProps) {
  return (
    <>
      <SkipNavLink targetId="main-content" />

      <div className="min-h-screen flex flex-col">
        <header className="bg-blue-600 text-white shadow-md">
          <div className="max-w-6xl mx-auto px-4 py-4 flex flex-wrap items-center justify-between">
            <div className="flex items-center">
              <Link href="/" className="text-xl font-bold hover:text-blue-100 transition-colors">
                Maily
              </Link>
              <span className="mx-2">|</span>
              <h1 className="text-lg font-medium">Accessibility Showcase</h1>
            </div>

            <nav>
              <ul className="flex space-x-4">
                <li>
                  <Link
                    href="/"
                    className="px-3 py-2 rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-white"
                  >
                    Home
                  </Link>
                </li>
                <li>
                  <Link
                    href="/accessibility-showcase"
                    className="px-3 py-2 rounded bg-blue-700 hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-white"
                    aria-current="page"
                  >
                    Accessibility
                  </Link>
                </li>
                <li>
                  <a
                    href="https://www.w3.org/WAI/WCAG21/quickref/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-3 py-2 rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-white"
                  >
                    WCAG Guidelines
                  </a>
                </li>
              </ul>
            </nav>
          </div>
        </header>

        <main id="main-content" className="flex-grow">
          <SkipNavTarget id="main-content" />
          {children}
        </main>

        <footer className="bg-gray-100 border-t border-gray-200 py-6">
          <div className="max-w-6xl mx-auto px-4 text-center text-gray-600">
            <p>
              Maily Accessibility Components - Implemented as part of Sprint 7
            </p>
            <p className="mt-2 text-sm">
              These components follow <a
                href="https://www.w3.org/WAI/WCAG21/quickref/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
              >
                WCAG 2.1 AA guidelines
              </a> for web accessibility.
            </p>
          </div>
        </footer>
      </div>
    </>
  );
}
