import React from 'react';
import ReactDOM from 'react-dom';

if (process.env.NODE_ENV !== 'production') {
  const axe = require('@axe-core/react');
  axe(React, ReactDOM, 1000);
}

interface AccessibilityProviderProps {
  children: React.ReactNode;
}

export function AccessibilityProvider({ children }: AccessibilityProviderProps) {
  React.useEffect(() => {
    // Add keyboard navigation outline styles
    const style = document.createElement('style');
    style.innerHTML = `
      *:focus-visible {
        outline: 2px solid #4f46e5;
        outline-offset: 2px;
      }
      
      .skip-to-content {
        position: absolute;
        top: -40px;
        left: 0;
        background: #4f46e5;
        color: white;
        padding: 8px;
        z-index: 100;
        transition: top 0.2s;
      }
      
      .skip-to-content:focus {
        top: 0;
      }
    `;
    document.head.appendChild(style);

    return () => {
      document.head.removeChild(style);
    };
  }, []);

  return (
    <>
      <a href="#main-content" className="skip-to-content">
        Skip to main content
      </a>
      {children}
    </>
  );
} 