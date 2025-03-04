"use client"

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { LoadingPulse } from '@/components/LoadingPulse';
import config from '@/lib/config';

export default function HomePage() {
  const router = useRouter();
  
  useEffect(() => {
    // Preload critical pages for faster navigation
    const preloadHybridInterface = () => {
      const link = document.createElement('link');
      link.rel = 'prefetch';
      link.href = '/hybrid-interface';
      document.head.appendChild(link);
    };
    
    preloadHybridInterface();
    
    // Add a slight delay for a smoother experience
    const redirectTimer = setTimeout(() => {
      router.push('/hybrid-interface');
    }, 800);
    
    return () => clearTimeout(redirectTimer);
  }, [router]);
  
  return (
    <div className="flex h-screen items-center justify-center bg-gradient-to-b from-white to-gray-50 dark:from-gray-900 dark:to-gray-950">
      <motion.div 
        className="text-center"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <motion.h1 
          className="mb-2 bg-gradient-to-r from-primary-600 to-primary-400 bg-clip-text text-4xl font-bold text-transparent"
          initial={{ scale: 0.9 }}
          animate={{ scale: 1 }}
          transition={{ duration: 0.5, type: "spring" }}
        >
          {config.meta.name}
        </motion.h1>
        <p className="text-muted-foreground">Redirecting to Hybrid Interface...</p>
        <div className="mt-6 flex justify-center">
          <LoadingPulse size="md" color="primary" className="p-4" />
        </div>
      </motion.div>
    </div>
  );
}
