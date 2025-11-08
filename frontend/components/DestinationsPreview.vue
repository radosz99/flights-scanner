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

    <div class="overflow-x-auto bg-white dark:bg-gray-800 rounded-lg shadow mt-4">
      <table class="w-full border-collapse text-sm">
        <thead class="bg-blue-100 dark:bg-blue-900 border-b-2 border-blue-300 dark:border-blue-700">
          <tr>
            <th class="px-4 py-3 text-left font-semibold text-gray-800 dark:text-gray-100">Code</th>
            <th class="px-4 py-3 text-left font-semibold text-gray-800 dark:text-gray-100">Destination</th>
            <th class="px-4 py-3 text-right font-semibold text-gray-800 dark:text-gray-100">Lowest Price</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="dest in destinations"
            :key="dest.destination"
            @click="$emit('select', dest)"
            :class="[
              'border-b border-gray-200 dark:border-gray-700 cursor-pointer transition-colors',
              selectedDestination === dest.destination
                ? 'bg-blue-100 dark:bg-blue-900'
                : 'hover:bg-blue-50 dark:hover:bg-gray-700'
            ]"
          >
            <td class="px-4 py-3 font-bold text-gray-900 dark:text-gray-100">
              {{ dest.destination }}
            </td>
            <td class="px-4 py-3 text-gray-700 dark:text-gray-300">
              {{ dest.destination_name }}
            </td>
            <td class="px-4 py-3 text-right font-bold text-green-600 dark:text-green-400 text-lg">
              {{ formatPrice(dest.min_total_price) }}
            </td>
          </tr>
        </tbody>
      </table>
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
