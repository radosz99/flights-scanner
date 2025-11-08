<template>
  <div v-if="routes.length > 0 && !origin" class="mt-8 p-6 bg-white dark:bg-gray-800 rounded-xl shadow-md">
    <div
      @click="toggleExpanded"
      class="flex justify-between items-center cursor-pointer select-none hover:opacity-80 transition"
    >
      <h2 class="text-2xl font-semibold text-gray-800 dark:text-gray-100 border-b-2 border-gray-200 dark:border-gray-700 pb-2">
        Popular Round Trip Routes
      </h2>
      <button
        class="text-3xl text-gray-600 dark:text-gray-300 hover:text-blue-500 dark:hover:text-blue-400 transition p-2"
        :aria-label="isExpanded ? 'Collapse' : 'Expand'"
      >
        {{ isExpanded ? '▼' : '▶' }}
      </button>
    </div>

    <div v-if="isExpanded">
      <p class="text-sm text-gray-600 dark:text-gray-400 mt-2 mb-4">
        Click on a route to search for round trips
      </p>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mt-4">
        <div
          v-for="route in routes"
          :key="`${route.origin}-${route.destination}`"
          @click="$emit('select', route)"
          class="bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-700 dark:to-gray-600 border-2 border-gray-300 dark:border-gray-600 rounded-lg p-4 cursor-pointer transition-all duration-200 hover:-translate-y-1 hover:shadow-lg hover:border-blue-500 dark:hover:border-blue-500 hover:from-blue-50 hover:to-blue-100 dark:hover:from-gray-600 dark:hover:to-gray-700"
        >
          <div class="mb-3">
            <div class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
              <strong>{{ route.origin }}</strong> ⇄ <strong>{{ route.destination }}</strong>
            </div>
            <div class="text-xs text-gray-600 dark:text-gray-400 leading-tight">
              {{ route.origin_name }} ⇄ {{ route.destination_name }}
            </div>
          </div>

          <div class="flex flex-col gap-1 pt-3 border-t border-gray-300 dark:border-gray-600">
            <div class="flex justify-between text-sm">
              <span class="text-gray-600 dark:text-gray-400">Outbound:</span>
              <span class="font-semibold text-gray-800 dark:text-gray-200">
                {{ route.outbound_flights || 0 }} flights
              </span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-gray-600 dark:text-gray-400">Return:</span>
              <span class="font-semibold text-gray-800 dark:text-gray-200">
                {{ route.return_flights || 0 }} flights
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  routes: Array,
  origin: String
})

defineEmits(['select'])

const isExpanded = ref(false)

const toggleExpanded = () => {
  isExpanded.value = !isExpanded.value
}
</script>
