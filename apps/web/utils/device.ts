/**
 * Utility functions to detect device capabilities
 */

/**
 * Checks if the current device is a touch device
 * This function should only be called on the client side
 */
export function isTouchDevice(): boolean {
  if (typeof window === 'undefined') return false;
  
  return (
    'ontouchstart' in window ||
    navigator.maxTouchPoints > 0 ||
    // @ts-ignore - navigator.msMaxTouchPoints is not in the TypeScript types
    navigator.msMaxTouchPoints > 0
  );
}

/**
 * Checks if the current device is a mobile device based on screen size
 * This function should only be called on the client side
 */
export function isMobileDevice(): boolean {
  if (typeof window === 'undefined') return false;
  
  return window.innerWidth < 768;
}

/**
 * Checks if the current device is a tablet device based on screen size
 * This function should only be called on the client side
 */
export function isTabletDevice(): boolean {
  if (typeof window === 'undefined') return false;
  
  return window.innerWidth >= 768 && window.innerWidth < 1024;
}

/**
 * Gets the device type based on screen size
 * This function should only be called on the client side
 */
export function getDeviceType(): 'mobile' | 'tablet' | 'desktop' {
  if (isMobileDevice()) return 'mobile';
  if (isTabletDevice()) return 'tablet';
  return 'desktop';
}