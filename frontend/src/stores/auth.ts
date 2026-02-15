
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import api from '../services/api';

interface User {
  username: string;
  email: string;
  full_name?: string;
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'));
  const user = ref<User | null>(null);

  const isAuthenticated = computed(() => !!token.value);

  async function login(username: string, password: string) {
    try {
      // Password login endpoint remains the primary existing path.
      const response = await api.post('/auth/login', { username, password });
      const accessToken = response.data.access_token;
      
      await loginWithToken(accessToken);
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  }

  async function loginWithToken(accessToken: string) {
    // Unified token sink for both password login and WeChat ticket exchange.
    token.value = accessToken;
    localStorage.setItem('token', accessToken);
    // Fetch profile immediately so navbar and route-guards have user context.
    await fetchUser();
    return true;
  }

  async function fetchUser() {
    if (!token.value) return;
    try {
      const response = await api.get('/auth/me');
      user.value = response.data;
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout(); // Token might be invalid
    }
  }

  function logout() {
    token.value = null;
    user.value = null;
    localStorage.removeItem('token');
    // Force reload to clear state and redirect
    window.location.href = '/login';
  }

  return {
    token,
    user,
    isAuthenticated,
    login,
    loginWithToken,
    logout,
    fetchUser
  };
});
