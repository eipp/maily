import React from 'react';
import { useTranslation } from 'next-intl';

export interface SkipNavigationProps {
  /**
   * ID of the main content element to skip to
   */
  mainContentId?: string;

  /**
   * Additional skip links to include
   */
  links?: Array<{
    id: string;
    label: string;
  }>;

  /**
   * CSS class for the skip navigation container
   */
  className?: string;
}

/**
 * Skip navigation component for keyboard users
 * Allows users to skip to main content or other important sections
 */
export const SkipNavigation: React.FC<SkipNavigationProps> = ({
  mainContentId = 'main-content',
  links = [],
  className = '',
}) => {
  const { t } = useTranslation();

  return (
    <div
      className={`skip-navigation ${className}`}
      style={{
        position: 'absolute',
        top: '-9999px',
        left: '-9999px',
        zIndex: 9999,
      }}
    >
      <nav aria-label={t('Skip navigation')}>
        <ul
          style={{
            margin: 0,
            padding: 0,
            listStyle: 'none',
          }}
        >
          <li>
            <a
              href={`#${mainContentId}`}
              className="skip-link"
              style={{
                display: 'inline-block',
                padding: '0.5rem 1rem',
                background: 'var(--color-primary)',
                color: 'white',
                textDecoration: 'none',
                fontWeight: 'bold',
                position: 'absolute',
                top: '0',
                left: '0',
                transform: 'translateY(-100%)',
                transition: 'transform 0.3s',
                ':focus': {
                  transform: 'translateY(0)',
                  outline: '2px solid var(--color-focus)',
                  outlineOffset: '2px',
                },
              }}
              onFocus={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
              }}
              onBlur={(e) => {
                e.currentTarget.style.transform = 'translateY(-100%)';
              }}
            >
              {t('Skip to main content')}
            </a>
          </li>

          {links.map((link) => (
            <li key={link.id}>
              <a
                href={`#${link.id}`}
                className="skip-link"
                style={{
                  display: 'inline-block',
                  padding: '0.5rem 1rem',
                  background: 'var(--color-primary)',
                  color: 'white',
                  textDecoration: 'none',
                  fontWeight: 'bold',
                  position: 'absolute',
                  top: '0',
                  left: '0',
                  transform: 'translateY(-100%)',
                  transition: 'transform 0.3s',
                  ':focus': {
                    transform: 'translateY(0)',
                    outline: '2px solid var(--color-focus)',
                    outlineOffset: '2px',
                  },
                }}
                onFocus={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
                onBlur={(e) => {
                  e.currentTarget.style.transform = 'translateY(-100%)';
                }}
              >
                {t('Skip to {section}', { section: link.label })}
              </a>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
};

export default SkipNavigation;
