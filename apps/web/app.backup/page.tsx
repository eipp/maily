"use client"

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import config from '@/lib/config';

export default function HomePage() {
  const router = useRouter();
  
  useEffect(() => {
    router.push('/hybrid-interface');
  }, [router]);
  
  return (
    <div className="h-screen flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-2">{config.meta.name}</h1>
        <p className="text-muted-foreground">Redirecting to Hybrid Interface...</p>
        <div className="mt-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
        </div>
      </div>
    </div>
  );
}
