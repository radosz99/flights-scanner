// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  devtools: { enabled: true },
  ssr: true,
  modules: ['@nuxtjs/tailwindcss', '@nuxtjs/leaflet'],
  css: ['@/assets/css/leaflet.css'],
  nitro: {
    preset: 'node-server'
  },
  runtimeConfig: {
    // Server-only config (SSR) - uses Docker internal URL
    apiBaseUrl: process.env.API_BASE_URL || 'http://localhost:8900',
    public: {
      // Client-side config (browser) - uses relative URL proxied by nginx in production
      // Set NUXT_PUBLIC_API_BASE_URL env var to override (e.g., '/api' for production, 'http://localhost:8900' for dev)
      apiBaseUrl: process.env.NUXT_PUBLIC_API_BASE_URL || (process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:8900')
    }
  }
})
