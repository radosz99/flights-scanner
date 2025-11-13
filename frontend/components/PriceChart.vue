<template>
  <div v-if="chartData && chartData.data.length > 0" class="mt-8 p-6 bg-white dark:bg-gray-800 rounded-xl shadow-md">
    <!-- Header -->
    <div class="mb-6">
      <h2 class="text-2xl font-semibold text-gray-800 dark:text-gray-100 mb-2">
        Trendy Cenowe: {{ chartData.origin }} → {{ chartData.destination }}
      </h2>
      <div class="flex flex-wrap gap-6 text-sm text-gray-600 dark:text-gray-400">
        <span class="flex gap-2">
          <strong class="text-gray-800 dark:text-gray-300">Łącznie dat:</strong>
          {{ chartData.total_dates }}
        </span>
        <span class="flex gap-2">
          <strong class="text-gray-800 dark:text-gray-300">Zakres dat:</strong>
          {{ chartData.data[0].date }} do {{ chartData.data[chartData.data.length - 1].date }}
        </span>
      </div>
    </div>

    <!-- Tip -->
    <div class="bg-blue-50 dark:bg-blue-900 border-2 border-blue-300 dark:border-blue-700 rounded-lg p-3 mb-6 text-blue-800 dark:text-blue-200 text-sm text-center">
      💡 <strong>Wskazówka:</strong> Kliknij na element legendy, aby pokazać/ukryć daną linię cen na wykresie
    </div>

    <!-- Chart Canvas -->
    <div class="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
      <canvas ref="chartCanvas"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const props = defineProps({
  chartData: Object
})

const chartCanvas = ref(null)
let chartInstance = null

const renderChart = () => {
  if (!chartCanvas.value || !props.chartData) return

  // Destroy existing chart if any
  if (chartInstance) {
    chartInstance.destroy()
  }

  const data = props.chartData.data
  const labels = data.map(d => d.date)
  const minPrices = data.map(d => d.min_price)
  const currentPrices = data.map(d => d.current_price)
  const avgPrices = data.map(d => d.avg_price)
  const maxPrices = data.map(d => d.max_price)

  // Detect dark mode
  const isDark = document.documentElement.classList.contains('dark')

  // Define colors based on theme
  const colors = {
    min: isDark ? '#4ade80' : '#28a745',
    minBg: isDark ? 'rgba(74, 222, 128, 0.1)' : 'rgba(40, 167, 69, 0.1)',
    current: isDark ? '#fbbf24' : '#ffc107',
    currentBg: isDark ? 'rgba(251, 191, 36, 0.1)' : 'rgba(255, 193, 7, 0.1)',
    avg: isDark ? '#60a5fa' : '#007bff',
    avgBg: isDark ? 'rgba(96, 165, 250, 0.1)' : 'rgba(0, 123, 255, 0.1)',
    max: isDark ? '#f87171' : '#dc3545',
    maxBg: isDark ? 'rgba(248, 113, 113, 0.1)' : 'rgba(220, 53, 69, 0.1)',
    text: isDark ? '#e5e7eb' : '#374151',
    grid: isDark ? 'rgba(107, 114, 128, 0.3)' : 'rgba(0, 0, 0, 0.1)',
    tooltipBg: isDark ? 'rgba(31, 41, 55, 0.95)' : 'rgba(0, 0, 0, 0.8)'
  }

  const ctx = chartCanvas.value.getContext('2d')

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Cena minimalna',
          data: minPrices,
          borderColor: colors.min,
          backgroundColor: colors.minBg,
          pointBackgroundColor: colors.min,
          pointBorderColor: colors.min,
          borderWidth: 2,
          pointRadius: 3,
          pointHoverRadius: 5,
          tension: 0.1
        },
        {
          label: 'Cena aktualna',
          data: currentPrices,
          borderColor: colors.current,
          backgroundColor: colors.currentBg,
          pointBackgroundColor: colors.current,
          pointBorderColor: colors.current,
          borderWidth: 2,
          pointRadius: 3,
          pointHoverRadius: 5,
          tension: 0.1
        },
        {
          label: 'Cena średnia',
          data: avgPrices,
          borderColor: colors.avg,
          backgroundColor: colors.avgBg,
          pointBackgroundColor: colors.avg,
          pointBorderColor: colors.avg,
          borderWidth: 2,
          pointRadius: 3,
          pointHoverRadius: 5,
          tension: 0.1
        },
        {
          label: 'Cena maksymalna',
          data: maxPrices,
          borderColor: colors.max,
          backgroundColor: colors.maxBg,
          pointBackgroundColor: colors.max,
          pointBorderColor: colors.max,
          borderWidth: 2,
          pointRadius: 3,
          pointHoverRadius: 5,
          tension: 0.1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      aspectRatio: 2,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: {
            color: colors.text,
            font: {
              size: 14,
              weight: '600'
            },
            usePointStyle: true,
            padding: 20
          },
          onClick: (e, legendItem, legend) => {
            const index = legendItem.datasetIndex
            const chart = legend.chart
            const meta = chart.getDatasetMeta(index)
            meta.hidden = meta.hidden === null ? !chart.data.datasets[index].hidden : null
            chart.update()
          }
        },
        title: {
          display: true,
          text: `Trendy cenowe: ${props.chartData.origin} → ${props.chartData.destination}`,
          color: colors.text,
          font: {
            size: 18,
            weight: 'bold'
          },
          padding: 20
        },
        tooltip: {
          backgroundColor: colors.tooltipBg,
          titleColor: '#ffffff',
          bodyColor: '#ffffff',
          titleFont: {
            size: 14,
            weight: 'bold'
          },
          bodyFont: {
            size: 13
          },
          padding: 12,
          displayColors: true,
          callbacks: {
            label: function(context) {
              const label = context.dataset.label || ''
              const value = context.parsed.y
              return `${label}: ${value.toFixed(2)} PLN`
            }
          }
        }
      },
      scales: {
        x: {
          display: true,
          grid: {
            color: colors.grid
          },
          ticks: {
            color: colors.text,
            maxRotation: 45,
            minRotation: 45,
            font: {
              size: 11
            }
          },
          title: {
            display: true,
            text: 'Data',
            color: colors.text,
            font: {
              size: 14,
              weight: 'bold'
            }
          }
        },
        y: {
          display: true,
          grid: {
            color: colors.grid
          },
          ticks: {
            color: colors.text,
            font: {
              size: 12
            },
            callback: function(value) {
              return value.toFixed(2) + ' PLN'
            }
          },
          title: {
            display: true,
            text: 'Cena (PLN)',
            color: colors.text,
            font: {
              size: 14,
              weight: 'bold'
            }
          },
          beginAtZero: false
        }
      }
    }
  })
}

watch(() => props.chartData, async (newData) => {
  if (newData && newData.data && newData.data.length > 0) {
    await nextTick()
    renderChart()
  }
}, { deep: true })

onMounted(async () => {
  if (props.chartData && props.chartData.data && props.chartData.data.length > 0) {
    await nextTick()
    renderChart()
  }
})

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.destroy()
  }
})
</script>
