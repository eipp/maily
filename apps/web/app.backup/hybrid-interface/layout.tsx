import type { Metadata } from 'next';
import { SplitScreenLayout } from '@/components/layout/SplitScreenLayout';
import { TopNavigation } from '@/components/navigation/TopNavigation';

export const metadata: Metadata = {
  title: 'JustMaily - Enterprise-Grade Hybrid Interface',
  description: 'Enterprise-Grade Hybrid Interface for Email Marketing with AI Mesh Network',
};

export default function HybridInterfaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background">
      <TopNavigation />
      <SplitScreenLayout>{children}</SplitScreenLayout>
    </div>
  );
}
