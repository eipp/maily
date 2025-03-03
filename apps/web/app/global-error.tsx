"use client"

import React from 'react';
import config from '@/lib/config';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body className="bg-background">
        <div className="h-screen flex flex-col items-center justify-center p-4">
          <div className="max-w-md w-full bg-card rounded-lg shadow-lg p-6 text-center">
            <div className="h-20 w-20 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-6">
              <span className="text-red-500 text-3xl">🛑</span>
            </div>
            
            <h1 className="text-2xl font-bold mb-2">{config.meta.name} - Critical Error</h1>
            
            <div className="bg-muted rounded-md p-4 my-4 text-left overflow-auto max-h-40">
              <p className="text-sm font-mono text-muted-foreground break-all">
                {error.message || "A critical error occurred"}
              </p>
              {error.digest && (
                <p className="text-xs font-mono text-muted-foreground mt-2">
                  Error ID: {error.digest}
                </p>
              )}
            </div>
            
            <p className="text-muted-foreground mb-6">
              We apologize for the inconvenience. Our team has been notified of this issue.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={() => reset()}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
              >
                Try Again
              </button>
              
              <a
                href={`mailto:${config.meta.support}?subject=Critical Error in JustMaily&body=Error ID: ${error.digest || 'N/A'}%0D%0AError Message: ${error.message || 'Unknown error'}%0D%0A%0D%0APlease describe what you were doing when the error occurred:%0D%0A%0D%0A`}
                className="px-4 py-2 bg-muted text-muted-foreground rounded-md hover:bg-muted/90 transition-colors"
              >
                Contact Support
              </a>
            </div>
          </div>
          
          <div className="mt-8 text-center">
            <p className="text-sm text-muted-foreground">
              You can also try refreshing the page or returning to the homepage.
            </p>
            <div className="flex justify-center gap-4 mt-4">
              <button
                onClick={() => window.location.reload()}
                className="text-sm text-primary hover:underline"
              >
                Refresh Page
              </button>
              <span className="text-muted-foreground">•</span>
              <a
                href="/"
                className="text-sm text-primary hover:underline"
              >
                Go to Homepage
              </a>
            </div>
          </div>
        </div>
      </body>
    </html>
  );
}
