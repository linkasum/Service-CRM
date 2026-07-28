import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import basicSsl from '@vitejs/plugin-basic-ssl';

export default defineConfig({
  base: '/mobile/',
  plugins: [react(), basicSsl()],
  server: {
    host: '0.0.0.0',
    port: 4173,
    proxy: {
      '/api': {
        target: 'http://10.20.4.199:8000',
        changeOrigin: true,
      },
    },
  },
});
