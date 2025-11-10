// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  devtools: { enabled: true },
  ssr: true,
  modules: ['@nuxtjs/tailwindcss'],
  nitro: {
    preset: 'node-server'
  },
  runtimeConfig: {
    public: {
      apiBaseUrl: process.env.API_BASE_URL || 'http://localhost:8900'
    }
  },
  vite: {
    optimizeDeps: {
      exclude: ['leaflet']
    },
    ssr: {
      noExternal: []
    }
  },
  build: {
    transpile: []
  }
})
