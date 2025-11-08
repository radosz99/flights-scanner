<template>
  <div class="container dark:bg-gray-900">
    <h1 class="dark:text-gray-100">Flight Price Chart</h1>
    <p class="subtitle dark:text-gray-400">View price trends for your selected route over the full date range</p>

    <div v-if="loading" class="loading dark:bg-yellow-900 dark:text-yellow-200 dark:border-yellow-700">
      {{ loadingMessage }}
    </div>

    <div v-if="error" class="error dark:bg-red-900 dark:text-red-200 dark:border-red-700">
      <strong>Error:</strong> {{ error }}
    </div>

    <!-- Route Selection -->
    <div class="route-selection dark:bg-gray-800">
      <h2 class="dark:text-gray-100 dark:border-gray-700">Select Route</h2>

      <div class="selection-grid">
        <div class="selection-group">
          <label class="dark:text-gray-200">Origin Airport</label>
          <select v-model="selectedOrigin" @change="onOriginChange" class="dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500">
            <option value="">Select origin...</option>
            <option v-for="origin in origins" :key="origin.code" :value="origin.code">
              {{ origin.code }} - {{ origin.name }} ({{ origin.flight_count }} flights)
            </option>
          </select>
        </div>

        <div class="selection-group">
          <label class="dark:text-gray-200">Destination Airport</label>
          <select
            v-model="selectedDestination"
            @change="onDestinationChange"
            :disabled="!selectedOrigin || availableDestinations.length === 0"
            class="dark:bg-gray-600 dark:text-gray-100 dark:border-gray-500 dark:disabled:bg-gray-700 dark:disabled:text-gray-400"
          >
            <option value="">{{ selectedOrigin ? 'Select destination...' : 'Select origin first' }}</option>
            <option v-for="dest in availableDestinations" :key="dest.code" :value="dest.code">
              {{ dest.code }} - {{ dest.name }} ({{ dest.flight_count }} flights)
            </option>
          </select>
        </div>
      </div>

      <div class="action-buttons">
        <button
          @click="loadChartData"
          :disabled="!selectedOrigin || !selectedDestination || loading"
          class="btn-primary dark:bg-blue-600 dark:hover:bg-blue-700"
        >
          {{ loading ? 'Loading...' : 'Load Price Chart' }}
        </button>
        <button
          @click="clearSelection"
          class="btn-secondary dark:bg-gray-600 dark:hover:bg-gray-700"
        >
          Clear Selection
        </button>
      </div>
    </div>

    <!-- Chart Display -->
    <div v-if="chartData && chartData.data.length > 0" class="chart-section dark:bg-gray-800">
      <div class="chart-header">
        <h2 class="dark:text-gray-100 dark:border-gray-700">
          Price Trends: {{ chartData.origin }} → {{ chartData.destination }}
        </h2>
        <div class="chart-stats dark:text-gray-400">
          <span class="stat-item">
            <strong class="dark:text-gray-300">Total Dates:</strong> {{ chartData.total_dates }}
          </span>
          <span class="stat-item">
            <strong class="dark:text-gray-300">Date Range:</strong>
            {{ chartData.data[0].date }} to {{ chartData.data[chartData.data.length - 1].date }}
          </span>
        </div>
      </div>

      <div class="chart-info-text dark:bg-blue-900 dark:text-blue-200 dark:border-blue-700">
        💡 <strong>Tip:</strong> Click on any legend item to show/hide that price line on the chart
      </div>

      <div class="chart-container dark:bg-gray-700">
        <canvas ref="chartCanvas"></canvas>
      </div>

      <!-- Price Statistics Table -->
      <div class="price-stats">
        <h3 class="dark:text-gray-100">Price Statistics by Date</h3>
        <div class="stats-summary">
          <div class="stat-card dark:bg-gradient-to-br dark:from-purple-700 dark:to-purple-900">
            <div class="stat-value dark:text-gray-100">{{ overallStats.minPrice }}</div>
            <div class="stat-label dark:text-gray-200">Lowest Price</div>
          </div>
          <div class="stat-card dark:bg-gradient-to-br dark:from-purple-700 dark:to-purple-900">
            <div class="stat-value dark:text-gray-100">{{ overallStats.maxPrice }}</div>
            <div class="stat-label dark:text-gray-200">Highest Price</div>
          </div>
          <div class="stat-card dark:bg-gradient-to-br dark:from-purple-700 dark:to-purple-900">
            <div class="stat-value dark:text-gray-100">{{ overallStats.avgPrice }}</div>
            <div class="stat-label dark:text-gray-200">Average Price</div>
          </div>
        </div>

        <div class="table-container">
          <table class="price-table">
            <thead class="dark:bg-gray-700 dark:border-gray-600">
              <tr>
                <th class="dark:text-gray-200">Date</th>
                <th class="dark:text-gray-200">Min Price</th>
                <th class="dark:text-gray-200">Current Price</th>
                <th class="dark:text-gray-200">Avg Price</th>
                <th class="dark:text-gray-200">Max Price</th>
                <th class="dark:text-gray-200">Flights</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in chartData.data" :key="item.date" class="dark:border-gray-700 dark:hover:bg-gray-700">
                <td class="dark:text-gray-200"><strong>{{ formatDate(item.date) }}</strong></td>
                <td class="price-cell min-price dark:text-green-400">{{ formatPrice(item.min_price) }}</td>
                <td class="price-cell current-price dark:text-yellow-400">{{ formatPrice(item.current_price) }}</td>
                <td class="price-cell avg-price dark:text-blue-400">{{ formatPrice(item.avg_price) }}</td>
                <td class="price-cell max-price dark:text-red-400">{{ formatPrice(item.max_price) }}</td>
                <td class="dark:text-gray-200">{{ item.flight_count }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div v-else-if="!loading && selectedOrigin && selectedDestination" class="no-data dark:bg-gray-700 dark:text-gray-300">
      No price data available for the selected route. Try selecting a different route.
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { Chart, registerables } from 'chart.js'
import { formatPrice, formatDate } from '~/utils/formatters'

// Register Chart.js components
Chart.register(...registerables)

const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl

const loading = ref(false)
const loadingMessage = ref('Loading...')
const error = ref(null)

const origins = ref([])
const destinations = ref([])
const availableDestinations = ref([]) // Destinations from selected origin
const selectedOrigin = ref('')
const selectedDestination = ref('')
const chartData = ref(null)
const chartCanvas = ref(null)
let chartInstance = null

// Computed overall statistics
const overallStats = computed(() => {
  if (!chartData.value || !chartData.value.data || chartData.value.data.length === 0) {
    return { minPrice: 'N/A', maxPrice: 'N/A', avgPrice: 'N/A' }
  }

  const data = chartData.value.data
  const minPrice = Math.min(...data.map(d => d.min_price))
  const maxPrice = Math.max(...data.map(d => d.max_price))
  const avgPrice = data.reduce((sum, d) => sum + d.avg_price, 0) / data.length

  return {
    minPrice: formatPrice(minPrice),
    maxPrice: formatPrice(maxPrice),
    avgPrice: formatPrice(avgPrice)
  }
})

// Load origins and destinations on mount
onMounted(async () => {
  await loadAirports()
})

const loadAirports = async () => {
  loading.value = true
  loadingMessage.value = 'Loading airports...'
  error.value = null

  try {
    // Only load origins initially
    const originsResponse = await $fetch(`${apiBaseUrl}/airports/origins`)
    origins.value = originsResponse.origins || []
  } catch (e) {
    error.value = e.message || 'Failed to load airports'
  } finally {
    loading.value = false
  }
}

const loadDestinationsFromOrigin = async (origin) => {
  if (!origin) {
    availableDestinations.value = []
    return
  }

  loading.value = true
  loadingMessage.value = 'Loading destinations...'
  error.value = null

  try {
    const response = await $fetch(`${apiBaseUrl}/airports/origins/${origin}/destinations`)
    availableDestinations.value = response.destinations || []
  } catch (e) {
    error.value = e.message || 'Failed to load destinations'
    availableDestinations.value = []
  } finally {
    loading.value = false
  }
}

const onOriginChange = async () => {
  // Clear destination selection when origin changes
  selectedDestination.value = ''
  chartData.value = null

  // Load destinations for selected origin
  if (selectedOrigin.value) {
    await loadDestinationsFromOrigin(selectedOrigin.value)
  } else {
    availableDestinations.value = []
  }
}

const onDestinationChange = () => {
  // Auto-load chart when both origin and destination are selected
  if (selectedOrigin.value && selectedDestination.value) {
    loadChartData()
  }
}

const onRouteChange = () => {
  // Auto-load chart when both origin and destination are selected
  if (selectedOrigin.value && selectedDestination.value) {
    loadChartData()
  }
}

const loadChartData = async () => {
  if (!selectedOrigin.value || !selectedDestination.value) {
    error.value = 'Please select both origin and destination'
    return
  }

  loading.value = true
  loadingMessage.value = 'Loading price data...'
  error.value = null
  chartData.value = null

  try {
    const response = await $fetch(`${apiBaseUrl}/flights/price-chart`, {
      params: {
        origin: selectedOrigin.value,
        destination: selectedDestination.value
      }
    })

    chartData.value = response

    // Wait for DOM update before rendering chart
    await nextTick()
    renderChart()
  } catch (e) {
    if (e.statusCode === 404) {
      error.value = `No flights found for route ${selectedOrigin.value} → ${selectedDestination.value}`
    } else {
      error.value = e.message || 'Failed to load price chart data'
    }
    chartData.value = null
  } finally {
    loading.value = false
  }
}

const renderChart = () => {
  if (!chartCanvas.value || !chartData.value) return

  // Destroy existing chart if any
  if (chartInstance) {
    chartInstance.destroy()
  }

  const data = chartData.value.data
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

            // Toggle visibility
            meta.hidden = meta.hidden === null ? !chart.data.datasets[index].hidden : null

            // Re-render chart
            chart.update()
          }
        },
        title: {
          display: true,
          text: `Price Trends: ${chartData.value.origin} → ${chartData.value.destination}`,
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

const clearSelection = () => {
  selectedOrigin.value = ''
  selectedDestination.value = ''
  availableDestinations.value = []
  chartData.value = null
  error.value = null

  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
}

// Watch for route changes in query params
watch(() => [selectedOrigin.value, selectedDestination.value], () => {
  error.value = null
})
</script>

<style scoped>
.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
  font-family: system-ui, -apple-system, sans-serif;
}

h1 {
  color: #2c3e50;
  margin-bottom: 0.5rem;
  font-size: 2.5rem;
}

.subtitle {
  color: #6c757d;
  font-size: 1.1rem;
  margin-bottom: 2rem;
}

h2 {
  color: #34495e;
  margin-bottom: 1rem;
  font-size: 1.5rem;
  border-bottom: 2px solid #e0e0e0;
  padding-bottom: 0.5rem;
}

h3 {
  color: #34495e;
  margin-bottom: 1rem;
  font-size: 1.2rem;
}

.loading {
  margin-top: 2rem;
  padding: 1rem;
  background: #fff3cd;
  color: #856404;
  border-radius: 5px;
  border: 1px solid #ffeaa7;
  text-align: center;
  font-size: 1.1rem;
}

.error {
  margin-top: 2rem;
  padding: 1rem;
  background: #f8d7da;
  color: #721c24;
  border-radius: 5px;
  border: 1px solid #f5c6cb;
}

.no-data {
  margin-top: 2rem;
  padding: 2rem;
  background: #f8f9fa;
  color: #6c757d;
  border-radius: 8px;
  text-align: center;
  font-size: 1.1rem;
}

/* Route Selection */
.route-selection {
  margin-top: 2rem;
  padding: 1.5rem;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.selection-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-top: 1rem;
}

.selection-group {
  display: flex;
  flex-direction: column;
}

.selection-group label {
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #495057;
  font-size: 1rem;
}

.selection-group select {
  padding: 0.75rem;
  border: 2px solid #ced4da;
  border-radius: 5px;
  font-size: 1rem;
  background: white;
  cursor: pointer;
  transition: border-color 0.2s;
}

.selection-group select:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.selection-group select:disabled {
  background: #e9ecef;
  cursor: not-allowed;
  opacity: 0.6;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

/* Chart Section */
.chart-section {
  margin-top: 2rem;
  padding: 1.5rem;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.chart-header {
  margin-bottom: 1.5rem;
}

.chart-stats {
  display: flex;
  gap: 2rem;
  margin-top: 0.5rem;
  font-size: 0.95rem;
  color: #6c757d;
}

.stat-item {
  display: flex;
  gap: 0.5rem;
}

.chart-info-text {
  background: #e7f3ff;
  border: 2px solid #2196f3;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  margin: 1rem 0;
  color: #1565c0;
  font-size: 0.95rem;
  text-align: center;
}

.chart-container {
  margin: 2rem 0;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
}

/* Price Statistics */
.price-stats {
  margin-top: 2rem;
}

.stats-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin: 1rem 0 2rem 0;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.25rem;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.stat-label {
  font-size: 0.85rem;
  text-transform: uppercase;
  font-weight: 600;
  letter-spacing: 0.5px;
  opacity: 0.9;
}

.table-container {
  overflow-x: auto;
  margin-top: 1rem;
}

.price-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
}

.price-table thead {
  background: #f8f9fa;
  border-bottom: 2px solid #dee2e6;
}

.price-table th {
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  color: #495057;
}

.price-table tbody tr {
  border-bottom: 1px solid #dee2e6;
  transition: background-color 0.2s;
}

.price-table tbody tr:hover {
  background: #f8f9fa;
}

.price-table td {
  padding: 0.75rem;
}

.price-cell {
  font-weight: 600;
}

.price-cell.min-price {
  color: #28a745;
}

.price-cell.current-price {
  color: #ffc107;
}

.price-cell.avg-price {
  color: #007bff;
}

.price-cell.max-price {
  color: #dc3545;
}

/* Buttons */
button {
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 5px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
}

.btn-primary {
  background: #007bff;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 123, 255, 0.3);
}

.btn-secondary {
  background: #6c757d;
}

.btn-secondary:hover:not(:disabled) {
  background: #545b62;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Responsive Design */
@media (max-width: 768px) {
  .container {
    padding: 1rem;
  }

  h1 {
    font-size: 2rem;
  }

  .selection-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .action-buttons {
    flex-direction: column;
  }

  .chart-stats {
    flex-direction: column;
    gap: 0.5rem;
  }

  .stats-summary {
    grid-template-columns: 1fr;
  }
}
</style>
