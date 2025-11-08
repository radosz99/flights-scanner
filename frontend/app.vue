<template>
  <div :class="{ 'dark': isDarkMode }">
    <div class="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 transition-colors duration-200">
      <AppHeader :isDarkMode="isDarkMode" @toggle-dark-mode="toggleDarkMode" />
      <NuxtPage />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const isDarkMode = ref(false)

onMounted(() => {
  // Load dark mode preference from localStorage
  const savedDarkMode = localStorage.getItem('darkMode')
  isDarkMode.value = savedDarkMode === 'true'
})

const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value
  localStorage.setItem('darkMode', isDarkMode.value.toString())
}
</script>
