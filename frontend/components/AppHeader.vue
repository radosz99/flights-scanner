<template>
  <header class="sticky top-0 z-50 bg-white dark:bg-gray-800 shadow-md dark:shadow-gray-900/30 transition-colors duration-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-16">
        <!-- Logo -->
        <div class="flex-shrink-0">
          <NuxtLink
            to="/"
            class="flex items-center gap-3 text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-all duration-200 hover:-translate-y-0.5"
          >
            <span class="text-3xl">✈️</span>
            <span class="text-xl font-bold">Skaner Lotów</span>
          </NuxtLink>
        </div>

        <!-- Navigation -->
        <nav class="hidden md:flex items-center gap-1">
          <NuxtLink
            to="/"
            class="px-4 py-2 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200 font-medium"
            :class="{ 'bg-blue-50 dark:bg-gray-700 text-blue-600 dark:text-blue-400 font-semibold': $route.path === '/' }"
          >
            Strona Główna
          </NuxtLink>
          <NuxtLink
            to="/price-chart"
            class="px-4 py-2 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200 font-medium"
            :class="{ 'bg-blue-50 dark:bg-gray-700 text-blue-600 dark:text-blue-400 font-semibold': $route.path === '/price-chart' }"
          >
            Wykres Cen
          </NuxtLink>
          <NuxtLink
            to="/trip-search"
            class="px-4 py-2 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200 font-medium"
            :class="{ 'bg-blue-50 dark:bg-gray-700 text-blue-600 dark:text-blue-400 font-semibold': $route.path === '/trip-search' }"
          >
            Wyszukiwarka Tras
          </NuxtLink>

          <!-- Dark Mode Toggle -->
          <button
            @click="$emit('toggle-dark-mode')"
            class="ml-2 p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-all duration-200 hover:scale-110"
            :aria-label="isDarkMode ? 'Przełącz na tryb jasny' : 'Przełącz na tryb ciemny'"
          >
            <span class="text-2xl">{{ isDarkMode ? '☀️' : '🌙' }}</span>
          </button>
        </nav>

        <!-- Mobile menu button -->
        <div class="md:hidden flex items-center gap-2">
          <button
            @click="$emit('toggle-dark-mode')"
            class="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-all duration-200"
            :aria-label="isDarkMode ? 'Przełącz na tryb jasny' : 'Przełącz na tryb ciemny'"
          >
            <span class="text-xl">{{ isDarkMode ? '☀️' : '🌙' }}</span>
          </button>
          <button
            @click="mobileMenuOpen = !mobileMenuOpen"
            class="p-2 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            :aria-label="mobileMenuOpen ? 'Zamknij menu' : 'Otwórz menu'"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path v-if="!mobileMenuOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
              <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile Navigation Menu -->
    <div
      v-if="mobileMenuOpen"
      class="md:hidden border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800"
    >
      <div class="px-4 py-3 space-y-1">
        <NuxtLink
          to="/"
          @click="mobileMenuOpen = false"
          class="block px-4 py-3 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200 font-medium"
          :class="{ 'bg-blue-50 dark:bg-gray-700 text-blue-600 dark:text-blue-400 font-semibold': $route.path === '/' }"
        >
          Strona Główna
        </NuxtLink>
        <NuxtLink
          to="/price-chart"
          @click="mobileMenuOpen = false"
          class="block px-4 py-3 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200 font-medium"
          :class="{ 'bg-blue-50 dark:bg-gray-700 text-blue-600 dark:text-blue-400 font-semibold': $route.path === '/price-chart' }"
        >
          Wykres Cen
        </NuxtLink>
        <NuxtLink
          to="/trip-search"
          @click="mobileMenuOpen = false"
          class="block px-4 py-3 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200 font-medium"
          :class="{ 'bg-blue-50 dark:bg-gray-700 text-blue-600 dark:text-blue-400 font-semibold': $route.path === '/trip-search' }"
        >
          Wyszukiwarka Tras
        </NuxtLink>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  isDarkMode: {
    type: Boolean,
    default: false
  }
})

defineEmits(['toggle-dark-mode'])

const mobileMenuOpen = ref(false)
</script>

<style scoped>
/* All styling is now handled by Tailwind classes */
</style>
