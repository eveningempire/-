import axios from 'axios';
import { ElMessage } from 'element-plus';

// Create an axios instance with sensible defaults for communicating with
// the Django backend. The baseURL points to the proxy path configured
// in vite.config.js, and withCredentials ensures that session cookies
// (used by Django REST Framework's session auth) are included in
// requests.

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 300000, // 增加到5分钟
  withCredentials: true,
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
  headers: { 'X-Requested-With': 'XMLHttpRequest' }
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 获取CSRF token
    const csrfToken = document.cookie
      .split('; ')
      .find(row => row.startsWith('csrftoken='))
      ?.split('=')[1];
    
    if (csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken;
      console.log('CSRF Token found:', csrfToken);
    } else {
      console.log('No CSRF token found in cookies');
      console.log('Available cookies:', document.cookie);
    }
    
    // 添加调试信息
    console.log('Request config:', {
      url: config.url,
      method: config.method,
      headers: config.headers
    });
    
    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log('Response received:', {
      status: response.status,
      url: response.config.url,
      data: response.data
    });
    return response;
  },
  (error) => {
    console.error('Response error:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      url: error.config?.url,
      data: error.response?.data,
      headers: error.response?.headers
    });
    
    if (error.response?.status === 401) {
      // 未授权，清除本地存储的用户信息
      localStorage.removeItem('user');
      
      // 如果不是在登录页面，则重定向到登录页面
      if (window.location.pathname !== '/login') {
        ElMessage.error('登录已过期，请重新登录');
        window.location.href = '/login';
      }
    } else if (error.response?.status === 403) {
      console.error('403 Forbidden - CSRF or permission issue');
      ElMessage.error('请求被拒绝，请检查权限设置');
    }
    
    return Promise.reject(error);
  }
);

export default api;