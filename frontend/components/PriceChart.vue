<template>
  <div v-if="chartData && chartData.data.length > 0" class="mt-8 p-6 bg-white dark:bg-gray-800 rounded-xl shadow-md">
    <!-- Header -->
    <div class="mb-6">
      <h2 class="text-2xl font-semibold text-gray-800 dark:text-gray-100 mb-2">
        Price Trends: {{ chartData.origin }} → {{ chartData.destination }}
      </h2>
      <div class="flex flex-wrap gap-6 text-sm text-gray-600 dark:text-gray-400">
        <span class="flex gap-2">
          <strong class="text-gray-800 dark:text-gray-300">Total Dates:</strong>
          {{ chartData.total_dates }}
        </span>
        <span class="flex gap-2">
          <strong class="text-gray-800 dark:text-gray-300">Date Range:</strong>
          {{ chartData.data[0].date }} to {{ chartData.data[chartData.data.length - 1].date }}
        </span>
      </div>
    </div>

    <!-- Tip -->
    <div class="bg-blue-50 dark:bg-blue-900 border-2 border-blue-300 dark:border-blue-700 rounded-lg p-3 mb-6 text-blue-800 dark:text-blue-200 text-sm text-center">
      💡 <strong>Tip:</strong> Click on any legend item to show/hide that price line on the chart
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

  const ctx = chartCanvas.value.getContext('2d')

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Minimum Price',
          data: minPrices,
          borderColor: '#28a745',
          backgroundColor: 'rgba(40, 167, 69, 0.1)',
          borderWidth: 2,
          pointRadius: 3,
          pointHoverRadius: 5,
          tension: 0.1
        },
        {
          label: 'Current Price',
          data: currentPrices,
          borderColor: '#ffc107',
          backgroundColor: 'rgba(255, 193, 7, 0.1)',
          borderWidth: 2,
          pointRadius: 3,
          pointHoverRadius: 5,
          tension: 0.1
        },
        {
          label: 'Average Price',
          data: avgPrices,
          borderColor: '#007bff',
          backgroundColor: 'rgba(0, 123, 255, 0.1)',
          borderWidth: 2,
          pointRadius: 3,
          pointHoverRadius: 5,
          tension: 0.1
        },
        {
          label: 'Maximum Price',
          data: maxPrices,
          borderColor: '#dc3545',
          backgroundColor: 'rgba(220, 53, 69, 0.1)',
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
          text: `Price Trends: ${props.chartData.origin} → ${props.chartData.destination}`,
          font: {
            size: 18,
            weight: 'bold'
          },
          padding: 20
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
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
          title: {
            display: true,
            text: 'Date',
            font: {
              size: 14,
              weight: 'bold'
            }
          },
          ticks: {
            maxRotation: 45,
            minRotation: 45,
            font: {
              size: 11
            }
          }
        },
        y: {
          display: true,
          title: {
            display: true,
            text: 'Price (PLN)',
            font: {
              size: 14,
              weight: 'bold'
            }
          },
          beginAtZero: false,
          ticks: {
            font: {
              size: 12
            },
            callback: function(value) {
              return value.toFixed(2) + ' PLN'
            }
          }
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
