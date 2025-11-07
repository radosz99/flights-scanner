<template>
  <div class="container">
    <h1>Flights Scanner</h1>
    <p>Backend API: <code>{{ apiBaseUrl }}</code></p>

    <div v-if="loading" class="loading">
      {{ loadingMessage }}
    </div>

    <div v-if="healthData" class="health-status">
      <h2>API Health Status</h2>
      <pre>{{ JSON.stringify(healthData, null, 2) }}</pre>
    </div>

    <div v-if="scanStatus" class="scan-status">
      <h2>Latest Scan Status</h2>

      <div class="scan-info">
        <div class="info-row">
          <strong>Status:</strong>
          <span :class="'status-badge status-' + scanStatus.status">{{ scanStatus.status.toUpperCase() }}</span>
        </div>

        <div class="info-row">
          <strong>Started:</strong> {{ formatDateTime(scanStatus.start_time) }}
        </div>

        <div v-if="scanStatus.end_time" class="info-row">
          <strong>Completed:</strong> {{ formatDateTime(scanStatus.end_time) }}
        </div>

        <div v-if="scanStatus.progress" class="progress-section">
          <h3>Progress</h3>

          <div class="progress-bar-container">
            <div class="progress-bar" :style="{ width: scanStatus.progress.percentage + '%' }">
              <span class="progress-text">{{ scanStatus.progress.percentage }}%</span>
            </div>
          </div>

          <div class="progress-details">
            <div class="info-row">
              <strong>Date Ranges:</strong>
              {{ scanStatus.progress.completed_date_ranges }} / {{ scanStatus.progress.total_date_ranges }}
            </div>

            <div v-if="scanStatus.progress.current_date_range" class="info-row">
              <strong>Current Range:</strong> {{ scanStatus.progress.current_date_range }}
            </div>
          </div>
        </div>

        <div class="stats-section">
          <h3>Statistics</h3>
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-value">{{ scanStatus.stats.total_routes }}</div>
              <div class="stat-label">Total Routes</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ scanStatus.stats.successful_queries }}</div>
              <div class="stat-label">Successful</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ scanStatus.stats.failed_queries }}</div>
              <div class="stat-label">Failed</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ scanStatus.stats.flights_saved }}</div>
              <div class="stat-label">Flights Saved</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="scanResult" class="success">
      <h2>Scan Triggered</h2>
      <p><strong>Message:</strong> {{ scanResult.message }}</p>
      <p><strong>Scan ID:</strong> <code>{{ scanResult.scan_id }}</code></p>
      <p><strong>Config:</strong></p>
      <pre>{{ JSON.stringify(scanResult.config, null, 2) }}</pre>
    </div>

    <div v-if="error" class="error">
      <strong>Error:</strong> {{ error }}
    </div>

    <div class="actions">
      <button @click="checkHealth" :disabled="loading" class="btn-primary">
        {{ loading ? 'Checking...' : 'Refresh Health Status' }}
      </button>

      <button @click="checkLatestScan" :disabled="loading" class="btn-secondary">
        {{ loading ? 'Checking...' : 'Check Latest Scan' }}
      </button>

      <button @click="triggerScan" :disabled="loading || scanning" class="btn-success">
        {{ scanning ? 'Starting Scan...' : 'Trigger New Scan' }}
      </button>
    </div>

    <div class="info">
      <h3>Available Endpoints:</h3>
      <ul>
        <li><code>GET /health</code> - Check API health</li>
        <li><code>GET /flights</code> - Query flights</li>
        <li><code>GET /scans/latest</code> - Get latest scan status</li>
        <li><code>POST /scans/run</code> - Trigger new scan</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl
const healthData = ref(null)
const scanStatus = ref(null)
const scanResult = ref(null)
const error = ref(null)
const loading = ref(false)
const scanning = ref(false)
const loadingMessage = ref('Loading...')

const checkHealth = async () => {
  loading.value = true
  loadingMessage.value = 'Checking API health...'
  error.value = null
  healthData.value = null
  scanStatus.value = null
  scanResult.value = null

  try {
    const response = await $fetch(`${apiBaseUrl}/health`, {
      method: 'GET'
    })
    healthData.value = response
  } catch (e) {
    error.value = e.message || 'Failed to connect to backend API. Make sure the backend is running on http://localhost:8000'
  } finally {
    loading.value = false
  }
}

const checkLatestScan = async () => {
  loading.value = true
  loadingMessage.value = 'Fetching latest scan status...'
  error.value = null
  healthData.value = null
  scanStatus.value = null
  scanResult.value = null

  try {
    const response = await $fetch(`${apiBaseUrl}/scans/latest`, {
      method: 'GET'
    })
    scanStatus.value = response
  } catch (e) {
    if (e.statusCode === 404) {
      error.value = 'No scans found. Trigger a new scan to get started.'
    } else {
      error.value = e.message || 'Failed to fetch scan status'
    }
  } finally {
    loading.value = false
  }
}

const triggerScan = async () => {
  scanning.value = true
  loading.value = true
  loadingMessage.value = 'Triggering new scan...'
  error.value = null
  healthData.value = null
  scanStatus.value = null
  scanResult.value = null

  try {
    const response = await $fetch(`${apiBaseUrl}/scans/run`, {
      method: 'POST',
      body: {
        departure_airports: null, // Will use default (all Polish airports)
        trip_duration_days: 4,
        scan_until_date: '2025-12-31'
      }
    })
    scanResult.value = response
  } catch (e) {
    error.value = e.message || 'Failed to trigger scan'
  } finally {
    scanning.value = false
    loading.value = false
  }
}

// Format datetime for display
const formatDateTime = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleString()
}

// Check health on mount (client-side only)
onMounted(() => {
  checkHealth()
})
</script>

<style scoped>
.container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem;
  font-family: system-ui, -apple-system, sans-serif;
}

h1 {
  color: #2c3e50;
  margin-bottom: 1rem;
}

h2 {
  color: #34495e;
  margin-bottom: 0.5rem;
  font-size: 1.25rem;
}

h3 {
  color: #34495e;
  margin-bottom: 0.5rem;
  font-size: 1.1rem;
}

code {
  background: #f4f4f4;
  padding: 0.2rem 0.5rem;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.loading {
  margin-top: 2rem;
  padding: 1rem;
  background: #fff3cd;
  color: #856404;
  border-radius: 5px;
  border: 1px solid #ffeaa7;
}

.health-status,
.scan-status {
  margin-top: 2rem;
  padding: 1rem;
  background: #d4edda;
  color: #155724;
  border-radius: 5px;
  border: 1px solid #c3e6cb;
}

.success {
  margin-top: 2rem;
  padding: 1rem;
  background: #d1ecf1;
  color: #0c5460;
  border-radius: 5px;
  border: 1px solid #bee5eb;
}

.error {
  margin-top: 2rem;
  padding: 1rem;
  background: #f8d7da;
  color: #721c24;
  border-radius: 5px;
  border: 1px solid #f5c6cb;
}

.actions {
  margin-top: 2rem;
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

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
}

.btn-secondary {
  background: #6c757d;
}

.btn-secondary:hover:not(:disabled) {
  background: #545b62;
}

.btn-success {
  background: #28a745;
}

.btn-success:hover:not(:disabled) {
  background: #218838;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.info {
  margin-top: 2rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 5px;
  border: 1px solid #dee2e6;
}

.info ul {
  margin: 0.5rem 0 0 0;
  padding-left: 1.5rem;
}

.info li {
  margin: 0.5rem 0;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0.5rem 0 0 0;
  background: rgba(0, 0, 0, 0.05);
  padding: 0.75rem;
  border-radius: 3px;
  font-size: 0.85rem;
}

.scan-info {
  margin-top: 0.5rem;
}

.info-row {
  margin: 0.75rem 0;
  font-size: 0.95rem;
}

.info-row strong {
  display: inline-block;
  min-width: 140px;
  color: #2c3e50;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.85rem;
  text-transform: uppercase;
}

.status-running {
  background: #fff3cd;
  color: #856404;
}

.status-completed {
  background: #d4edda;
  color: #155724;
}

.status-failed {
  background: #f8d7da;
  color: #721c24;
}

.progress-section {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

.progress-bar-container {
  width: 100%;
  height: 30px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 15px;
  overflow: hidden;
  margin: 1rem 0;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #28a745, #20c997);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: width 0.3s ease;
  min-width: 40px;
}

.progress-text {
  color: white;
  font-weight: 600;
  font-size: 0.85rem;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.progress-details {
  margin-top: 0.5rem;
}

.stats-section {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.stat-card {
  background: rgba(0, 0, 0, 0.03);
  padding: 1rem;
  border-radius: 8px;
  text-align: center;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #2c3e50;
  line-height: 1;
  margin-bottom: 0.5rem;
}

.stat-label {
  font-size: 0.85rem;
  color: #6c757d;
  text-transform: uppercase;
  font-weight: 600;
  letter-spacing: 0.5px;
}
</style>
