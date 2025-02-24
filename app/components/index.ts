import dynamic from 'next/dynamic';
import React from 'react';

// Dynamic imports with loading fallbacks
export const Canvas = dynamic(() => import('./Canvas'), {
  loading: () => <div className="animate-pulse bg-gray-200 rounded-lg h-64"></div>,
  ssr: false, // Disable SSR for canvas component
});

export const Chat = dynamic(() => import('./Chat'), {
  loading: () => <div className="animate-pulse bg-gray-100 rounded p-4 h-96"></div>,
});

export const Layout = dynamic(() => import('./Layout'), {
  loading: () => <div className="min-h-screen bg-gray-50"></div>,
  ssr: true, // Enable SSR for layout
});

// Add loading states for other components as needed
export const EmailEditor = dynamic(() => import('./EmailEditor'), {
  loading: () => <div className="animate-pulse bg-white rounded-lg p-6 h-screen"></div>,
});

export const ImageUploader = dynamic(() => import('./ImageUploader'), {
  loading: () => <div className="animate-pulse bg-gray-100 rounded-lg p-4 h-32"></div>,
  ssr: false, // Disable SSR for file operations
});

export const TemplateSelector = dynamic(() => import('./TemplateSelector'), {
  loading: () => <div className="animate-pulse grid grid-cols-3 gap-4 p-4"></div>,
});

const LoadingPulse: React.FC = () => (
  <div className="animate-pulse space-y-4">
    <div className="h-8 bg-gray-200 rounded w-1/4" />
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="h-32 bg-gray-200 rounded-lg" />
      ))}
    </div>
  </div>
);

// Analytics components with heavy computations
export const AnalyticsDashboard = dynamic(() => import('./AnalyticsDashboard'), {
  loading: () => <LoadingPulse />,
  ssr: true,
});

export const CampaignManager = dynamic(() => import('./CampaignManager'), {
  loading: () => <div className="animate-pulse bg-white p-6 rounded-lg h-96"></div>,
  ssr: true,
  prefetch: false,
});

// Campaign editor with rich text editing
export const CampaignEditor = dynamic(() => import('./CampaignEditor'), {
  loading: () => <div className="animate-pulse h-96 bg-gray-100 rounded-lg" />,
  ssr: false, // Rich text editor needs client-side only
});

// Heavy visualization components
export const DataVisualization = dynamic(() => import('./DataVisualization'), {
  loading: () => <div className="animate-pulse h-64 bg-gray-100 rounded-lg" />,
  ssr: false,
});

// Image processing components
export const ImageEditor = dynamic(() => import('./ImageEditor'), {
  loading: () => <div className="animate-pulse aspect-video bg-gray-100 rounded-lg" />,
  ssr: false,
});

// Authentication components
export const AuthForms = dynamic(() => import('./AuthForms'), {
  loading: () => <div className="animate-pulse h-96 bg-gray-50 rounded-lg" />,
  ssr: true,
});

// Settings and configuration components
export const SettingsPanel = dynamic(() => import('./SettingsPanel'), {
  loading: () => <div className="animate-pulse h-full bg-gray-50 rounded-lg" />,
  ssr: true,
});

// Utility components that are always needed
export { default as Layout } from './Layout';
export { default as Navigation } from './Navigation';
export { default as Footer } from './Footer'; 