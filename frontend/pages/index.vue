<template>
  <div class="container">
    <h1>Flights Scanner</h1>
    <p>Backend API endpoint: <code>{{ apiEndpoint }}</code></p>

    <div v-if="healthData" class="health-status">
      <h2>API Health Status</h2>
      <pre>{{ healthData }}</pre>
    </div>

    <div v-if="error" class="error">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
const apiEndpoint = 'http://localhost:8000/health'
const { data: healthData, error } = await useFetch(apiEndpoint, {
  server: true
})
</script>

<style scoped>
.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
  font-family: system-ui, -apple-system, sans-serif;
}

h1 {
  color: #2c3e50;
  margin-bottom: 1rem;
}

code {
  background: #f4f4f4;
  padding: 0.2rem 0.5rem;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}

.health-status {
  margin-top: 2rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 5px;
}

.error {
  margin-top: 2rem;
  padding: 1rem;
  background: #fee;
  color: #c33;
  border-radius: 5px;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
