/**
 * Array utility functions
 */

/**
 * Create a unique array by removing duplicate elements
 * @param array Array with potential duplicates
 * @returns Array with unique elements
 */
export function unique<T>(array: T[]): T[] {
  return [...new Set(array)];
}

/**
 * Group array elements by a key function
 * @param array Array to group
 * @param keyFn Function to extract group key
 * @returns Record of groups
 */
export function groupBy<T, K extends string | number | symbol>(
  array: T[],
  keyFn: (item: T) => K
): Record<K, T[]> {
  return array.reduce((result, item) => {
    const key = keyFn(item);
    result[key] = result[key] || [];
    result[key].push(item);
    return result;
  }, {} as Record<K, T[]>);
}

/**
 * Chunk array into groups of specified size
 * @param array Array to chunk
 * @param size Chunk size
 * @returns Array of chunks
 */
export function chunk<T>(array: T[], size: number): T[][] {
  return Array.from(
    { length: Math.ceil(array.length / size) },
    (_, index) => array.slice(index * size, (index + 1) * size)
  );
}

/**
 * Flatten a nested array structure (one level)
 * @param array Array of arrays
 * @returns Flattened array
 */
export function flatten<T>(array: T[][]): T[] {
  return array.reduce((result, items) => result.concat(items), [] as T[]);
}

/**
 * Deep flatten a nested array structure (recursive)
 * @param array Deeply nested array
 * @returns Flattened array
 */
export function flattenDeep<T>(array: any[]): T[] {
  return array.reduce((result, item) => result.concat(Array.isArray(item) ? flattenDeep(item) : [item]), [] as T[]);
}

/**
 * Partition array into two groups based on predicate
 * @param array Array to partition
 * @param predicate Function to test elements
 * @returns Tuple of [matching, non-matching]
 */
export function partition<T>(array: T[], predicate: (item: T) => boolean): [T[], T[]] {
  return array.reduce(
    (result, item) => {
      result[predicate(item) ? 0 : 1].push(item);
      return result;
    },
    [[], []] as [T[], T[]]
  );
}

/**
 * Find the intersection of two arrays
 * @param a First array
 * @param b Second array
 * @returns Array of elements in both arrays
 */
export function intersection<T>(a: T[], b: T[]): T[] {
  const setB = new Set(b);
  return a.filter(x => setB.has(x));
}

/**
 * Find the difference between two arrays
 * @param a First array
 * @param b Second array
 * @returns Elements in first array but not in second
 */
export function difference<T>(a: T[], b: T[]): T[] {
  const setB = new Set(b);
  return a.filter(x => !setB.has(x));
}

/**
 * Shuffle array elements in-place using Fisher-Yates algorithm
 * @param array Array to shuffle
 * @returns Shuffled array (same reference)
 */
export function shuffle<T>(array: T[]): T[] {
  for (let i = array.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
  return array;
}

/**
 * Create a new shuffled array without modifying the original
 * @param array Array to shuffle
 * @returns New shuffled array
 */
export function shuffled<T>(array: T[]): T[] {
  return shuffle([...array]);
}

/**
 * Count occurrences of each value in an array
 * @param array Array to count values in
 * @returns Map of values to counts
 */
export function countBy<T>(array: T[]): Map<T, number> {
  return array.reduce((counts, value) => {
    counts.set(value, (counts.get(value) || 0) + 1);
    return counts;
  }, new Map<T, number>());
}

/**
 * Pick a random element from an array
 * @param array Array to pick from
 * @returns Random element or undefined if empty
 */
export function sample<T>(array: T[]): T | undefined {
  if (array.length === 0) return undefined;
  return array[Math.floor(Math.random() * array.length)];
}

/**
 * Pick multiple random elements from an array
 * @param array Array to pick from
 * @param n Number of elements to pick
 * @returns Array of random elements
 */
export function sampleSize<T>(array: T[], n: number): T[] {
  return shuffled(array).slice(0, n);
}

/**
 * Remove null and undefined values from array
 * @param array Array with potential null/undefined values
 * @returns Filtered array
 */
export function compact<T>(array: (T | null | undefined)[]): T[] {
  return array.filter((x): x is T => x != null);
}

/**
 * Create an array of numbers in range
 * @param start Start of range (inclusive)
 * @param end End of range (exclusive)
 * @param step Step between numbers
 * @returns Array of numbers
 */
export function range(start: number, end: number, step: number = 1): number[] {
  const result: number[] = [];
  for (let i = start; i < end; i += step) {
    result.push(i);
  }
  return result;
}

/**
 * Check if all elements in array satisfy predicate
 * @param array Array to check
 * @param predicate Test function
 * @returns Whether all elements satisfy predicate
 */
export function all<T>(array: T[], predicate: (item: T) => boolean): boolean {
  return array.every(predicate);
}

/**
 * Check if any element in array satisfies predicate
 * @param array Array to check
 * @param predicate Test function
 * @returns Whether any element satisfies predicate
 */
export function any<T>(array: T[], predicate: (item: T) => boolean): boolean {
  return array.some(predicate);
}

/**
 * Get the cartesian product of multiple arrays
 * @param arrays Arrays to combine
 * @returns Array of all possible combinations
 */
export function cartesian<T>(...arrays: T[][]): T[][] {
  return arrays.reduce(
    (result, array) =>
      result.flatMap(combo => array.map(item => [...combo, item])),
    [[]] as T[][]
  );
}
