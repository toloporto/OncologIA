import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { nodePolyfills } from 'vite-plugin-node-polyfills'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    nodePolyfills({
      // Para asegurar que Buffer esté disponible globalmente
      globals: {
        Buffer: true,
        global: true,
        process: true,
      },
    }),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'masked-icon.svg'],
      manifest: {
        name: 'OncologIA - Asistente Clínico',
        short_name: 'OncologIA',
        description: 'Plataforma de IA para Análisis Clínico y Apoyo Terapéutico',
        theme_color: '#0d9488',
        background_color: '#f8fafc',
        display: 'standalone',
        orientation: 'portrait',
        start_url: '/',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable'
          }
        ]
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        runtimeCaching: [
            {
                urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
                handler: 'CacheFirst',
                options: {
                cacheName: 'google-fonts-cache',
                expiration: {
                    maxEntries: 10,
                    maxAgeSeconds: 60 * 60 * 24 * 365 // <== 365 days
                },
                cacheableResponse: {
                    statuses: [0, 200]
                }
                }
            },
            {
                urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/i,
                handler: 'CacheFirst',
                options: {
                cacheName: 'gstatic-fonts-cache',
                expiration: {
                    maxEntries: 10,
                    maxAgeSeconds: 60 * 60 * 24 * 365 // <== 365 days
                },
                cacheableResponse: {
                    statuses: [0, 200]
                }
                }
            }
        ]
      }
    }),
  ],
  server: {
    // Exponer en la red local para poder acceder desde otros dispositivos si es necesario
    host: '0.0.0.0', 
    port: 5173, // Puerto estándar de Vite, puedes cambiarlo si lo necesitas
    // Configuración del proxy para redirigir las llamadas a la API al backend
    proxy: {
      '/api': {
        target: 'http://localhost:8004', // La URL donde se ejecuta tu backend real
        changeOrigin: true, // Necesario para que el backend reciba la petición correctamente
        rewrite: (path) => path.replace(/^\/api/, ''), // Elimina '/api' antes de enviar la petición al backend
      },
    },
  },
})
