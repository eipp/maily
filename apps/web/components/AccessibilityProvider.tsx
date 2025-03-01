import React, { createContext, useContext, useState, useEffect } from 'react';
import type { FC, ReactNode } from 'react';
import ReactDOM from 'react-dom';

// Load axe-core in development only
if (process.env.NODE_ENV !== 'production') {
  void import('@axe-core/react').then(axe => {
    axe.default(React, ReactDOM, 1000);
  });
}

interface AccessibilityContextType {
  highContrast: boolean;
  toggleHighContrast: () => void;
  fontSize: number;
  increaseFontSize: () => void;
  decreaseFontSize: () => void;
}

const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined);

interface AccessibilityProviderProps {
  children: ReactNode;
}

export const AccessibilityProvider: FC<AccessibilityProviderProps> = ({ children }) => {
  const [highContrast, setHighContrast] = useState(false);
  const [fontSize, setFontSize] = useState(16);

  const toggleHighContrast = () => {
    setHighContrast((prev) => !prev);
  };

  const increaseFontSize = () => {
    setFontSize((prev) => Math.min(prev + 2, 24));
  };

  const decreaseFontSize = () => {
    setFontSize((prev) => Math.max(prev - 2, 12));
  };

  useEffect(() => {
    document.documentElement.style.fontSize = `${fontSize}px`;
  }, [fontSize]);

  useEffect(() => {
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
        padding: 8px 16px;
        z-index: 1000;
        transition: top 0.2s ease-in-out;
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
    <AccessibilityContext.Provider
      value={{
        highContrast,
        toggleHighContrast,
        fontSize,
        increaseFontSize,
        decreaseFontSize,
      }}
    >
      <div className={`${highContrast ? 'bg-black text-white' : 'bg-white text-black'}`}>
        <button
          className="fixed left-4 top-4 -translate-y-full bg-primary-600 px-4 py-2 text-white transition focus:translate-y-0 focus:outline-none"
          onClick={toggleHighContrast}
        >
          Skip to content
        </button>
        {children}
      </div>
    </AccessibilityContext.Provider>
  );
};

export const useAccessibility = () => {
  const context = useContext(AccessibilityContext);
  if (context === undefined) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider');
  }
  return context;
};

AccessibilityProvider.displayName = 'AccessibilityProvider';

export default AccessibilityProvider;
