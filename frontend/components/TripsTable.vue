<template>
  <div v-if="results && results.trips.length > 0" class="mt-8">
    <div class="mb-6 pb-4 border-b-2 border-gray-200 dark:border-gray-700">
      <h2 class="text-2xl font-semibold text-gray-800 dark:text-gray-100">
        Znaleziono {{ results.total_combinations }} Lotów w Obie Strony
      </h2>
      <p class="text-gray-600 dark:text-gray-400 mt-2">
        Pokazywanie {{ results.showing }} wyników dla
        <strong class="text-gray-900 dark:text-gray-200">
          {{ results.origin }} → {{ results.destination === 'ALL' ? 'Wszystkie Cele' : results.destination }}
        </strong>
        ({{ results.min_days }}-{{ results.max_days }} dni)
      </p>
    </div>

    <div class="overflow-x-auto bg-white dark:bg-gray-800 rounded-xl shadow-md">
      <table class="w-full border-collapse text-sm">
        <thead class="bg-gray-100 dark:bg-gray-700 border-b-2 border-gray-300 dark:border-gray-600">
          <tr>
            <th v-if="results.destination === 'ALL'" class="px-3 py-4 text-left font-semibold text-gray-700 dark:text-gray-200 whitespace-nowrap sticky top-0 bg-gray-100 dark:bg-gray-700 z-10">
              Cel Podróży
            </th>
            <th class="px-3 py-4 text-left font-semibold text-gray-700 dark:text-gray-200 whitespace-nowrap sticky top-0 bg-gray-100 dark:bg-gray-700 z-10">
              Czas Trwania
            </th>
            <th class="px-3 py-4 text-left font-semibold text-gray-700 dark:text-gray-200 whitespace-nowrap sticky top-0 bg-gray-100 dark:bg-gray-700 z-10">
              Lot Tam
            </th>
            <th class="px-3 py-4 text-left font-semibold text-gray-700 dark:text-gray-200 whitespace-nowrap sticky top-0 bg-gray-100 dark:bg-gray-700 z-10">
              Godziny Lotu Tam
            </th>
            <th class="px-3 py-4 text-left font-semibold text-gray-700 dark:text-gray-200 whitespace-nowrap sticky top-0 bg-gray-100 dark:bg-gray-700 z-10">
              Lot Powrotny
            </th>
            <th class="px-3 py-4 text-left font-semibold text-gray-700 dark:text-gray-200 whitespace-nowrap sticky top-0 bg-gray-100 dark:bg-gray-700 z-10">
              Godziny Lotu Powrotnego
            </th>
            <th class="px-3 py-4 text-left font-semibold text-gray-700 dark:text-gray-200 whitespace-nowrap sticky top-0 bg-gray-100 dark:bg-gray-700 z-10">
              Cena Całkowita
            </th>
          </tr>
        </thead>
        <tbody class="bg-white dark:bg-gray-800">
          <tr
            v-for="(trip, index) in results.trips"
            :key="index"
            class="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition"
          >
            <!-- Destination (conditional) -->
            <td v-if="results.destination === 'ALL'" class="px-3 py-3 bg-white dark:bg-gray-800">
              <div class="flex flex-col gap-1">
                <div class="font-semibold text-gray-900 dark:text-gray-100">
                  {{ trip.destination }}
                </div>
                <div class="text-xs text-gray-600 dark:text-gray-400">
                  {{ trip.destination_name }}
                </div>
              </div>
            </td>

            <!-- Duration -->
            <td class="px-3 py-3 whitespace-nowrap bg-white dark:bg-gray-800">
              <strong class="text-gray-900 dark:text-gray-100">{{ trip.trip_duration_days }} dni</strong>
            </td>

            <!-- Outbound Date -->
            <td class="px-3 py-3 min-w-[140px] bg-white dark:bg-gray-800">
              <div class="flex flex-col gap-1">
                <div class="font-medium text-gray-900 dark:text-gray-200">
                  {{ formatDateWithWeekday(trip.outbound_flight.date) }}
                </div>
                <div class="flex gap-2 text-xs text-gray-600 dark:text-gray-400">
                  <span>{{ trip.outbound_flight.flight_number }}</span>
                  <span>{{ trip.outbound_flight.duration }}</span>
                </div>
                <div v-if="trip.outbound_flight.last_seen" class="text-xs text-gray-500 dark:text-gray-400">
                  Zaktualizowano: {{ formatDateTime(trip.outbound_flight.last_seen) }}
                </div>
              </div>
            </td>

            <!-- Outbound Times -->
            <td class="px-3 py-3 min-w-[140px] bg-white dark:bg-gray-800">
              <div class="flex items-center gap-2 font-mono text-sm font-medium text-gray-900 dark:text-gray-200">
                <span class="whitespace-nowrap">{{ formatTime(trip.outbound_flight.departure_time) }}</span>
                <span class="text-blue-500 dark:text-blue-400 text-lg">→</span>
                <span class="whitespace-nowrap">{{ formatTime(trip.outbound_flight.arrival_time) }}</span>
              </div>
            </td>

            <!-- Return Date -->
            <td class="px-3 py-3 min-w-[140px] bg-white dark:bg-gray-800">
              <div class="flex flex-col gap-1">
                <div class="font-medium text-gray-900 dark:text-gray-200">
                  {{ formatDateWithWeekday(trip.return_flight.date) }}
                </div>
                <div class="flex gap-2 text-xs text-gray-600 dark:text-gray-400">
                  <span>{{ trip.return_flight.flight_number }}</span>
                  <span>{{ trip.return_flight.duration }}</span>
                </div>
                <div v-if="trip.return_flight.last_seen" class="text-xs text-gray-500 dark:text-gray-400">
                  Zaktualizowano: {{ formatDateTime(trip.return_flight.last_seen) }}
                </div>
              </div>
            </td>

            <!-- Return Times -->
            <td class="px-3 py-3 min-w-[140px] bg-white dark:bg-gray-800">
              <div class="flex items-center gap-2 font-mono text-sm font-medium text-gray-900 dark:text-gray-200">
                <span class="whitespace-nowrap">{{ formatTime(trip.return_flight.departure_time) }}</span>
                <span class="text-blue-500 dark:text-blue-400 text-lg">→</span>
                <span class="whitespace-nowrap">{{ formatTime(trip.return_flight.arrival_time) }}</span>
              </div>
            </td>

            <!-- Total Price -->
            <td class="px-3 py-3 text-right font-bold text-green-600 dark:text-green-400 min-w-[120px] bg-white dark:bg-gray-800">
              <div class="flex flex-col items-end gap-1">
                <div class="text-xl">{{ formatPrice(trip.total_price) }}</div>
                <div class="text-xs font-normal text-gray-600 dark:text-gray-400">
                  {{ formatPrice(trip.price_per_person) }} /p
                </div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { formatPrice, formatDate, formatTime, formatDateTime, formatDateWithWeekday } from '~/utils/formatters'

const props = defineProps({
  results: Object
})
</script>
