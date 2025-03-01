import React from 'react';

interface SkipNavLinkProps {
  targetId: string;
  className?: string;
}

/**
 * A skip navigation link that allows keyboard users to bypass navigation
 * and jump directly to the main content.
 *
 * This component should be placed at the very beginning of the page.
 */
const SkipNavLink: React.FC<SkipNavLinkProps> = ({
  targetId,
  className = ''
}) => {
  // Base styles for the skip link
  const baseStyles = `
    absolute top-0 left-0 p-2 bg-blue-600 text-white font-medium
    transform -translate-y-full focus:translate-y-0 transition-transform
    z-50 focus:outline-none focus:ring-2 focus:ring-blue-500
  `;

  return (
    <a
      href={`#${targetId}`}
      className={`${baseStyles} ${className}`.trim()}
      data-testid="skip-nav-link"
    >
      Skip to main content
    </a>
  );
};

/**
 * The target element for the skip navigation link.
 * This component should be placed at the beginning of the main content.
 */
export const SkipNavTarget: React.FC<{ id: string }> = ({ id }) => {
  return <div id={id} tabIndex={-1} />;
};

export default SkipNavLink;
