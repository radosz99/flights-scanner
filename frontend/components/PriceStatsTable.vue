<template>
  <div v-if="chartData" class="mt-8">
    <h3 class="text-xl font-semibold text-gray-800 dark:text-gray-100 mb-4">Statystyki Cen według Daty</h3>

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
      <div class="bg-gradient-to-br from-purple-600 to-purple-800 dark:from-purple-700 dark:to-purple-900 text-white p-6 rounded-lg shadow-md text-center">
        <div class="text-3xl font-bold mb-2">{{ overallStats.minPrice }}</div>
        <div class="text-sm uppercase tracking-wide font-semibold opacity-90">Najniższa cena</div>
      </div>
      <div class="bg-gradient-to-br from-purple-600 to-purple-800 dark:from-purple-700 dark:to-purple-900 text-white p-6 rounded-lg shadow-md text-center">
        <div class="text-3xl font-bold mb-2">{{ overallStats.maxPrice }}</div>
        <div class="text-sm uppercase tracking-wide font-semibold opacity-90">Najwyższa cena</div>
      </div>
      <div class="bg-gradient-to-br from-purple-600 to-purple-800 dark:from-purple-700 dark:to-purple-900 text-white p-6 rounded-lg shadow-md text-center">
        <div class="text-3xl font-bold mb-2">{{ overallStats.avgPrice }}</div>
        <div class="text-sm uppercase tracking-wide font-semibold opacity-90">Średnia cena</div>
      </div>
    </div>

    <!-- Tip -->
    <div class="bg-blue-50 dark:bg-blue-900 border-2 border-blue-300 dark:border-blue-700 rounded-lg p-3 mb-4 text-blue-800 dark:text-blue-200 text-sm text-center">
      💡 <strong>Wskazówka:</strong> Kliknij na wiersz w tabeli, aby zobaczyć historię cen dla konkretnych lotów w danym dniu
    </div>

    <!-- Data Table -->
    <div class="overflow-x-auto mt-4">
      <table class="w-full border-collapse text-sm bg-white dark:bg-gray-800 rounded-lg shadow">
        <thead class="bg-gray-100 dark:bg-gray-700 border-b-2 border-gray-300 dark:border-gray-600">
          <tr>
            <th class="px-3 py-3 text-left font-semibold text-gray-700 dark:text-gray-200">Data</th>
            <th class="px-3 py-3 text-left font-semibold text-gray-700 dark:text-gray-200">Cena min</th>
            <th class="px-3 py-3 text-left font-semibold text-gray-700 dark:text-gray-200">Cena aktualna</th>
            <th class="px-3 py-3 text-left font-semibold text-gray-700 dark:text-gray-200">Cena śred.</th>
            <th class="px-3 py-3 text-left font-semibold text-gray-700 dark:text-gray-200">Cena max</th>
            <th class="px-3 py-3 text-left font-semibold text-gray-700 dark:text-gray-200">Lotów</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in chartData.data"
            :key="item.date"
            class="border-b border-gray-200 dark:border-gray-700 hover:bg-blue-50 dark:hover:bg-gray-700 transition-colors cursor-pointer"
            @click="$emit('date-click', item.date)"
          >
            <td class="px-3 py-3 font-semibold text-gray-900 dark:text-gray-200">
              {{ formatDate(item.date) }}
            </td>
            <td class="px-3 py-3 font-semibold text-green-600 dark:text-green-400">
              {{ formatPrice(item.min_price) }}
            </td>
            <td class="px-3 py-3 font-semibold text-yellow-600 dark:text-yellow-400">
              {{ formatPrice(item.current_price) }}
            </td>
            <td class="px-3 py-3 font-semibold text-blue-600 dark:text-blue-400">
              {{ formatPrice(item.avg_price) }}
            </td>
            <td class="px-3 py-3 font-semibold text-red-600 dark:text-red-400">
              {{ formatPrice(item.max_price) }}
            </td>
            <td class="px-3 py-3 text-gray-900 dark:text-gray-200">
              {{ item.flight_count }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatPrice, formatDate } from '~/utils/formatters'

const props = defineProps({
  chartData: Object
})

defineEmits(['date-click'])

const overallStats = computed(() => {
  if (!props.chartData || !props.chartData.data || props.chartData.data.length === 0) {
    return { minPrice: 'N/A', maxPrice: 'N/A', avgPrice: 'N/A' }
  }

  const data = props.chartData.data
  const minPrice = Math.min(...data.map(d => d.min_price))
  const maxPrice = Math.max(...data.map(d => d.max_price))
  const avgPrice = data.reduce((sum, d) => sum + d.avg_price, 0) / data.length

  return {
    minPrice: formatPrice(minPrice),
    maxPrice: formatPrice(maxPrice),
    avgPrice: formatPrice(avgPrice)
  }
})
</script>
