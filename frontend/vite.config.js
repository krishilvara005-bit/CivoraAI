import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// In development the Vite server forwards /api to the Node gateway, which forwards to Flask.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { '/api': process.env.GATEWAY_URL || 'http://localhost:8080' } },
});
