import React from 'react';
import { renderHook, act } from '@testing-library/react-hooks';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useAuth, AuthProvider } from '../useAuth';

// Mock fetch
global.fetch = jest.fn();

describe('useAuth', () => {
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Mock localStorage
    const localStorageMock = {
      getItem: jest.fn(),
      setItem: jest.fn(),
      removeItem: jest.fn()
    };
    Object.defineProperty(window, 'localStorage', { value: localStorageMock });
    
    // Mock fetch to return a successful response for checkAuth
    global.fetch.mockImplementation((url) => {
      if (url.includes('/api/auth/me')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ id: 'user-123', name: 'Test User', email: 'test@example.com' })
        });
      }
      return Promise.resolve({
        ok: false,
        json: () => Promise.resolve({ message: 'Not found' })
      });
    });
  });
  
  it('should provide authentication context', () => {
    const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
    const { result } = renderHook(() => useAuth(), { wrapper });
    
    expect(result.current).toHaveProperty('user');
    expect(result.current).toHaveProperty('isAuthenticated');
    expect(result.current).toHaveProperty('isLoading');
    expect(result.current).toHaveProperty('error');
    expect(result.current).toHaveProperty('login');
    expect(result.current).toHaveProperty('logout');
    expect(result.current).toHaveProperty('register');
  });
  
  it('should check authentication status on mount', async () => {
    // Mock localStorage to return a token
    window.localStorage.getItem.mockReturnValue('fake-token');
    
    const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
    const { result, waitForNextUpdate } = renderHook(() => useAuth(), { wrapper });
    
    // Initially it should be loading
    expect(result.current.isLoading).toBe(true);
    
    await waitForNextUpdate();
    
    // After loading, it should be authenticated
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual({ id: 'user-123', name: 'Test User', email: 'test@example.com' });
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBe(null);
    
    // It should have called the API
    expect(global.fetch).toHaveBeenCalledWith('/api/auth/me', expect.any(Object));
  });
  
  it('should not be authenticated if no token is found', async () => {
    // Mock localStorage to return null for token
    window.localStorage.getItem.mockReturnValue(null);
    
    const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
    const { result } = renderHook(() => useAuth(), { wrapper });
    
    // It should not be authenticated
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBe(null);
  });
  
  it('should login successfully', async () => {
    // Mock fetch to return a successful login response
    global.fetch.mockImplementation((url) => {
      if (url.includes('/api/auth/login')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ 
            token: 'fake-token',
            user: { id: 'user-123', name: 'Test User', email: 'test@example.com' }
          })
        });
      }
      return Promise.resolve({
        ok: false,
        json: () => Promise.resolve({ message: 'Not found' })
      });
    });
    
    const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
    const { result } = renderHook(() => useAuth(), { wrapper });
    
    await act(async () => {
      await result.current.login('test@example.com', 'password');
    });
    
    // It should be authenticated
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual({ id: 'user-123', name: 'Test User', email: 'test@example.com' });
    
    // It should have called the API
    expect(global.fetch).toHaveBeenCalledWith('/api/auth/login', expect.objectContaining({
      method: 'POST',
      body: expect.any(String)
    }));
    
    // It should have stored the token
    expect(window.localStorage.setItem).toHaveBeenCalledWith('authToken', 'fake-token');
  });
  
  it('should handle login errors', async () => {
    // Mock fetch to return an error
    global.fetch.mockImplementation((url) => {
      if (url.includes('/api/auth/login')) {
        return Promise.resolve({
          ok: false,
          status: 401,
          json: () => Promise.resolve({ message: 'Invalid credentials' })
        });
      }
      return Promise.resolve({
        ok: false,
        json: () => Promise.resolve({ message: 'Not found' })
      });
    });
    
    const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
    const { result } = renderHook(() => useAuth(), { wrapper });
    
    await act(async () => {
      await result.current.login('test@example.com', 'wrong-password');
    });
    
    // It should not be authenticated
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBe(null);
    expect(result.current.error).toEqual(new Error('Invalid credentials'));
  });
  
  it('should logout successfully', async () => {
    // Set initial state as authenticated
    window.localStorage.getItem.mockReturnValue('fake-token');
    
    const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
    const { result, waitForNextUpdate } = renderHook(() => useAuth(), { wrapper });
    
    await waitForNextUpdate();
    
    // Initially it should be authenticated
    expect(result.current.isAuthenticated).toBe(true);
    
    await act(async () => {
      await result.current.logout();
    });
    
    // After logout, it should not be authenticated
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBe(null);
    
    // It should have removed the token
    expect(window.localStorage.removeItem).toHaveBeenCalledWith('authToken');
  });
  
  it('should register successfully', async () => {
    // Mock fetch to return a successful register response
    global.fetch.mockImplementation((url) => {
      if (url.includes('/api/auth/register')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ 
            token: 'fake-token',
            user: { id: 'new-user', name: 'New User', email: 'new@example.com' }
          })
        });
      }
      return Promise.resolve({
        ok: false,
        json: () => Promise.resolve({ message: 'Not found' })
      });
    });
    
    const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
    const { result } = renderHook(() => useAuth(), { wrapper });
    
    await act(async () => {
      await result.current.register('new@example.com', 'password', 'New User');
    });
    
    // It should be authenticated
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual({ id: 'new-user', name: 'New User', email: 'new@example.com' });
    
    // It should have called the API
    expect(global.fetch).toHaveBeenCalledWith('/api/auth/register', expect.objectContaining({
      method: 'POST',
      body: expect.any(String)
    }));
    
    // It should have stored the token
    expect(window.localStorage.setItem).toHaveBeenCalledWith('authToken', 'fake-token');
  });
  
  it('should handle register errors', async () => {
    // Mock fetch to return an error
    global.fetch.mockImplementation((url) => {
      if (url.includes('/api/auth/register')) {
        return Promise.resolve({
          ok: false,
          status: 400,
          json: () => Promise.resolve({ message: 'Email already in use' })
        });
      }
      return Promise.resolve({
        ok: false,
        json: () => Promise.resolve({ message: 'Not found' })
      });
    });
    
    const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
    const { result } = renderHook(() => useAuth(), { wrapper });
    
    await act(async () => {
      await result.current.register('existing@example.com', 'password', 'Existing User');
    });
    
    // It should not be authenticated
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBe(null);
    expect(result.current.error).toEqual(new Error('Email already in use'));
  });
}); 