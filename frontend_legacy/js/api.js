// Base API client with JWT token management and generic requests
const API_BASE = '/api/v1';

class NexusAPI {
  constructor() {
    this.baseUrl = API_BASE;
  }

  getHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };
    const token = localStorage.getItem('access_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  async request(method, endpoint, body = null) {
    const url = `${this.baseUrl}${endpoint}`;
    const options = {
      method,
      headers: this.getHeaders(),
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    try {
      const response = await fetch(url, options);

      if (response.status === 401 && endpoint !== '/auth/login' && endpoint !== '/auth/register') {
        // Attempt token refresh
        const refreshed = await this.refreshToken();
        if (refreshed) {
          // Retry original request
          options.headers = this.getHeaders();
          const retryResponse = await fetch(url, options);
          return await this.handleResponse(retryResponse);
        } else {
          this.logoutRedirect();
          return null;
        }
      }

      return await this.handleResponse(response);
    } catch (error) {
      console.error(`API Request failed: ${method} ${endpoint}`, error);
      throw error;
    }
  }

  async handleResponse(response) {
    if (response.status === 204) {
      return null;
    }
    
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || data.detail || 'API request failed');
    }
    return data;
  }

  logoutRedirect() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_profile');
    if (window.location.pathname !== '/' && window.location.pathname !== '/index.html') {
      window.location.href = '/index.html';
    }
  }

  // Auth Operations
  async login(email, password) {
    const data = await this.request('POST', '/auth/login', { email, password });
    if (data) {
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      // Fetch user details immediately to cache in localStorage
      const profile = await this.getProfile();
      localStorage.setItem('user_profile', JSON.stringify(profile));
    }
    return data;
  }

  async register(username, email, password) {
    const data = await this.request('POST', '/auth/register', { username, email, password });
    if (data) {
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      const profile = await this.getProfile();
      localStorage.setItem('user_profile', JSON.stringify(profile));
    }
    return data;
  }

  async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) return false;

    try {
      const url = `${this.baseUrl}/auth/refresh`;
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        return true;
      }
    } catch (e) {
      console.error('Failed to refresh token', e);
    }
    return false;
  }

  async getProfile() {
    return await this.request('GET', '/auth/me');
  }

  async logout() {
    this.logoutRedirect();
  }

  // Queries Operations
  async submitQuery(question, sessionId = null) {
    return await this.request('POST', '/query', { question, session_id: sessionId });
  }

  async getQuery(id) {
    return await this.request('GET', `/query/${id}`);
  }

  async getHistory(page = 1, pageSize = 20) {
    return await this.request('GET', `/query/history?page=${page}&page_size=${pageSize}`);
  }

  async getSuggestions() {
    return await this.request('GET', '/query/suggestions');
  }

  // Saved Queries Operations
  async saveQuery(name, description, queryId) {
    return await this.request('POST', '/saved-queries', { name, description, query_id: queryId });
  }

  async getSavedQueries() {
    return await this.request('GET', '/saved-queries');
  }

  async updateSavedQuery(id, data) {
    return await this.request('PATCH', `/saved-queries/${id}`, data);
  }

  async deleteSavedQuery(id) {
    return await this.request('DELETE', `/saved-queries/${id}`);
  }

  // Export Operations
  exportCSVUrl(queryId) {
    return `${this.baseUrl}/export/${queryId}?format=csv`;
  }

  exportExcelUrl(queryId) {
    return `${this.baseUrl}/export/${queryId}?format=excel`;
  }

  // Admin Operations
  async getUsers() {
    return await this.request('GET', '/admin/users');
  }

  async updateUserRole(userId, role) {
    return await this.request('PATCH', `/admin/users/${userId}/role`, { role });
  }

  async deactivateUser(userId) {
    return await this.request('POST', `/admin/users/${userId}/deactivate`);
  }

  async getAuditLogs(limit = 50) {
    return await this.request('GET', `/admin/audit-logs?limit=${limit}`);
  }

  async getPlatformStats() {
    return await this.request('GET', '/admin/stats');
  }

  async healthCheck() {
    return await this.request('GET', '/health');
  }
}

export const api = new NexusAPI();
