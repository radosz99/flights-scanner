<template>
  <div class="mt-8 p-6 bg-white dark:bg-gray-800 rounded-xl shadow-md">
    <h2 class="text-2xl font-semibold text-gray-800 dark:text-gray-100 border-b-2 border-gray-200 dark:border-gray-700 pb-2 mb-4">
      Wybierz Trasę
    </h2>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
      <!-- Origin -->
      <div class="flex flex-col">
        <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200">Lotnisko Wylotu</label>
        <select
          :value="origin"
          @change="$emit('update:origin', $event.target.value)"
          class="px-3 py-2 border-2 border-gray-300 dark:border-gray-500 rounded-md bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 dark:focus:ring-blue-800 transition cursor-pointer"
        >
          <option value="">Wybierz lotnisko wylotu...</option>
          <option v-for="orig in origins" :key="orig.code" :value="orig.code">
            {{ orig.code }} - {{ orig.name }} ({{ orig.flight_count }} lotów)
          </option>
        </select>
      </div>

      <!-- Destination -->
      <div class="flex flex-col">
        <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200">Lotnisko Docelowe</label>
        <select
          :value="destination"
          @change="$emit('update:destination', $event.target.value)"
          :disabled="!origin || availableDestinations.length === 0"
          class="px-3 py-2 border-2 border-gray-300 dark:border-gray-500 rounded-md bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 dark:focus:ring-blue-800 transition cursor-pointer disabled:bg-gray-200 dark:disabled:bg-gray-700 disabled:text-gray-500 dark:disabled:text-gray-400 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <option value="">{{ origin ? 'Wybierz lotnisko docelowe...' : 'Najpierw wybierz lotnisko wylotu' }}</option>
          <option v-for="dest in availableDestinations" :key="dest.code" :value="dest.code">
            {{ dest.code }} - {{ dest.name }} ({{ dest.flight_count }} lotów)
          </option>
        </select>
      </div>
    </div>

    <!-- Action Buttons -->
    <div class="flex gap-4 mt-6">
      <button
        @click="$emit('load')"
        :disabled="!origin || !destination || loading"
        class="px-6 py-3 bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-700 text-white font-medium rounded-md transition transform hover:-translate-y-0.5 hover:shadow-lg disabled:opacity-60 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none"
      >
        {{ loading ? 'Ładowanie...' : 'Załaduj Wykres Cen' }}
      </button>
      <button
        @click="$emit('clear')"
        class="px-6 py-3 bg-gray-600 hover:bg-gray-700 dark:bg-gray-600 dark:hover:bg-gray-700 text-white font-medium rounded-md transition"
      >
        Wyczyść Wybór
      </button>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  origin: String,
  destination: String,
  origins: Array,
  availableDestinations: Array,
  loading: Boolean
})

defineEmits(['update:origin', 'update:destination', 'load', 'clear'])
</script>
