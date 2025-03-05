import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./jest.setup.js'],
    include: ['src/**/*.test.{ts,tsx,js,jsx}'],
    coverage: {
      reporter: ['text', 'html'],
    },
  },
});