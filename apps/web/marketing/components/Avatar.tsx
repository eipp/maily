'use client';

import React, { useMemo } from 'react';
import { User } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AvatarProps {
  name: string;
  image?: string | null;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | number;
  className?: string;
  fallback?: React.ReactNode;
  status?: 'online' | 'offline' | 'away' | 'busy';
  border?: boolean;
  loading?: boolean;
}

const sizeMap = {
  xs: 24,
  sm: 32,
  md: 40,
  lg: 48,
  xl: 56,
};

const statusColorMap = {
  online: 'bg-green-500',
  offline: 'bg-gray-500',
  away: 'bg-yellow-500',
  busy: 'bg-red-500',
};

export function Avatar({
  name,
  image,
  size = 'md',
  className = '',
  fallback,
  status,
  border = false,
  loading = false,
}: AvatarProps) {
  const initials = useMemo(
    () =>
      name
        .split(' ')
        .map((part) => part[0])
        .join('')
        .toUpperCase()
        .slice(0, 2),
    [name]
  );

  const bgColor = useMemo(() => {
    // Generate a more unique color based on name
    const hash = name.split('').reduce((acc, char) => {
      return char.charCodeAt(0) + ((acc << 5) - acc);
    }, 0);

    const colors = [
      'bg-blue-500',
      'bg-green-500',
      'bg-purple-500',
      'bg-pink-500',
      'bg-indigo-500',
      'bg-orange-500',
      'bg-teal-500',
      'bg-cyan-500',
    ];

    return colors[Math.abs(hash) % colors.length];
  }, [name]);

  const dimensions = typeof size === 'number' ? size : sizeMap[size];
  const fontSize = dimensions * 0.4;

  if (loading) {
    return (
      <div
        className={cn(
          'animate-pulse rounded-full bg-gray-200',
          border && 'border-2 border-white ring-2 ring-gray-100',
          className
        )}
        style={{ width: dimensions, height: dimensions }}
      />
    );
  }

  const imageContent = image ? (
    <img
      src={image}
      alt={name}
      className={cn(
        'rounded-full object-cover',
        border && 'border-2 border-white ring-2 ring-gray-100',
        className
      )}
      style={{ width: dimensions, height: dimensions }}
      onError={(e) => {
        e.currentTarget.style.display = 'none';
        e.currentTarget.nextElementSibling?.removeAttribute('style');
      }}
    />
  ) : null;

  const fallbackContent = (
    <div
      className={cn(
        'flex items-center justify-center rounded-full text-white',
        bgColor,
        border && 'border-2 border-white ring-2 ring-gray-100',
        className
      )}
      style={{
        width: dimensions,
        height: dimensions,
        fontSize,
        display: image ? 'none' : undefined,
      }}
    >
      {fallback || initials || <User size={dimensions * 0.6} />}
    </div>
  );

  return (
    <div className="relative inline-flex">
      {imageContent}
      {fallbackContent}
      {status && (
        <span
          className={cn(
            'absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-white',
            statusColorMap[status]
          )}
        />
      )}
    </div>
  );
}
