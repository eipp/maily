'use client';

import React from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import CanvasNavigation from '@/components/Canvas/CanvasNavigation';

export interface CanvasLayoutProps {
  children: React.ReactNode;
  title: string;
  description?: string;
  showBackButton?: boolean;
  backButtonUrl?: string;
  backButtonText?: string;
  activeNavItem?: string;
  maxWidth?: 'default' | 'small' | 'medium' | 'large' | 'full';
  canvasId?: string;
}

export default function CanvasLayout({
  children,
  title,
  description,
  showBackButton = false,
  backButtonUrl = '/canvas/dashboard',
  backButtonText = 'Back to Canvas Dashboard',
  activeNavItem,
  maxWidth = 'default',
  canvasId
}: CanvasLayoutProps) {
  // Map maxWidth to appropriate classes
  const maxWidthClasses = {
    small: 'max-w-3xl',
    medium: 'max-w-5xl',
    large: 'max-w-7xl',
    default: 'max-w-5xl',
    full: 'max-w-full',
  };

  return (
    <div className={`mx-auto px-4 py-8 ${maxWidthClasses[maxWidth]}`}>
      <div className="mb-6">
        {/* Title and back button */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold">{title}</h1>
            {description && <p className="text-muted-foreground mt-1">{description}</p>}
          </div>

          {showBackButton && (
            <Button variant="outline" asChild>
              <Link href={backButtonUrl} className="flex items-center">
                <ArrowLeft className="mr-2 h-4 w-4" />
                {backButtonText}
              </Link>
            </Button>
          )}
        </div>

        {/* Navigation */}
        <CanvasNavigation activeItem={activeNavItem} canvasId={canvasId} />
      </div>

      {/* Main content */}
      <main>{children}</main>
    </div>
  );
}
