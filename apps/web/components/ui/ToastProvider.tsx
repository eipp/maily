'use client';

import React from 'react';
import { Toaster as HotToaster } from 'react-hot-toast';

export default function ToastProvider() {
  return (
    <div>
      <HotToaster
        position="top-right"
        toastOptions={{
          duration: 5000,
          style: {
            background: '#fff',
            color: '#333',
          },
        }}
      />
    </div>
  );
}
