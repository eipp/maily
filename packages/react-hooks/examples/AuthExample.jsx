import React, { useState } from 'react';
import { useAuth, AuthProvider } from '../src';

// Login form component
function LoginForm({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  
  const handleSubmit = (e) => {
    e.preventDefault();
    onLogin(email, password);
  };
  
  return (
    <form onSubmit={handleSubmit} className="login-form">
      <h2>Login</h2>
      
      <div className="form-group">
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </div>
      
      <button type="submit">Login</button>
    </form>
  );
}

// Registration form component
function RegisterForm({ onRegister }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  
  const handleSubmit = (e) => {
    e.preventDefault();
    onRegister(email, password, name);
  };
  
  return (
    <form onSubmit={handleSubmit} className="register-form">
      <h2>Register</h2>
      
      <div className="form-group">
        <label htmlFor="name">Name</label>
        <input
          id="name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </div>
      
      <button type="submit">Register</button>
    </form>
  );
}

// User profile component
function UserProfile({ user, onLogout }) {
  return (
    <div className="user-profile">
      <h2>User Profile</h2>
      
      <div className="profile-info">
        <p><strong>Name:</strong> {user.name}</p>
        <p><strong>Email:</strong> {user.email}</p>
        <p><strong>Role:</strong> {user.role || 'User'}</p>
      </div>
      
      <button onClick={onLogout}>Logout</button>
    </div>
  );
}

// Authentication example component
function AuthExample() {
  const { user, isAuthenticated, isLoading, error, login, logout, register } = useAuth();
  const [view, setView] = useState('login'); // 'login' or 'register'
  
  if (isLoading) {
    return <div className="loading">Loading authentication state...</div>;
  }
  
  if (isAuthenticated) {
    return <UserProfile user={user} onLogout={logout} />;
  }
  
  return (
    <div className="auth-example">
      {error && (
        <div className="error-message">
          <p>{error.message}</p>
        </div>
      )}
      
      {view === 'login' ? (
        <>
          <LoginForm onLogin={login} />
          <p>
            Don't have an account?{' '}
            <button onClick={() => setView('register')}>Register</button>
          </p>
        </>
      ) : (
        <>
          <RegisterForm onRegister={register} />
          <p>
            Already have an account?{' '}
            <button onClick={() => setView('login')}>Login</button>
          </p>
        </>
      )}
    </div>
  );
}

// Main component with AuthProvider
export default function AuthExampleWithProvider() {
  return (
    <AuthProvider>
      <div className="auth-example-container">
        <h1>Authentication Example</h1>
        <AuthExample />
      </div>
    </AuthProvider>
  );
} 