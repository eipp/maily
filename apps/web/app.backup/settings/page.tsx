import React from 'react';
import ModelSettings from '@/components/settings/ModelSettings';

export const metadata = {
  title: 'Settings - Maily',
  description: 'Configure your AI model preferences and API keys',
};

export default function SettingsPage() {
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-4xl font-bold mb-2">Settings</h1>
      <p className="text-muted-foreground mb-8">
        Configure your preferences and API keys for Maily's AI features
      </p>

      <div className="space-y-12">
        <ModelSettings />
      </div>
    </div>
  );
}
