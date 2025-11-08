<template>
  <div
    v-if="origin && destinations.length > 0"
    class="mt-8 p-6 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900 dark:to-blue-800 rounded-xl shadow-md border-2 border-blue-300 dark:border-blue-700"
  >
    <h2 class="text-2xl font-semibold text-gray-800 dark:text-gray-100 mb-1">
      Available Destinations from {{ origin }}
    </h2>
    <p class="text-sm text-blue-800 dark:text-blue-200 font-medium mb-4">
      Showing lowest round-trip prices ({{ minDays }}-{{ maxDays }} days)
    </p>

    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 mt-4">
      <div
        v-for="dest in destinations"
        :key="dest.destination"
        @click="$emit('select', dest)"
        :class="[
          'bg-white dark:bg-gray-700 border-2 rounded-lg p-4 cursor-pointer transition-all duration-200',
          'hover:-translate-y-1 hover:shadow-lg hover:border-blue-500 dark:hover:border-blue-500',
          selectedDestination === dest.destination
            ? 'border-blue-500 dark:border-blue-500 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-gray-600 dark:to-gray-700 border-3'
            : 'border-gray-300 dark:border-gray-600'
        ]"
      >
        <div class="mb-3">
          <div class="text-xl font-bold text-gray-900 dark:text-gray-100 mb-1">
            {{ dest.destination }}
          </div>
          <div class="text-xs text-gray-600 dark:text-gray-400 leading-tight">
            {{ dest.destination_name }}
          </div>
        </div>

        <div class="pt-3 border-t border-gray-200 dark:border-gray-600 text-center">
          <div class="text-xs uppercase text-gray-500 dark:text-gray-400 tracking-wide mb-1">
            From
          </div>
          <div class="text-xl font-bold text-green-600 dark:text-green-400">
            {{ formatPrice(dest.min_total_price) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { formatPrice } from '~/utils/formatters'

const props = defineProps({
  origin: String,
  destinations: Array,
  minDays: Number,
  maxDays: Number,
  selectedDestination: String
})

defineEmits(['select'])
</script>
