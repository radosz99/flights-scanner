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
    public: {
      apiBaseUrl: process.env.API_BASE_URL || 'http://localhost:8900'
    }
  }
})
