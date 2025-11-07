<template>
  <div class="container">
    <h1>Flight Price Chart</h1>
    <p class="subtitle">View price trends for your selected route over the full date range</p>

    <div v-if="loading" class="loading">
      {{ loadingMessage }}
    </div>

    <div v-if="error" class="error">
      <strong>Error:</strong> {{ error }}
    </div>

    <!-- Route Selection -->
    <div class="route-selection">
      <h2>Select Route</h2>

      <div class="selection-grid">
        <div class="selection-group">
          <label>Origin Airport</label>
          <select v-model="selectedOrigin" @change="onRouteChange">
            <option value="">Select origin...</option>
            <option v-for="origin in origins" :key="origin.code" :value="origin.code">
              {{ origin.code }} - {{ origin.name }} ({{ origin.flight_count }} flights)
            </option>
          </select>
        </div>

        <div class="selection-group">
          <label>Destination Airport</label>
          <select v-model="selectedDestination" @change="onRouteChange">
            <option value="">Select destination...</option>
            <option v-for="dest in destinations" :key="dest.code" :value="dest.code">
              {{ dest.code }} - {{ dest.name }} ({{ dest.flight_count }} flights)
            </option>
          </select>
        </div>
      </div>

      <div class="action-buttons">
        <button
          @click="loadChartData"
          :disabled="!selectedOrigin || !selectedDestination || loading"
          class="btn-primary"
        >
          {{ loading ? 'Loading...' : 'Load Price Chart' }}
        </button>
        <button
          @click="clearSelection"
          class="btn-secondary"
        >
          Clear Selection
        </button>
      </div>
    </div>

    <!-- Chart Display -->
    <div v-if="chartData && chartData.data.length > 0" class="chart-section">
      <div class="chart-header">
        <h2>
          Price Trends: {{ chartData.origin }} → {{ chartData.destination }}
        </h2>
        <div class="chart-stats">
          <span class="stat-item">
            <strong>Total Dates:</strong> {{ chartData.total_dates }}
          </span>
          <span class="stat-item">
            <strong>Date Range:</strong>
            {{ chartData.data[0].date }} to {{ chartData.data[chartData.data.length - 1].date }}
          </span>
        </div>
      </div>

      <div class="chart-container">
        <canvas ref="chartCanvas"></canvas>
      </div>

      <!-- Price Statistics Table -->
      <div class="price-stats">
        <h3>Price Statistics by Date</h3>
        <div class="stats-summary">
          <div class="stat-card">
            <div class="stat-value">{{ overallStats.minPrice }}{{ overallStats.currency }}</div>
            <div class="stat-label">Lowest Price</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ overallStats.maxPrice }}{{ overallStats.currency }}</div>
            <div class="stat-label">Highest Price</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ overallStats.avgPrice }}{{ overallStats.currency }}</div>
            <div class="stat-label">Average Price</div>
          </div>
        </div>

        <div class="table-container">
          <table class="price-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Min Price</th>
                <th>Avg Price</th>
                <th>Max Price</th>
                <th>Flights</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in chartData.data" :key="item.date">
                <td><strong>{{ item.date }}</strong></td>
                <td class="price-cell">{{ item.min_price }} {{ item.currency }}</td>
                <td class="price-cell">{{ item.avg_price }} {{ item.currency }}</td>
                <td class="price-cell">{{ item.max_price }} {{ item.currency }}</td>
                <td>{{ item.flight_count }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div v-else-if="!loading && selectedOrigin && selectedDestination" class="no-data">
      No price data available for the selected route. Try selecting a different route.
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { Chart, registerables } from 'chart.js'

// Register Chart.js components
Chart.register(...registerables)

const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl

const loading = ref(false)
const loadingMessage = ref('Loading...')
const error = ref(null)

const origins = ref([])
const destinations = ref([])
const selectedOrigin = ref('')
const selectedDestination = ref('')
const chartData = ref(null)
const chartCanvas = ref(null)
let chartInstance = null

// Computed overall statistics
const overallStats = computed(() => {
  if (!chartData.value || !chartData.value.data || chartData.value.data.length === 0) {
    return { minPrice: 0, maxPrice: 0, avgPrice: 0, currency: '' }
  }

  const data = chartData.value.data
  const minPrice = Math.min(...data.map(d => d.min_price))
  const maxPrice = Math.max(...data.map(d => d.max_price))
  const avgPrice = (data.reduce((sum, d) => sum + d.avg_price, 0) / data.length).toFixed(2)
  const currency = data[0].currency || ''

  return { minPrice, maxPrice, avgPrice, currency }
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
    const [originsResponse, destinationsResponse] = await Promise.all([
      $fetch(`${apiBaseUrl}/airports/origins`),
      $fetch(`${apiBaseUrl}/airports/destinations`)
    ])

    origins.value = originsResponse.origins || []
    destinations.value = destinationsResponse.destinations || []
  } catch (e) {
    error.value = e.message || 'Failed to load airports'
  } finally {
    loading.value = false
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
              const currency = data[context.dataIndex].currency || ''
              return `${label}: ${value} ${currency}`
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
            text: `Price (${data[0].currency || ''})`,
            font: {
              size: 14,
              weight: 'bold'
            }
          },
          beginAtZero: false,
          ticks: {
            font: {
              size: 12
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
  color: #28a745;
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
