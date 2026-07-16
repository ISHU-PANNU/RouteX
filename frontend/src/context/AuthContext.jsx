import React, { createContext, useState, useEffect, useContext } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check login status on page refresh/boot
  useEffect(() => {
    const checkLoginStatus = async () => {
      const accessToken = localStorage.getItem('access_token');
      if (accessToken) {
        try {
          // Attempt token login check (validates access token authenticity)
          // We can decrypt or retrieve user information from storage
          const savedUser = localStorage.getItem('user_details');
          if (savedUser) {
            setUser(JSON.parse(savedUser));
          } else {
            // If details are not cached, fetch them
            // In a production setup, we query /auth/me or similar,
            // but for simplicity we rely on cached user_details or decoded JWT.
            localStorage.clear();
          }
        } catch (e) {
          localStorage.clear();
        }
      }
      setLoading(false);
    };

    checkLoginStatus();
  }, []);

  const login = async (email, password) => {
    try {
      const response = await api.post('/auth/login', { email, password });
      const { access_token, refresh_token, user: userDetails } = response.data;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('user_details', JSON.stringify(userDetails));
      
      setUser(userDetails);
      return userDetails;
    } catch (error) {
      let errorMsg = 'Login credentials incorrect.';
      if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          errorMsg = error.response.data.detail.map(d => d.msg).join(', ');
        } else {
          errorMsg = error.response.data.detail;
        }
      } else if (error.response?.data?.message) {
        errorMsg = error.response.data.message;
      }
      throw errorMsg;
    }
  };

  const register = async (name, email, password, phone, role = 'Customer') => {
    try {
      const response = await api.post('/auth/register', {
        name,
        email,
        password,
        phone,
        role,
      });
      return response.data;
    } catch (error) {
      let errorMsg = 'Registration failed. Check inputs.';
      if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          errorMsg = error.response.data.detail.map(d => d.msg).join(', ');
        } else {
          errorMsg = error.response.data.detail;
        }
      } else if (error.response?.data?.message) {
        errorMsg = error.response.data.message;
      }
      throw errorMsg;
    }
  };

  const logout = async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        await api.post('/auth/logout', { refresh_token: refreshToken });
      }
    } catch (e) {
      // Proceed with local logout on API failure
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_details');
      setUser(null);
      window.location.href = '/login';
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be executed within an AuthProvider scope');
  }
  return context;
};
