<template>
  <div v-if="stats" class="mt-8 p-6 bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900 dark:to-purple-700 rounded-xl shadow-md">
    <h2 class="text-2xl font-semibold text-gray-800 dark:text-gray-100 border-b-2 border-purple-300 dark:border-purple-600 pb-2 mb-4">
      Statystyki Bazy Danych
    </h2>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div class="bg-white/50 dark:bg-purple-800/30 border-2 border-purple-200 dark:border-purple-600 rounded-lg p-6 text-center">
        <div class="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-2">{{ stats.total_flights }}</div>
        <div class="text-sm uppercase tracking-wide font-semibold text-purple-800 dark:text-gray-200">Wszystkie Loty</div>
      </div>
      <div class="bg-white/50 dark:bg-purple-800/30 border-2 border-purple-200 dark:border-purple-600 rounded-lg p-6 text-center">
        <div class="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-2">{{ stats.unique_origins }}</div>
        <div class="text-sm uppercase tracking-wide font-semibold text-purple-800 dark:text-gray-200">Lotniska Wylotu</div>
      </div>
      <div class="bg-white/50 dark:bg-purple-800/30 border-2 border-purple-200 dark:border-purple-600 rounded-lg p-6 text-center">
        <div class="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-2">{{ stats.unique_destinations }}</div>
        <div class="text-sm uppercase tracking-wide font-semibold text-purple-800 dark:text-gray-200">Lotniska Docelowe</div>
      </div>
      <div class="bg-white/50 dark:bg-purple-800/30 border-2 border-purple-200 dark:border-purple-600 rounded-lg p-6 text-center">
        <div class="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-2">{{ formatPrice(stats.average_price) }}</div>
        <div class="text-sm uppercase tracking-wide font-semibold text-purple-800 dark:text-gray-200">Średnia Cena</div>
      </div>
    </div>

    <div v-if="stats.cheapest_flight" class="bg-white/50 dark:bg-purple-800/30 border-2 border-purple-200 dark:border-purple-600 rounded-lg p-4">
      <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-2">Najtańszy Lot</h3>
      <p class="text-gray-800 dark:text-gray-200">
        <strong class="text-gray-900 dark:text-gray-100">{{ stats.cheapest_flight.route }}</strong> -
        {{ formatPrice(stats.cheapest_flight.price) }} on
        {{ formatDate(stats.cheapest_flight.date) }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { formatPrice, formatDate } from '~/utils/formatters'

const props = defineProps({
  stats: Object
})
</script>
