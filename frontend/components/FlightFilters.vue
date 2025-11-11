<template>
  <div class="mt-8 p-6 bg-white dark:bg-gray-800 rounded-xl shadow-md">
    <h2 class="text-2xl font-semibold text-gray-800 dark:text-gray-100 border-b-2 border-gray-200 dark:border-gray-700 pb-2 mb-4">
      Search Flights
    </h2>

    <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-6">
      <!-- Row 1 -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
        <div class="flex flex-col">
          <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200">Origin</label>
          <select
            :value="filters.origin"
            @change="$emit('update:origin', $event.target.value)"
            class="px-3 py-2 border-2 border-gray-300 dark:border-gray-500 rounded-md bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 cursor-pointer focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 dark:focus:ring-blue-800"
          >
            <option value="">All origins</option>
            <option v-for="origin in origins" :key="origin.code" :value="origin.code">
              {{ origin.code }} - {{ origin.name }}
            </option>
          </select>
        </div>

        <div class="flex flex-col">
          <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200">Destination</label>
          <select
            :value="filters.destination"
            @change="$emit('update:destination', $event.target.value)"
            class="px-3 py-2 border-2 border-gray-300 dark:border-gray-500 rounded-md bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 cursor-pointer focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 dark:focus:ring-blue-800"
          >
            <option value="">All destinations</option>
            <option v-for="dest in destinations" :key="dest.code" :value="dest.code">
              {{ dest.code }} - {{ dest.name }}
            </option>
          </select>
        </div>

        <div class="flex flex-col">
          <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200">Date From</label>
          <input
            type="date"
            :value="filters.dateFrom"
            @change="$emit('update:dateFrom', $event.target.value)"
            class="px-3 py-2 border-2 border-gray-300 dark:border-gray-500 rounded-md bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 dark:focus:ring-blue-800"
          />
        </div>

        <div class="flex flex-col">
          <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200">Date To</label>
          <input
            type="date"
            :value="filters.dateTo"
            @change="$emit('update:dateTo', $event.target.value)"
            class="px-3 py-2 border-2 border-gray-300 dark:border-gray-500 rounded-md bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 dark:focus:ring-blue-800"
          />
        </div>
      </div>

      <!-- Row 2 -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div class="flex flex-col">
          <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200">Cena Min (PLN)</label>
          <input
            type="number"
            :value="filters.minPrice"
            @input="$emit('update:minPrice', parseFloat($event.target.value) || null)"
            min="0"
            placeholder="Min"
            class="px-3 py-2 border-2 border-gray-300 dark:border-gray-500 rounded-md bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 dark:focus:ring-blue-800"
          />
        </div>

        <div class="flex flex-col">
          <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200">Cena Maks (PLN)</label>
          <input
            type="number"
            :value="filters.maxPrice"
            @input="$emit('update:maxPrice', parseFloat($event.target.value) || null)"
            min="0"
            placeholder="Max"
            class="px-3 py-2 border-2 border-gray-300 dark:border-gray-500 rounded-md bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 dark:focus:ring-blue-800"
          />
        </div>

        <div class="flex flex-col">
          <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200">Sortuj Według</label>
          <select
            :value="filters.sortBy"
            @change="$emit('update:sortBy', $event.target.value)"
            class="px-3 py-2 border-2 border-gray-300 dark:border-gray-500 rounded-md bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 cursor-pointer focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 dark:focus:ring-blue-800"
          >
            <option value="price">Cena (Od Najniższej)</option>
            <option value="price_desc">Cena (Od Najwyższej)</option>
            <option value="date">Data (Najwcześniejsza)</option>
            <option value="duration">Czas Trwania</option>
          </select>
        </div>

        <div class="flex flex-col">
          <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200">Rozmiar Strony</label>
          <select
            :value="filters.pageSize"
            @change="$emit('update:pageSize', parseInt($event.target.value))"
            class="px-3 py-2 border-2 border-gray-300 dark:border-gray-500 rounded-md bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 cursor-pointer focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 dark:focus:ring-blue-800"
          >
            <option :value="25">25</option>
            <option :value="50">50</option>
            <option :value="100">100</option>
          </select>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex gap-4">
        <button
          @click="$emit('search')"
          :disabled="loading"
          class="px-6 py-3 bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-700 text-white font-medium rounded-md transition transform hover:-translate-y-0.5 hover:shadow-lg disabled:opacity-60 disabled:cursor-not-allowed disabled:transform-none"
        >
          Szukaj Lotów
        </button>
        <button
          @click="$emit('clear')"
          class="px-6 py-3 bg-gray-600 hover:bg-gray-700 dark:bg-gray-600 dark:hover:bg-gray-700 text-white font-medium rounded-md transition"
        >
          Wyczyść Filtry
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  filters: Object,
  origins: Array,
  destinations: Array,
  loading: Boolean
})

defineEmits(['update:origin', 'update:destination', 'update:dateFrom', 'update:dateTo', 'update:minPrice', 'update:maxPrice', 'update:sortBy', 'update:pageSize', 'search', 'clear'])
</script>
