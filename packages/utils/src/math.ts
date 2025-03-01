/**
 * Math utility functions
 */

/**
 * Clamp a number between min and max
 * @param value Value to clamp
 * @param min Minimum value
 * @param max Maximum value
 * @returns Clamped value
 */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/**
 * Linear interpolation between two values
 * @param a Start value
 * @param b End value
 * @param t Interpolation factor (0-1)
 * @returns Interpolated value
 */
export function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

/**
 * Map a value from one range to another
 * @param value Value to map
 * @param fromMin Input range minimum
 * @param fromMax Input range maximum
 * @param toMin Output range minimum
 * @param toMax Output range maximum
 * @param clamp Whether to clamp the output to the range
 * @returns Mapped value
 */
export function map(
  value: number,
  fromMin: number,
  fromMax: number,
  toMin: number,
  toMax: number,
  clamp: boolean = false
): number {
  const normalized = (value - fromMin) / (fromMax - fromMin);
  const mapped = toMin + normalized * (toMax - toMin);

  if (clamp) {
    if (toMin < toMax) {
      return Math.min(Math.max(mapped, toMin), toMax);
    } else {
      return Math.min(Math.max(mapped, toMax), toMin);
    }
  }

  return mapped;
}

/**
 * Normalize a value to the range [0, 1]
 * @param value Value to normalize
 * @param min Minimum value
 * @param max Maximum value
 * @returns Normalized value
 */
export function normalize(value: number, min: number, max: number): number {
  return (value - min) / (max - min);
}

/**
 * Check if a number is between two values
 * @param value Value to check
 * @param min Minimum value
 * @param max Maximum value
 * @param inclusive Whether to include min and max in the range
 * @returns Whether the value is in range
 */
export function inRange(
  value: number,
  min: number,
  max: number,
  inclusive: boolean = true
): boolean {
  return inclusive
    ? value >= min && value <= max
    : value > min && value < max;
}

/**
 * Round a number to a specific precision
 * @param value Value to round
 * @param precision Number of decimal places
 * @returns Rounded value
 */
export function round(value: number, precision: number = 0): number {
  const factor = Math.pow(10, precision);
  return Math.round(value * factor) / factor;
}

/**
 * Calculate the distance between two points in 2D space
 * @param x1 First point x coordinate
 * @param y1 First point y coordinate
 * @param x2 Second point x coordinate
 * @param y2 Second point y coordinate
 * @returns Distance between points
 */
export function distance(
  x1: number,
  y1: number,
  x2: number,
  y2: number
): number {
  return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
}

/**
 * Calculate the average of an array of numbers
 * @param values Array of numbers
 * @returns Average value
 */
export function average(values: number[]): number {
  if (values.length === 0) {
    return 0;
  }

  return sum(values) / values.length;
}

/**
 * Calculate the sum of an array of numbers
 * @param values Array of numbers
 * @returns Sum of values
 */
export function sum(values: number[]): number {
  return values.reduce((acc, val) => acc + val, 0);
}

/**
 * Generate a random number between min and max
 * @param min Minimum value
 * @param max Maximum value
 * @param integer Whether to return an integer
 * @returns Random number
 */
export function random(
  min: number,
  max: number,
  integer: boolean = false
): number {
  const value = min + Math.random() * (max - min);
  return integer ? Math.floor(value) : value;
}

/**
 * Calculate the median of an array of numbers
 * @param values Array of numbers
 * @returns Median value
 */
export function median(values: number[]): number {
  if (values.length === 0) {
    return 0;
  }

  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);

  return sorted.length % 2 === 0
    ? (sorted[mid - 1] + sorted[mid]) / 2
    : sorted[mid];
}

/**
 * Calculate the mode of an array of numbers
 * @param values Array of numbers
 * @returns Mode value(s)
 */
export function mode(values: number[]): number[] {
  if (values.length === 0) {
    return [];
  }

  const counts = new Map<number, number>();
  let maxCount = 0;

  // Count occurrences
  for (const value of values) {
    const count = (counts.get(value) || 0) + 1;
    counts.set(value, count);
    maxCount = Math.max(maxCount, count);
  }

  // Find values with maximum count
  return Array.from(counts.entries())
    .filter(([_, count]) => count === maxCount)
    .map(([value]) => value);
}

/**
 * Calculate standard deviation of an array of numbers
 * @param values Array of numbers
 * @param sample Whether to calculate sample standard deviation
 * @returns Standard deviation
 */
export function standardDeviation(
  values: number[],
  sample: boolean = true
): number {
  if (values.length <= 1) {
    return 0;
  }

  const avg = average(values);
  const squareDiffs = values.map(value => Math.pow(value - avg, 2));
  const divisor = sample ? values.length - 1 : values.length;

  return Math.sqrt(sum(squareDiffs) / divisor);
}

/**
 * Calculate variance of an array of numbers
 * @param values Array of numbers
 * @param sample Whether to calculate sample variance
 * @returns Variance
 */
export function variance(values: number[], sample: boolean = true): number {
  if (values.length <= 1) {
    return 0;
  }

  const avg = average(values);
  const squareDiffs = values.map(value => Math.pow(value - avg, 2));
  const divisor = sample ? values.length - 1 : values.length;

  return sum(squareDiffs) / divisor;
}

/**
 * Calculate percentile of an array of numbers
 * @param values Array of numbers
 * @param percentile Percentile to calculate (0-100)
 * @returns Percentile value
 */
export function percentile(values: number[], percentile: number): number {
  if (values.length === 0) {
    return 0;
  }

  const sorted = [...values].sort((a, b) => a - b);
  const index = Math.ceil(percentile / 100 * sorted.length) - 1;
  return sorted[Math.max(0, Math.min(sorted.length - 1, index))];
}

/**
 * Generate n evenly spaced values within a range
 * @param min Minimum value
 * @param max Maximum value
 * @param steps Number of steps
 * @param includeMax Whether to include the maximum value
 * @returns Array of values
 */
export function linspace(
  min: number,
  max: number,
  steps: number,
  includeMax: boolean = true
): number[] {
  const adjustedSteps = includeMax ? steps - 1 : steps;

  return Array.from({ length: steps }, (_, i) =>
    min + i * (max - min) / adjustedSteps
  );
}

/**
 * Convert degrees to radians
 * @param degrees Angle in degrees
 * @returns Angle in radians
 */
export function toRadians(degrees: number): number {
  return degrees * (Math.PI / 180);
}

/**
 * Convert radians to degrees
 * @param radians Angle in radians
 * @returns Angle in degrees
 */
export function toDegrees(radians: number): number {
  return radians * (180 / Math.PI);
}

/**
 * Check if a number is even
 * @param n Number to check
 * @returns Whether the number is even
 */
export function isEven(n: number): boolean {
  return n % 2 === 0;
}

/**
 * Check if a number is odd
 * @param n Number to check
 * @returns Whether the number is odd
 */
export function isOdd(n: number): boolean {
  return n % 2 !== 0;
}

/**
 * Calculate greatest common divisor of two numbers
 * @param a First number
 * @param b Second number
 * @returns Greatest common divisor
 */
export function gcd(a: number, b: number): number {
  a = Math.abs(a);
  b = Math.abs(b);

  while (b !== 0) {
    const temp = b;
    b = a % b;
    a = temp;
  }

  return a;
}

/**
 * Calculate least common multiple of two numbers
 * @param a First number
 * @param b Second number
 * @returns Least common multiple
 */
export function lcm(a: number, b: number): number {
  return Math.abs(a * b) / gcd(a, b);
}
