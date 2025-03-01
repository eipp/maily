import React, { useState, useEffect, createContext, useContext, ReactNode } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { XMarkIcon } from '@heroicons/react/24/outline'

// Toast types
export type ToastType = 'default' | 'success' | 'error' | 'warning' | 'info'

// Toast variants
export type ToastVariant = 'default' | 'destructive'

// Toast data structure
export interface Toast {
  id: string
  title: string
  description?: string
  type?: ToastType
  variant?: ToastVariant
  duration?: number
  onClose?: () => void
}

// Toast context
interface ToastContextType {
  toasts: Toast[]
  toast: (toast: Omit<Toast, 'id'>) => string
  dismiss: (id: string) => void
  clearAll: () => void
}

const ToastContext = createContext<ToastContextType | undefined>(undefined)

// Toast provider component
export interface ToastProviderProps {
  children: ReactNode
}

export const ToastProvider: React.FC<ToastProviderProps> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([])

  // Add a new toast
  const toast = (params: Omit<Toast, 'id'>): string => {
    const id = Math.random().toString(36).substring(2, 9)
    const newToast = { ...params, id }
    setToasts((prev) => [...prev, newToast])
    return id
  }

  // Remove a toast by id
  const dismiss = (id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }

  // Clear all toasts
  const clearAll = () => {
    setToasts([])
  }

  // Render the toasts and provider
  return (
    <ToastContext.Provider value={{ toasts, toast, dismiss, clearAll }}>
      {children}
      <AnimatePresence>
        {toasts.length > 0 && <Toasts toasts={toasts} dismiss={dismiss} />}
      </AnimatePresence>
    </ToastContext.Provider>
  )
}

// Toasts container component
interface ToastsProps {
  toasts: Toast[]
  dismiss: (id: string) => void
}

const Toasts: React.FC<ToastsProps> = ({ toasts, dismiss }) => {
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-xs w-full">
      <AnimatePresence>
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} dismiss={dismiss} />
        ))}
      </AnimatePresence>
    </div>
  )
}

// Individual toast component
interface ToastItemProps {
  toast: Toast
  dismiss: (id: string) => void
}

const ToastItem: React.FC<ToastItemProps> = ({ toast, dismiss }) => {
  // Auto-dismiss toast after duration
  useEffect(() => {
    const { id, duration = 5000 } = toast
    if (duration > 0) {
      const timer = setTimeout(() => {
        dismiss(id)
      }, duration)
      return () => clearTimeout(timer)
    }
  }, [toast, dismiss])

  // Handle manual dismiss
  const handleDismiss = () => {
    dismiss(toast.id)
    if (toast.onClose) {
      toast.onClose()
    }
  }

  // Get variant classes
  const getVariantClasses = (): string => {
    switch (toast.variant) {
      case 'destructive':
        return 'bg-destructive text-destructive-foreground'
      default:
        return 'bg-background text-foreground border'
    }
  }

  const variantClasses = getVariantClasses()

  // Icon based on type
  const getIcon = () => {
    switch (toast.type) {
      case 'success':
        return (
          <div className="h-6 w-6 rounded-full bg-green-500/20 flex items-center justify-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              className="w-4 h-4 text-green-600"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
          </div>
        )
      case 'error':
        return (
          <div className="h-6 w-6 rounded-full bg-red-500/20 flex items-center justify-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              className="w-4 h-4 text-red-600"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </div>
        )
      case 'warning':
        return (
          <div className="h-6 w-6 rounded-full bg-yellow-500/20 flex items-center justify-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              className="w-4 h-4 text-yellow-600"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
              />
            </svg>
          </div>
        )
      case 'info':
        return (
          <div className="h-6 w-6 rounded-full bg-blue-500/20 flex items-center justify-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              className="w-4 h-4 text-blue-600"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
              />
            </svg>
          </div>
        )
      default:
        return null
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -20, scale: 0.95 }}
      transition={{ duration: 0.2 }}
      className={`rounded-md shadow-lg ${variantClasses} flex items-start p-4 relative`}
    >
      <div className="flex items-start gap-3 w-full max-w-full">
        {getIcon()}
        <div className="flex-1 overflow-hidden">
          {toast.title && (
            <p className="font-medium text-sm leading-tight mb-1">{toast.title}</p>
          )}
          {toast.description && (
            <p className="text-xs opacity-90 overflow-hidden text-ellipsis whitespace-normal line-clamp-3">
              {toast.description}
            </p>
          )}
        </div>
        <button
          onClick={handleDismiss}
          className="text-foreground/50 hover:text-foreground"
          aria-label="Close toast"
        >
          <XMarkIcon className="w-4 h-4" />
        </button>
      </div>
    </motion.div>
  )
}

// Hook to use toast context
export const useToast = () => {
  const context = useContext(ToastContext)
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}
