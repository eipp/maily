import { useState, useCallback } from 'react';

interface Toast {
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
}

export function useToast() {
  const [toast, setToast] = useState<Toast | null>(null);

  const showToast = useCallback((newToast: Toast) => {
    setToast(newToast);
    setTimeout(() => setToast(null), 5000); // Auto-dismiss after 5 seconds
  }, []);

  return {
    toast,
    showToast,
  };
}
