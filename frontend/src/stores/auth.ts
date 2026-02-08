
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
      // Assuming the backend returns { access_token: "...", token_type: "bearer" }
      const response = await api.post('/auth/login', { username, password });
      const accessToken = response.data.access_token;
      
      token.value = accessToken;
      localStorage.setItem('token', accessToken);
      
      // Optionally fetch user info immediately
      await fetchUser();
      
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
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
    logout,
    fetchUser
  };
});
