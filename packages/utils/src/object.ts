/**
 * Object utility functions
 */

/**
 * Deep clone an object
 * @param obj Object to clone
 * @returns Deep clone of the object
 */
export function deepClone<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }

  if (obj instanceof Date) {
    return new Date(obj.getTime()) as any;
  }

  if (obj instanceof Array) {
    return obj.map(item => deepClone(item)) as any;
  }

  if (obj instanceof Set) {
    return new Set(Array.from(obj).map(item => deepClone(item))) as any;
  }

  if (obj instanceof Map) {
    return new Map(
      Array.from(obj.entries()).map(([key, value]) => [key, deepClone(value)])
    ) as any;
  }

  const cloned: Record<string, any> = {};

  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      cloned[key] = deepClone((obj as any)[key]);
    }
  }

  return cloned as T;
}

/**
 * Deep merge objects (recursive)
 * @param target Target object
 * @param sources Source objects
 * @returns Merged object
 */
export function deepMerge<T extends object>(target: T, ...sources: Partial<T>[]): T {
  if (!sources.length) {
    return target;
  }

  const source = sources.shift();

  if (source === undefined) {
    return target;
  }

  if (isMergeableObject(target) && isMergeableObject(source)) {
    Object.keys(source).forEach(key => {
      if (isMergeableObject(source[key as keyof typeof source])) {
        if (!target[key as keyof typeof target]) {
          (target as any)[key] = {};
        }

        deepMerge(
          (target as any)[key],
          (source as any)[key]
        );
      } else {
        (target as any)[key] = (source as any)[key];
      }
    });
  }

  return deepMerge(target, ...sources);
}

/**
 * Check if an object is mergeable
 * @param item Item to check
 * @returns Whether the item is a mergeable object
 */
function isMergeableObject(item: any): item is object {
  return item && typeof item === 'object' &&
    !(item instanceof RegExp) &&
    !(item instanceof Date) &&
    !(item instanceof Array) &&
    !(item instanceof Map) &&
    !(item instanceof Set);
}

/**
 * Pick specific properties from an object
 * @param obj Source object
 * @param keys Keys to pick
 * @returns New object with only picked properties
 */
export function pick<T extends object, K extends keyof T>(
  obj: T,
  keys: K[]
): Pick<T, K> {
  return keys.reduce(
    (result, key) => {
      if (key in obj) {
        result[key] = obj[key];
      }
      return result;
    },
    {} as Pick<T, K>
  );
}

/**
 * Omit specific properties from an object
 * @param obj Source object
 * @param keys Keys to omit
 * @returns New object without omitted properties
 */
export function omit<T extends object, K extends keyof T>(
  obj: T,
  keys: K[]
): Omit<T, K> {
  const result = { ...obj };

  for (const key of keys) {
    delete result[key];
  }

  return result;
}

/**
 * Check if objects are deeply equal
 * @param a First object
 * @param b Second object
 * @returns Whether objects are deeply equal
 */
export function isEqual(a: any, b: any): boolean {
  if (a === b) {
    return true;
  }

  if (a === null || b === null) {
    return a === b;
  }

  if (typeof a !== 'object' || typeof b !== 'object') {
    return a === b;
  }

  if (a instanceof Date && b instanceof Date) {
    return a.getTime() === b.getTime();
  }

  if (a instanceof RegExp && b instanceof RegExp) {
    return a.toString() === b.toString();
  }

  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) {
      return false;
    }

    for (let i = 0; i < a.length; i++) {
      if (!isEqual(a[i], b[i])) {
        return false;
      }
    }

    return true;
  }

  if (a instanceof Set && b instanceof Set) {
    if (a.size !== b.size) {
      return false;
    }

    for (const item of a) {
      if (!b.has(item)) {
        return false;
      }
    }

    return true;
  }

  if (a instanceof Map && b instanceof Map) {
    if (a.size !== b.size) {
      return false;
    }

    for (const [key, value] of a.entries()) {
      if (!b.has(key) || !isEqual(value, b.get(key))) {
        return false;
      }
    }

    return true;
  }

  const keysA = Object.keys(a);
  const keysB = Object.keys(b);

  if (keysA.length !== keysB.length) {
    return false;
  }

  return keysA.every(key =>
    Object.prototype.hasOwnProperty.call(b, key) &&
    isEqual(a[key], b[key])
  );
}

/**
 * Flatten a nested object structure
 * @param obj Object to flatten
 * @param prefix Key prefix for flattened keys
 * @param separator Separator between nested keys
 * @returns Flattened object
 */
export function flattenObject(
  obj: Record<string, any>,
  prefix: string = '',
  separator: string = '.'
): Record<string, any> {
  return Object.keys(obj).reduce((acc, key) => {
    const prefixedKey = prefix ? `${prefix}${separator}${key}` : key;

    if (
      typeof obj[key] === 'object' &&
      obj[key] !== null &&
      !Array.isArray(obj[key]) &&
      !(obj[key] instanceof Date) &&
      !(obj[key] instanceof RegExp)
    ) {
      Object.assign(acc, flattenObject(obj[key], prefixedKey, separator));
    } else {
      acc[prefixedKey] = obj[key];
    }

    return acc;
  }, {} as Record<string, any>);
}

/**
 * Unflatten a flattened object
 * @param obj Flattened object
 * @param separator Separator used in keys
 * @returns Nested object
 */
export function unflattenObject(
  obj: Record<string, any>,
  separator: string = '.'
): Record<string, any> {
  const result: Record<string, any> = {};

  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      const keys = key.split(separator);
      let current = result;

      for (let i = 0; i < keys.length; i++) {
        const k = keys[i];

        if (i === keys.length - 1) {
          current[k] = obj[key];
        } else {
          current[k] = current[k] || {};
          current = current[k];
        }
      }
    }
  }

  return result;
}

/**
 * Convert object to URL query string
 * @param params Object to convert
 * @param options Serialization options
 * @returns Query string (without leading ?)
 */
export function toQueryString(
  params: Record<string, any>,
  options: {
    arrayFormat?: 'brackets' | 'comma' | 'repeat' | 'indices';
    encode?: boolean;
  } = {}
): string {
  const { arrayFormat = 'brackets', encode = true } = options;

  return Object.entries(params)
    .filter(([_, value]) => value !== undefined && value !== null)
    .map(([key, value]) => {
      if (Array.isArray(value)) {
        return serializeArray(key, value, arrayFormat, encode);
      }

      return `${encodePart(key, encode)}=${encodePart(value, encode)}`;
    })
    .join('&');
}

/**
 * Parse query string to object
 * @param queryString Query string to parse (with or without leading ?)
 * @param options Parsing options
 * @returns Parsed object
 */
export function parseQueryString(
  queryString: string,
  options: {
    arrayFormat?: 'brackets' | 'comma' | 'repeat' | 'indices';
    decode?: boolean;
  } = {}
): Record<string, any> {
  const { arrayFormat = 'brackets', decode = true } = options;

  // Remove leading ? if present
  const query = queryString.startsWith('?')
    ? queryString.substring(1)
    : queryString;

  // Handle empty query
  if (!query) {
    return {};
  }

  const result: Record<string, any> = {};

  query.split('&').forEach(part => {
    if (!part) {
      return;
    }

    const [rawKey, rawValue] = part.split('=', 2);
    const key = decode ? decodeURIComponent(rawKey) : rawKey;
    const value = rawValue === undefined
      ? null
      : decode ? decodeURIComponent(rawValue) : rawValue;

    parseQueryParam(result, key, value, arrayFormat);
  });

  return result;
}

/**
 * Encode query string part
 * @param value Value to encode
 * @param encode Whether to encode
 * @returns Encoded string
 */
function encodePart(value: any, encode: boolean): string {
  const str = String(value);
  return encode ? encodeURIComponent(str) : str;
}

/**
 * Serialize array for query string
 * @param key Array key
 * @param arr Array to serialize
 * @param format Array format
 * @param encode Whether to encode
 * @returns Serialized array string
 */
function serializeArray(
  key: string,
  arr: any[],
  format: 'brackets' | 'comma' | 'repeat' | 'indices',
  encode: boolean
): string {
  const encodedKey = encodePart(key, encode);

  if (format === 'comma') {
    return `${encodedKey}=${arr.map(v => encodePart(v, encode)).join(',')}`;
  }

  if (format === 'repeat') {
    return arr.map(v => `${encodedKey}=${encodePart(v, encode)}`).join('&');
  }

  if (format === 'brackets') {
    return arr.map(v => `${encodedKey}[]=${encodePart(v, encode)}`).join('&');
  }

  if (format === 'indices') {
    return arr
      .map((v, i) => `${encodedKey}[${i}]=${encodePart(v, encode)}`)
      .join('&');
  }

  // Default to brackets
  return arr.map(v => `${encodedKey}[]=${encodePart(v, encode)}`).join('&');
}

/**
 * Parse query parameter
 * @param result Result object
 * @param key Parameter key
 * @param value Parameter value
 * @param arrayFormat Array format
 */
function parseQueryParam(
  result: Record<string, any>,
  key: string,
  value: string | null,
  arrayFormat: 'brackets' | 'comma' | 'repeat' | 'indices'
): void {
  // Handle comma-separated arrays
  if (arrayFormat === 'comma' && value?.includes(',')) {
    result[key] = value.split(',').map(v => v === '' ? null : v);
    return;
  }

  // Handle array syntax
  const matches = key.match(/^([^[\]]+)(\[\d*\]|\[\])?$/);

  if (matches) {
    const [, keyName, arrayNotation] = matches;

    if (arrayNotation) {
      // Array key - add to existing array or create new one
      result[keyName] = result[keyName] || [];

      // Handle indexed array (e.g., key[0])
      if (arrayNotation.match(/^\[\d+\]$/)) {
        const index = parseInt(arrayNotation.replace(/[\[\]]/g, ''), 10);
        result[keyName][index] = value;
      } else {
        // Handle array notation (e.g., key[])
        result[keyName].push(value);
      }
    } else {
      // Regular key
      result[key] = value;
    }
  } else {
    // Handle keys with dots for nested objects
    if (key.includes('.')) {
      const keys = key.split('.');
      let current = result;

      for (let i = 0; i < keys.length; i++) {
        const k = keys[i];

        if (i === keys.length - 1) {
          current[k] = value;
        } else {
          current[k] = current[k] || {};
          current = current[k];
        }
      }
    } else {
      // Regular key
      result[key] = value;
    }
  }
}

/**
 * Extract values from object using path strings
 * @param obj Source object
 * @param path Property path (e.g., 'user.address.city')
 * @param defaultValue Default value if path not found
 * @returns Value at path or default value
 */
export function get<T>(
  obj: Record<string, any>,
  path: string,
  defaultValue?: T
): any {
  const keys = path.split('.');
  let current = obj;

  for (const key of keys) {
    if (current === null || current === undefined) {
      return defaultValue;
    }

    current = current[key];
  }

  return current === undefined ? defaultValue : current;
}

/**
 * Set a value in object using a path string
 * @param obj Object to modify
 * @param path Property path (e.g., 'user.address.city')
 * @param value Value to set
 * @returns Modified object
 */
export function set<T extends object>(
  obj: T,
  path: string,
  value: any
): T {
  if (!obj || typeof obj !== 'object') {
    return obj;
  }

  const keys = path.split('.');
  let current = obj;

  for (let i = 0; i < keys.length - 1; i++) {
    const key = keys[i];

    if (!current[key as keyof typeof current] || typeof current[key as keyof typeof current] !== 'object') {
      current[key] = {};
    }

    current = current[key];
  }

  current[keys[keys.length - 1]] = value;
  return obj;
}

/**
 * Remove a property using path string
 * @param obj Object to modify
 * @param path Property path to remove
 * @returns Modified object
 */
export function unset<T extends object>(obj: T, path: string): T {
  const keys = path.split('.');
  let current = obj;

  for (let i = 0; i < keys.length - 1; i++) {
    const key = keys[i];

    if (!current[key] || typeof current[key] !== 'object') {
      return obj;
    }

    current = current[key];
  }

  delete current[keys[keys.length - 1]];
  return obj;
}

/**
 * Check if an object has a property at a given path
 * @param obj Object to check
 * @param path Property path
 * @returns Whether property exists
 */
export function has(obj: Record<string, any>, path: string): boolean {
  const keys = path.split('.');
  let current = obj;

  for (const key of keys) {
    if (current === null || current === undefined || !Object.prototype.hasOwnProperty.call(current, key)) {
      return false;
    }

    current = current[key];
  }

  return true;
}

/**
 * Map object values
 * @param obj Object to map
 * @param fn Mapping function
 * @returns New object with mapped values
 */
export function mapValues<T, R>(
  obj: Record<string, T>,
  fn: (value: T, key: string, object: Record<string, T>) => R
): Record<string, R> {
  return Object.fromEntries(
    Object.entries(obj).map(([key, value]) => [key, fn(value, key, obj)])
  );
}

/**
 * Filter object properties
 * @param obj Object to filter
 * @param fn Filter function
 * @returns New object with filtered properties
 */
export function filterObject<T>(
  obj: Record<string, T>,
  fn: (value: T, key: string, object: Record<string, T>) => boolean
): Record<string, T> {
  return Object.fromEntries(
    Object.entries(obj).filter(([key, value]) => fn(value, key, obj))
  );
}

/**
 * Create a new object with transformed keys
 * @param obj Source object
 * @param fn Key transform function
 * @returns New object with transformed keys
 */
export function mapKeys<T>(
  obj: Record<string, T>,
  fn: (key: string, value: T, object: Record<string, T>) => string
): Record<string, T> {
  return Object.fromEntries(
    Object.entries(obj).map(([key, value]) => [fn(key, value, obj), value])
  );
}

/**
 * Invert object keys and values
 * @param obj Object to invert
 * @returns Inverted object
 */
export function invert<T extends string | number | symbol>(
  obj: Record<string, T>
): Record<T, string> {
  return Object.fromEntries(
    Object.entries(obj).map(([key, value]) => [value, key])
  ) as Record<T, string>;
}

/**
 * Convert array to object using key function
 * @param array Array to convert
 * @param keyFn Function to extract key
 * @returns Object keyed by keyFn results
 */
export function keyBy<T>(
  array: T[],
  keyFn: (item: T) => string
): Record<string, T> {
  return array.reduce((result, item) => {
    result[keyFn(item)] = item;
    return result;
  }, {} as Record<string, T>);
}
