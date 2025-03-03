import React from 'react';
import AccessibilityShowcase from '../../components/accessibility/AccessibilityShowcase';
import AxeAccessibility from '../../components/accessibility/AxeAccessibility';

/**
 * Page component for the accessibility showcase
 * This page demonstrates all the accessible components implemented in Sprint 7
 */
export default function AccessibilityShowcasePage() {
  return (
    <AxeAccessibility>
      <main className="min-h-screen bg-white">
        <AccessibilityShowcase />
      </main>
    </AxeAccessibility>
  );
}

// Metadata for the page
export const metadata = {
  title: 'Accessibility Components Showcase | Maily',
  description: 'A showcase of accessible components implemented in Maily following WCAG 2.1 AA guidelines.',
};
