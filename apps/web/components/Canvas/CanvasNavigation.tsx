'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { LayoutDashboard, Plus, Settings, Layers, Brain } from 'lucide-react';

export interface CanvasNavigationProps {
  activeItem?: string;
  canvasId?: string;
}

export default function CanvasNavigation({ activeItem, canvasId }: CanvasNavigationProps) {
  // Define all possible navigation items
  const navigationItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      href: '/canvas/dashboard',
      icon: <LayoutDashboard className="h-5 w-5" />,
      showForNewCanvas: true,
    },
    {
      id: 'new',
      label: 'New Canvas',
      href: '/canvas/new',
      icon: <Plus className="h-5 w-5" />,
      showForNewCanvas: true,
    },
    {
      id: 'canvas',
      label: 'Canvas',
      href: `/canvas/${canvasId}`,
      icon: <Layers className="h-5 w-5" />,
      showForNewCanvas: false,
    },
    {
      id: 'ai-assistant',
      label: 'AI Assistant',
      href: `/canvas/${canvasId}/ai-assistant`,
      icon: <Brain className="h-5 w-5" />,
      showForNewCanvas: false,
    },
    {
      id: 'settings',
      label: 'Settings',
      href: '/canvas/settings',
      icon: <Settings className="h-5 w-5" />,
      showForNewCanvas: true,
    },
  ];

  // Filter items based on whether a canvas ID is provided
  const visibleItems = navigationItems.filter(
    (item) => canvasId || item.showForNewCanvas
  );

  return (
    <div className="border rounded-lg overflow-hidden bg-card">
      <nav className="flex items-center justify-center sm:justify-start p-2 space-x-1 sm:space-x-2">
        {visibleItems.map((item) => {
          const isActive = activeItem === item.id;

          // Replace placeholder with actual canvasId where needed
          const href = item.href.includes('${canvasId}') && canvasId
            ? item.href.replace('${canvasId}', canvasId)
            : item.href;

          return (
            <Link
              key={item.id}
              href={href}
              className={`
                flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium
                transition-colors whitespace-nowrap
                ${isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-muted'}
              `}
            >
              {item.icon}
              <span className="hidden sm:inline">{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
