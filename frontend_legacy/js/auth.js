// Auth checks and page guards
import { api } from './api.js';

export function isLoggedIn() {
  return !!localStorage.getItem('access_token');
}

export function getCurrentUser() {
  const profile = localStorage.getItem('user_profile');
  return profile ? JSON.parse(profile) : null;
}

export function requireAuth() {
  if (!isLoggedIn()) {
    window.location.href = '/index.html';
  }
}

export function requireAdmin() {
  requireAuth();
  const user = getCurrentUser();
  if (!user || user.role !== 'admin') {
    window.location.href = '/dashboard.html';
  }
}

export function initAuthGuard() {
  const path = window.location.pathname;
  if (path === '/' || path.endsWith('/index.html')) {
    if (isLoggedIn()) {
      window.location.href = '/dashboard.html';
    }
  } else {
    requireAuth();
    if (path.endsWith('/admin.html')) {
      requireAdmin();
    }
  }
}

export function logout() {
  api.logout();
}
