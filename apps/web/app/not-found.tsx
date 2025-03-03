import React from 'react';
import Link from 'next/link';
import config from '@/lib/config';

export default function NotFound() {
  return (
    <div className="h-screen flex flex-col items-center justify-center bg-background p-4">
      <div className="max-w-md w-full text-center">
        <div className="mb-6">
          <span className="text-8xl font-bold text-primary">404</span>
        </div>
        
        <h1 className="text-3xl font-bold mb-4">{config.meta.name}</h1>
        <h2 className="text-2xl font-semibold mb-6">Page Not Found</h2>
        
        <p className="text-muted-foreground mb-8">
          The page you are looking for doesn't exist or has been moved.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/"
            className="px-6 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            Go to Dashboard
          </Link>
          
          <Link
            href="/hybrid-interface"
            className="px-6 py-3 bg-muted text-muted-foreground rounded-md hover:bg-muted/90 transition-colors"
          >
            Hybrid Interface
          </Link>
        </div>
      </div>
      
      <div className="mt-16 text-center">
        <p className="text-sm text-muted-foreground mb-2">
          Need help? Contact our support team.
        </p>
        <a
          href={`mailto:${config.meta.support}`}
          className="text-sm text-primary hover:underline"
        >
          {config.meta.support}
        </a>
      </div>
      
      {/* Decorative elements */}
      <div className="absolute top-1/4 left-1/4 transform -translate-x-1/2 -translate-y-1/2 opacity-5">
        <div className="text-[20rem] font-bold">4</div>
      </div>
      <div className="absolute bottom-1/4 right-1/4 transform translate-x-1/2 translate-y-1/2 opacity-5">
        <div className="text-[20rem] font-bold">4</div>
      </div>
    </div>
  );
}
