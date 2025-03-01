import { renderHook, act } from '@testing-library/react';
import { useLocalStorage } from '@/hooks/useLocalStorage';

describe('useLocalStorage Hook', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    window.localStorage.clear();
  });

  it('should return initial value when no stored value exists', () => {
    const { result } = renderHook(() => useLocalStorage('testKey', 'initial'));
    expect(result.current[0]).toBe('initial');
  });

  it('should return stored value when it exists', () => {
    window.localStorage.setItem('testKey', JSON.stringify('stored value'));
    const { result } = renderHook(() => useLocalStorage('testKey', 'initial'));
    expect(result.current[0]).toBe('stored value');
  });

  it('should update stored value', () => {
    const { result } = renderHook(() => useLocalStorage('testKey', 'initial'));

    act(() => {
      result.current[1]('new value');
    });

    expect(result.current[0]).toBe('new value');
    expect(JSON.parse(window.localStorage.getItem('testKey')!)).toBe('new value');
  });

  it('should handle storing objects', () => {
    const initialValue = { name: 'John', age: 30 };
    const { result } = renderHook(() => useLocalStorage('testKey', initialValue));

    const newValue = { name: 'Jane', age: 25 };
    act(() => {
      result.current[1](newValue);
    });

    expect(result.current[0]).toEqual(newValue);
    expect(JSON.parse(window.localStorage.getItem('testKey')!)).toEqual(newValue);
  });

  it('should handle storing arrays', () => {
    const initialValue = [1, 2, 3];
    const { result } = renderHook(() => useLocalStorage('testKey', initialValue));

    const newValue = [4, 5, 6];
    act(() => {
      result.current[1](newValue);
    });

    expect(result.current[0]).toEqual(newValue);
    expect(JSON.parse(window.localStorage.getItem('testKey')!)).toEqual(newValue);
  });

  it('should handle errors in JSON parsing', () => {
    // Set invalid JSON in localStorage
    window.localStorage.setItem('testKey', 'invalid json');
    const { result } = renderHook(() => useLocalStorage('testKey', 'initial'));

    // Should fall back to initial value
    expect(result.current[0]).toBe('initial');
  });
});
