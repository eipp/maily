import { useMemo } from 'react';

interface AvatarProps {
  name: string;
  image?: string;
  size?: number;
  className?: string;
}

export function Avatar({ name, image, size = 40, className = '' }: AvatarProps) {
  const initials = useMemo(() => {
    return name
      .split(' ')
      .map(part => part[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  }, [name]);

  const backgroundColor = useMemo(() => {
    const colors = [
      'bg-blue-500',
      'bg-green-500',
      'bg-yellow-500',
      'bg-red-500',
      'bg-purple-500',
      'bg-pink-500',
    ];
    const index = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    return colors[index % colors.length];
  }, [name]);

  if (image) {
    return (
      <div
        className={`relative overflow-hidden rounded-full ${className}`}
        style={{ width: size, height: size }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={image}
          alt={name}
          className="object-cover w-full h-full"
        />
      </div>
    );
  }

  return (
    <div
      className={`flex items-center justify-center rounded-full text-white font-medium ${backgroundColor} ${className}`}
      style={{
        width: size,
        height: size,
        fontSize: Math.max(size * 0.4, 12),
      }}
    >
      {initials}
    </div>
  );
} 