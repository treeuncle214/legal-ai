// frontend-react/vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),  // 添加这一行
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          const nid = id.replace(/\\/g, '/');
          if (!nid.includes('/node_modules/')) return undefined;
          if (/\/react\/|\/react-dom\/|\/react-router\/|\/react-router-dom\//.test(nid)) return 'react-vendor';
          if (/\/antd\/|@ant-design\/icons/.test(nid)) return 'antd-vendor';
          if (/\/echarts\/|echarts-for-react|\/zrender\//.test(nid)) return 'echarts-vendor';
          if (/\/xlsx\//.test(nid)) return 'xlsx-vendor';
          if (/\/jspdf\/|\/html2canvas\//.test(nid)) return 'pdf-vendor';
          return undefined;
        },
      },
    },
  },
});