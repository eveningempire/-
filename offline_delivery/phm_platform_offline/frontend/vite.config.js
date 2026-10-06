import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';

// Vite configuration for the CMG health management platform frontend.
// This file sets up the Vue plugin and configures a proxy for API calls to
// the Django backend running on localhost:8000. When developing the
// frontend, all requests beginning with `/api/v1` will be forwarded to
// the backend, which simplifies cross‑origin development.

export default defineConfig({
  base: '/static/',
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  server: {
    proxy: {
      '/api/v1': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/ws': {
        // 将前端 WebSocket 代理到 Daphne(ASGI) 服务端口
        target: 'ws://localhost:8001',
        ws: true,
        changeOrigin: true
      }
    }
  }
});
