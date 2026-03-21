'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import Cookies from 'js-cookie';
import { authAPI } from '@/lib/api';
import { signInWithPopup, signInWithRedirect, getRedirectResult } from 'firebase/auth';
import { auth, googleProvider } from '@/lib/firebase';

interface User {
  id: number;
  name: string;
  email: string;
  role?: string;
  profile_picture?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing session
    const savedToken = Cookies.get('token');
    const savedUser = Cookies.get('user');

    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
      setLoading(false);
    } else {
      // Check for redirect result (fallback from popup-blocked)
      getRedirectResult(auth)
        .then(async (result) => {
          if (result?.user) {
            const firebaseUser = result.user;
            if (firebaseUser.email) {
              const response = await authAPI.googleLogin(
                firebaseUser.displayName || '',
                firebaseUser.email,
                firebaseUser.photoURL || ''
              );
              const { user: userData, token: newToken } = response;
              setUser(userData);
              setToken(newToken);
              Cookies.set('token', newToken, { expires: 7 });
              Cookies.set('user', JSON.stringify(userData), { expires: 7 });
            }
          }
        })
        .catch((err) => console.error('Redirect result error:', err))
        .finally(() => setLoading(false));
    }
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await authAPI.login(email, password);
      const { user: userData, token: newToken } = response;

      setUser(userData);
      setToken(newToken);

      // Store in cookies
      Cookies.set('token', newToken, { expires: 7 }); // 7 days
      Cookies.set('user', JSON.stringify(userData), { expires: 7 });
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Login failed');
    }
  };

  const loginWithGoogle = async () => {
    try {
      setLoading(true);
      let result;
      try {
        result = await signInWithPopup(auth, googleProvider);
      } catch (popupError: any) {
        // If popup is blocked or cancelled, fall back to redirect
        if (popupError.code === 'auth/popup-blocked') {
          await signInWithRedirect(auth, googleProvider);
          return; // Will be handled by getRedirectResult on page reload
        }
        if (popupError.code === 'auth/cancelled-popup-request') {
          // User opened multiple popups; ignore this harmless error
          return;
        }
        throw popupError;
      }

      const firebaseUser = result.user;

      if (!firebaseUser.email) {
        throw new Error('Google account must have an email address');
      }

      // Send to backend to get JWT
      const response = await authAPI.googleLogin(
        firebaseUser.displayName || '',
        firebaseUser.email,
        firebaseUser.photoURL || ''
      );

      const { user: userData, token: newToken } = response;

      setUser(userData);
      setToken(newToken);

      // Store in cookies
      Cookies.set('token', newToken, { expires: 7 });
      Cookies.set('user', JSON.stringify(userData), { expires: 7 });
    } catch (error: any) {
      console.error('Google Login Error:', error);
      throw new Error(error.response?.data?.message || error.message || 'Google login failed');
    } finally {
      setLoading(false);
    }
  };

  const signup = async (name: string, email: string, password: string) => {
    try {
      const response = await authAPI.signup(name, email, password);
      const { user: userData, token: newToken } = response;

      setUser(userData);
      setToken(newToken);

      // Store in cookies
      Cookies.set('token', newToken, { expires: 7 }); // 7 days
      Cookies.set('user', JSON.stringify(userData), { expires: 7 });
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Signup failed');
    }
  };

  const logout = () => {
    authAPI.logout();
    setUser(null);
    setToken(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        loginWithGoogle,
        signup,
        logout,
        isAuthenticated: !!user && !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
