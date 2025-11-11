<template>
  <div class="max-w-full mx-auto p-8 min-h-screen dark:bg-gray-900">
    <h1 class="text-gray-800 dark:text-gray-100 text-4xl font-bold mb-4">Custom Trip Search</h1>
    <p class="text-gray-600 dark:text-gray-300 text-lg mb-8">
      Search for one-way or round-trip flights with flexible origin and destination matching. Use batch search to efficiently find flights across multiple airports.
    </p>

    <!-- Error -->
    <div
      v-if="error"
      class="mt-8 p-4 bg-red-50 dark:bg-red-900 text-red-800 dark:text-red-200 rounded-md border border-red-200 dark:border-red-700"
    >
      <strong>Error:</strong> {{ error }}
    </div>

    <!-- Main Content: Filters + Results Side by Side on Desktop -->
    <div class="flex flex-col lg:flex-row lg:items-start gap-6 mt-8">
      <!-- Search Form (Left Side on Desktop) -->
      <div class="lg:w-[30%] lg:sticky lg:top-8">
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md flex flex-col max-h-[calc(100vh-6rem)]">
          <!-- Header and Buttons (Sticky) -->
          <div class="p-6 pb-4 sticky top-0 bg-white dark:bg-gray-800 z-10 rounded-t-lg">
            <!-- Action Buttons -->
            <div class="flex gap-2 pb-4 border-b border-gray-200 dark:border-gray-700">
              <button
                @click="searchTrips"
                :disabled="!canSearch || loading"
                class="flex-1 py-2 px-4 bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-700 text-white font-medium rounded-md transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed hover:shadow-lg hover:-translate-y-0.5 text-sm"
              >
                Search Trips
              </button>
              <button
                @click="clearFilters"
                class="flex-1 py-2 px-4 bg-gray-600 hover:bg-gray-700 dark:bg-gray-600 dark:hover:bg-gray-700 text-white font-medium rounded-md transition-all duration-200 text-sm"
              >
                Clear All
              </button>
            </div>
          </div>

          <!-- Scrollable Filters -->
          <div class="overflow-y-auto px-6 pb-6">
            <div class="flex flex-col gap-4 pt-4">
            <!-- Origin Airports (Multi-select) - Polish airports only -->
            <div class="flex flex-col">
              <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200 text-sm">Origin Airports</label>
              <MultiSelectDropdown
                :options="polishAirportsOptions"
                :selected-values="searchParams.origins"
                @update:selected-values="searchParams.origins = $event"
                placeholder="Select Polish airports..."
                search-placeholder="Search airports..."
              />
            </div>

            <!-- Destination Selection Mode -->
            <div class="flex flex-col">
              <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200 text-sm">Destination Mode</label>
              <div class="inline-flex rounded-md shadow-sm" role="group">
                <button
                  type="button"
                  @click="destinationMode = 'airports'"
                  :class="[
                    'flex-1 px-4 py-2.5 text-sm font-medium border-2 rounded-l-md transition-all duration-200',
                    destinationMode === 'airports'
                      ? 'bg-blue-600 text-white border-blue-600 dark:bg-blue-600 dark:border-blue-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600 dark:hover:bg-gray-600'
                  ]"
                >
                  Airports
                </button>
                <button
                  type="button"
                  @click="destinationMode = 'country'"
                  :class="[
                    'flex-1 px-4 py-2.5 text-sm font-medium border-2 border-l-0 rounded-r-md transition-all duration-200',
                    destinationMode === 'country'
                      ? 'bg-blue-600 text-white border-blue-600 dark:bg-blue-600 dark:border-blue-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600 dark:hover:bg-gray-600'
                  ]"
                >
                  Countries
                </button>
              </div>
            </div>

            <!-- Destination Airports (Multi-select) -->
            <div v-if="destinationMode === 'airports'" class="flex flex-col">
              <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200 text-sm">Destination Airports</label>
              <MultiSelectDropdown
                :options="allAirportsOptions"
                :selected-values="searchParams.destinations"
                @update:selected-values="searchParams.destinations = $event"
                placeholder="Select destination airports..."
                search-placeholder="Search airports..."
              />
            </div>

            <!-- Destination Countries (Multi-select) -->
            <div v-if="destinationMode === 'country'" class="flex flex-col">
              <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200 text-sm">Destination Countries</label>
              <MultiSelectDropdown
                :options="countriesOptions"
                :selected-values="selectedCountries"
                @update:selected-values="selectAirportsByCountries"
                placeholder="Select countries..."
                search-placeholder="Search countries..."
              />
              <p v-if="selectedCountries.length > 0" class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                {{ getTotalAirportsFromCountries() }} airports from {{ selectedCountries.length }} {{ selectedCountries.length === 1 ? 'country' : 'countries' }}
              </p>
            </div>

            <!-- Two-Way Routes Checkbox -->
            <div class="flex items-center justify-center">
              <label class="flex items-center gap-2 cursor-pointer font-semibold text-gray-700 dark:text-gray-200 text-sm">
                <input
                  v-model="searchParams.twoWayRoutes"
                  type="checkbox"
                  class="w-5 h-5 cursor-pointer"
                />
                <span>Two-way routes (flexible matching)</span>
                <span class="inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/30 rounded-full cursor-help transition-all hover:bg-blue-100 dark:hover:bg-blue-900/50 hover:scale-110"
                      title="When checked, return flight can be to any selected origin airport">ℹ</span>
              </label>
            </div>

            <!-- Return from Same Airport Checkbox (only for two-way routes) -->
            <div v-if="searchParams.twoWayRoutes" class="flex items-center justify-center">
              <label class="flex items-center gap-2 cursor-pointer font-semibold text-gray-700 dark:text-gray-200 text-sm">
                <input
                  v-model="searchParams.returnFromSameAirport"
                  type="checkbox"
                  class="w-5 h-5 cursor-pointer"
                />
                <span>Return from same airport</span>
                <span class="inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/30 rounded-full cursor-help transition-all hover:bg-blue-100 dark:hover:bg-blue-900/50 hover:scale-110"
                      title="Uncheck to allow returns from different airports (e.g., fly to BCN, return from VLC)">ℹ</span>
              </label>
            </div>

            <!-- Return to Same Airport Checkbox (only for two-way routes) -->
            <div v-if="searchParams.twoWayRoutes" class="flex items-center justify-center">
              <label class="flex items-center gap-2 cursor-pointer font-semibold text-gray-700 dark:text-gray-200 text-sm">
                <input
                  v-model="searchParams.returnToSameAirport"
                  type="checkbox"
                  class="w-5 h-5 cursor-pointer"
                />
                <span>Return to same airport</span>
                <span class="inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/30 rounded-full cursor-help transition-all hover:bg-blue-100 dark:hover:bg-blue-900/50 hover:scale-110"
                      title="Uncheck to allow returns to different origin airports (e.g., fly from WRO, return to KRK)">ℹ</span>
              </label>
            </div>

            <!-- Date Range (From and To on same line) -->
            <div class="flex gap-2">
              <div class="flex flex-col flex-1">
                <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200 text-sm">From</label>
                <input
                  v-model="searchParams.dateFrom"
                  type="date"
                  class="p-2 border-2 border-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600 rounded-md text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                />
              </div>
              <div class="flex flex-col flex-1">
                <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200 text-sm">To</label>
                <input
                  v-model="searchParams.dateTo"
                  type="date"
                  class="p-2 border-2 border-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600 rounded-md text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                />
              </div>
            </div>

            <!-- Min/Max Days (on same line, only for two-way routes) -->
            <div v-if="searchParams.twoWayRoutes" class="flex gap-2">
              <div class="flex flex-col flex-1">
                <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200 text-sm">Min Days</label>
                <input
                  v-model.number="searchParams.minDays"
                  type="number"
                  min="1"
                  max="365"
                  class="p-2 border-2 border-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600 rounded-md text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                />
              </div>
              <div class="flex flex-col flex-1">
                <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200 text-sm">Max Days</label>
                <input
                  v-model.number="searchParams.maxDays"
                  type="number"
                  min="1"
                  max="365"
                  class="p-2 border-2 border-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600 rounded-md text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                />
              </div>
            </div>

            <!-- Outbound and Return Weekdays (on same line for two-way, single for one-way) -->
            <div v-if="searchParams.twoWayRoutes" class="flex gap-2">
              <div class="flex flex-col flex-1">
                <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200 text-sm flex items-center gap-1">
                  Outbound Days
                  <span class="inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/30 rounded-full cursor-help transition-all hover:bg-blue-100 dark:hover:bg-blue-900/50 hover:scale-110"
                        title="Select specific days of the week for outbound flights">ℹ</span>
                </label>
                <MultiSelectDropdown
                  :options="weekdayOptions"
                  :selected-values="searchParams.outboundWeekdays"
                  @update:selected-values="searchParams.outboundWeekdays = $event"
                  placeholder="Any day"
                  :searchable="false"
                  :show-selected-items="false"
                />
              </div>
              <div class="flex flex-col flex-1">
                <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200 text-sm flex items-center gap-1">
                  Return Days
                  <span class="inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/30 rounded-full cursor-help transition-all hover:bg-blue-100 dark:hover:bg-blue-900/50 hover:scale-110"
                        title="Select specific days of the week for return flights">ℹ</span>
                </label>
                <MultiSelectDropdown
                  :options="weekdayOptions"
                  :selected-values="searchParams.returnWeekdays"
                  @update:selected-values="searchParams.returnWeekdays = $event"
                  placeholder="Any day"
                  :searchable="false"
                  :show-selected-items="false"
                />
              </div>
            </div>

            <!-- One-way Flight Days (single column) -->
            <div v-if="!searchParams.twoWayRoutes" class="flex flex-col">
              <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200 text-sm flex items-center gap-1">
                Flight Days
                <span class="inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/30 rounded-full cursor-help transition-all hover:bg-blue-100 dark:hover:bg-blue-900/50 hover:scale-110"
                      title="Select specific days of the week for flights">ℹ</span>
              </label>
              <MultiSelectDropdown
                :options="weekdayOptions"
                :selected-values="searchParams.outboundWeekdays"
                @update:selected-values="searchParams.outboundWeekdays = $event"
                placeholder="Any day"
                :searchable="false"
                :show-selected-items="false"
              />
            </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Results Section (Right Side on Desktop) -->
      <div class="lg:flex-1 lg:min-w-0 relative">
        <!-- Loading Overlay -->
        <div v-if="loading" class="absolute inset-0 flex items-start justify-center pt-8 z-10">
          <div class="w-full max-w-[70%] p-4 bg-yellow-50 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 rounded-md border border-yellow-200 dark:border-yellow-700 text-center text-lg shadow-lg">
            <div class="mb-3">{{ loadingMessage }}</div>
            <div class="w-full bg-yellow-200 dark:bg-yellow-700 rounded-full h-2.5 overflow-hidden">
              <div class="bg-yellow-600 dark:bg-yellow-400 h-2.5 rounded-full animate-progress"></div>
            </div>
          </div>
        </div>

        <!-- Results Content (blurred when loading) -->
        <div :class="{ 'blur-sm opacity-60 pointer-events-none': loading && results }">
          <!-- Initial State Message -->
          <div v-if="!searched" class="p-8 bg-blue-50 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 rounded-lg border-2 border-blue-200 dark:border-blue-700 text-center">
            <div class="text-2xl mb-3">🔍</div>
            <h3 class="text-xl font-semibold mb-2">Ready to Search</h3>
            <p class="text-base">Please select your origin, destination, and other filters, then click "Search Trips" to find available flights.</p>
          </div>

        <!-- Results Table -->
        <div v-if="results && results.trips.length > 0" class="mt-4">
          <div class="overflow-x-auto bg-white dark:bg-gray-800 rounded-lg shadow-md w-full">
            <table class="w-full border-collapse text-sm">
              <thead class="bg-gray-50 dark:bg-gray-700 border-b-2 border-gray-200 dark:border-gray-600">
                <tr>
                  <th class="p-3 text-left font-semibold text-gray-700 dark:text-gray-200 whitespace-nowrap">
                    Destination
                  </th>
                  <th class="p-3 text-center font-semibold text-gray-700 dark:text-gray-200 whitespace-nowrap">
                    Date Range
                  </th>
                  <th class="p-3 text-left font-semibold text-gray-700 dark:text-gray-200 whitespace-nowrap">
                    Flight Info
                  </th>
                  <th class="p-3 text-center font-semibold text-gray-700 dark:text-gray-200 whitespace-nowrap">
                    Total Price
                  </th>
                  <th v-if="searchParams.twoWayRoutes" class="p-3 text-center font-semibold text-gray-700 dark:text-gray-200 whitespace-nowrap">
                    Duration
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white dark:bg-gray-800">
                <template v-for="(trip, index) in paginatedTrips" :key="index">
                  <!-- Outbound / One-way Flight Row -->
                  <tr class="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                    <td :rowspan="searchParams.twoWayRoutes && trip.return ? 2 : 1" class="p-3 text-center align-middle font-bold text-gray-800 dark:text-gray-200 border-r-2 border-gray-300 dark:border-gray-600">
                      <div class="text-lg">{{ trip.outbound.destination }}</div>
                      <div class="text-xs font-normal text-gray-600 dark:text-gray-400">{{ trip.outbound.destination_name }}</div>
                    </td>
                    <td :rowspan="searchParams.twoWayRoutes && trip.return ? 2 : 1" class="p-3 text-center align-middle text-gray-800 dark:text-gray-200">
                      <div class="text-sm font-semibold">{{ formatDateRange(trip) }}</div>
                    </td>
                    <td class="p-3 text-gray-800 dark:text-gray-200">
                      <div class="flex flex-col gap-1">
                        <div class="flex items-center gap-2">
                          <a
                            :href="buildRyanairUrl(trip.outbound)"
                            target="_blank"
                            rel="noopener noreferrer"
                            class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors"
                            title="Book on Ryanair"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                          </a>
                          <span class="text-sm font-bold">
                            {{ trip.outbound.origin }} → {{ trip.outbound.destination }}
                          </span>
                          <span class="text-xs text-gray-500 dark:text-gray-400">
                            {{ formatDate(trip.outbound.date_out) }}
                          </span>
                        </div>
                        <div class="text-xs text-gray-600 dark:text-gray-400 ml-7">
                          {{ trip.outbound.origin_name }} → {{ trip.outbound.destination_name }}
                        </div>
                        <div class="flex items-center gap-3 ml-7 text-xs">
                          <span class="text-gray-700 dark:text-gray-300">
                            {{ formatTime(trip.outbound.departure_time) }} - {{ formatTime(trip.outbound.arrival_time) }}
                          </span>
                          <span class="text-gray-500 dark:text-gray-400">
                            {{ trip.outbound.duration }}
                          </span>
                          <span class="text-green-600 dark:text-green-400 font-semibold">
                            {{ formatPrice(searchParams.twoWayRoutes ? trip.outbound.current_price : trip.outbound.price_per_person) }}
                          </span>
                        </div>
                      </div>
                    </td>
                    <td :rowspan="searchParams.twoWayRoutes && trip.return ? 2 : 1" class="p-3 text-center align-middle border-l border-gray-200 dark:border-gray-700">
                      <strong class="text-lg text-green-600 dark:text-green-400">{{ formatPrice(trip.total_price) }}</strong>
                    </td>
                    <td v-if="searchParams.twoWayRoutes" :rowspan="trip.return ? 2 : 1" class="p-3 text-center align-middle border-l border-gray-200 dark:border-gray-700">
                      <div class="flex flex-col gap-1">
                        <div class="text-base font-bold text-gray-800 dark:text-gray-200">{{ trip.trip_duration_days }} days</div>
                        <div class="text-xs text-gray-600 dark:text-gray-400">{{ trip.stay_duration }}</div>
                      </div>
                    </td>
                  </tr>

                  <!-- Return Flight Row (only for two-way routes) -->
                  <tr v-if="searchParams.twoWayRoutes && trip.return" class="border-b-4 border-gray-400 dark:border-gray-500 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                    <td class="p-3 text-gray-800 dark:text-gray-200">
                      <div class="flex flex-col gap-1">
                        <div class="flex items-center gap-2">
                          <a
                            :href="buildRyanairUrl(trip.return)"
                            target="_blank"
                            rel="noopener noreferrer"
                            class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors"
                            title="Book on Ryanair"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                          </a>
                          <span class="text-sm font-bold">
                            {{ trip.return.origin }} → {{ trip.return.destination }}
                          </span>
                          <span class="text-xs text-gray-500 dark:text-gray-400">
                            {{ formatDate(trip.return.date_out) }}
                          </span>
                        </div>
                        <div class="text-xs text-gray-600 dark:text-gray-400 ml-7">
                          {{ trip.return.origin_name }} → {{ trip.return.destination_name }}
                        </div>
                        <div class="flex items-center gap-3 ml-7 text-xs">
                          <span class="text-gray-700 dark:text-gray-300">
                            {{ formatTime(trip.return.departure_time) }} - {{ formatTime(trip.return.arrival_time) }}
                          </span>
                          <span class="text-gray-500 dark:text-gray-400">
                            {{ trip.return.duration }}
                          </span>
                          <span class="text-green-600 dark:text-green-400 font-semibold">
                            {{ formatPrice(trip.return.current_price) }}
                          </span>
                        </div>
                      </div>
                    </td>
                  </tr>

                  <!-- One-way flight wider separation -->
                  <tr v-if="!searchParams.twoWayRoutes" class="h-3 bg-gray-100 dark:bg-gray-900">
                    <td colspan="4" class="p-0"></td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>

          <!-- Pagination -->
          <div v-if="totalPages > 1" class="flex items-center justify-center gap-2 mt-6">
            <button
              @click="currentPage = 1"
              :disabled="currentPage === 1"
              class="px-3 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
            >
              ««
            </button>
            <button
              @click="currentPage--"
              :disabled="currentPage === 1"
              class="px-3 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
            >
              «
            </button>
            <span class="px-4 py-2 text-gray-700 dark:text-gray-200">
              Page {{ currentPage }} of {{ totalPages }}
            </span>
            <button
              @click="currentPage++"
              :disabled="currentPage === totalPages"
              class="px-3 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
            >
              »
            </button>
            <button
              @click="currentPage = totalPages"
              :disabled="currentPage === totalPages"
              class="px-3 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
            >
              »»
            </button>
          </div>
        </div>

          <!-- No Results -->
          <div
            v-if="!loading && searched && (!results || results.trips.length === 0)"
            class="p-8 text-center bg-gray-50 dark:bg-gray-700 rounded-lg text-gray-600 dark:text-gray-300 text-lg"
          >
            <p>No trips found matching your criteria. Try adjusting your search parameters.</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Scroll to Top Button -->
    <button
      v-if="showScrollTop"
      @click="scrollToTop"
      class="fixed bottom-8 right-8 p-4 bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-700 text-white rounded-full shadow-lg transition-all duration-300 hover:scale-110 z-50"
      title="Scroll to top"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18" />
      </svg>
    </button>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { formatPrice, formatDate, formatTime } from '~/utils/formatters'
import MultiSelectDropdown from '~/components/MultiSelectDropdown.vue'

const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl

// Scroll to top state
const showScrollTop = ref(false)

// List of Polish airport codes
const POLISH_AIRPORT_CODES = [
  'BZG', // Bydgoszcz
  'GDN', // Gdańsk
  'KRK', // Krakow
  'KTW', // Katowice
  'LCJ', // Lodz
  'LUZ', // Lublin
  'POZ', // Poznań
  'RZE', // Rzeszów
  'SZY', // Olsztyn-Mazury
  'SZZ', // Szczecin
  'WAW', // Warsaw (Chopin)
  'WMI', // Warsaw (Modlin)
  'WRO'  // Wroclaw
]

// State
const loading = ref(false)
const loadingMessage = ref('Loading...')
const error = ref(null)
const searched = ref(false)

const allAirports = ref([])
const destinationMode = ref('airports')
const selectedCountries = ref([])
const countriesData = ref([])

// Pagination
const currentPage = ref(1)
const itemsPerPage = 50

// Get today's date in YYYY-MM-DD format
const getTodayDate = () => {
  const today = new Date()
  return today.toISOString().split('T')[0]
}

// Search Parameters
const searchParams = ref({
  origins: [],
  destinations: [],
  twoWayRoutes: true,
  returnFromSameAirport: true,
  returnToSameAirport: true,
  dateFrom: getTodayDate(),
  dateTo: '',
  minDays: 3,
  maxDays: 7,
  outboundWeekdays: [],
  returnWeekdays: []
})

const results = ref(null)

// Computed
const canSearch = computed(() => {
  const hasOrigins = searchParams.value.origins.length > 0
  const hasDestinations = searchParams.value.destinations.length > 0

  // For two-way routes, validate trip duration
  if (searchParams.value.twoWayRoutes) {
    const validDuration = searchParams.value.minDays > 0 &&
                          searchParams.value.maxDays > 0 &&
                          searchParams.value.minDays <= searchParams.value.maxDays
    return hasOrigins && hasDestinations && validDuration
  }

  // For one-way routes, just need origins and destinations
  return hasOrigins && hasDestinations
})

// Pagination computed properties
const totalPages = computed(() => {
  if (!results.value || !results.value.trips) return 0
  return Math.ceil(results.value.trips.length / itemsPerPage)
})

const pageStart = computed(() => {
  return (currentPage.value - 1) * itemsPerPage
})

const pageEnd = computed(() => {
  const end = currentPage.value * itemsPerPage
  return Math.min(end, results.value?.trips.length || 0)
})

const paginatedTrips = computed(() => {
  if (!results.value || !results.value.trips) return []
  return results.value.trips.slice(pageStart.value, pageEnd.value)
})

// Options formatted for MultiSelectDropdown component (countries)
const countriesOptions = computed(() => {
  return countriesData.value.map(countryData => ({
    value: countryData.country,
    label: `${countryData.country} (${countryData.airport_count} airports)`
  }))
})

// Computed property for Polish airports only (for origin selection)
const polishAirports = computed(() => {
  return allAirports.value.filter(airport => {
    return POLISH_AIRPORT_CODES.includes(airport.code)
  }).sort((a, b) => a.code.localeCompare(b.code))
})

// Options formatted for MultiSelectDropdown component
const polishAirportsOptions = computed(() => {
  return polishAirports.value.map(airport => ({
    value: airport.code,
    label: `${airport.code} - ${airport.name}`
  }))
})

const allAirportsOptions = computed(() => {
  return allAirports.value.map(airport => ({
    value: airport.code,
    label: `${airport.code} - ${airport.name}`
  }))
})

// Weekday options (0=Monday, 6=Sunday)
const weekdayOptions = [
  { value: 0, label: 'Monday' },
  { value: 1, label: 'Tuesday' },
  { value: 2, label: 'Wednesday' },
  { value: 3, label: 'Thursday' },
  { value: 4, label: 'Friday' },
  { value: 5, label: 'Saturday' },
  { value: 6, label: 'Sunday' }
]

// Methods
const selectAirportsByCountries = (countries) => {
  selectedCountries.value = countries

  if (countries.length === 0) {
    searchParams.value.destinations = []
    return
  }

  // Find all airports from selected countries
  const airportCodes = []
  countries.forEach(country => {
    const countryData = countriesData.value.find(c => c.country === country)
    if (countryData && countryData.airports) {
      airportCodes.push(...countryData.airports.map(a => a.code))
    }
  })

  searchParams.value.destinations = airportCodes
}

const getTotalAirportsFromCountries = () => {
  let total = 0
  selectedCountries.value.forEach(country => {
    const countryData = countriesData.value.find(c => c.country === country)
    if (countryData) {
      total += countryData.airport_count
    }
  })
  return total
}

const loadAirports = async () => {
  loading.value = true
  loadingMessage.value = 'Loading airports...'
  error.value = null

  try {
    // Load all airports (both origins and destinations) and countries
    const [originsResponse, destinationsResponse, countriesResponse] = await Promise.all([
      $fetch(`${apiBaseUrl}/airports/origins`),
      $fetch(`${apiBaseUrl}/airports/destinations`),
      $fetch(`${apiBaseUrl}/airports/countries?airline=ryanair`)
    ])

    // Combine and deduplicate airports
    const airportsMap = new Map()

    ;[...(originsResponse.origins || []), ...(destinationsResponse.destinations || [])].forEach(airport => {
      if (!airportsMap.has(airport.code)) {
        airportsMap.set(airport.code, airport)
      }
    })

    allAirports.value = Array.from(airportsMap.values()).sort((a, b) =>
      a.code.localeCompare(b.code)
    )

    // Store countries data
    countriesData.value = countriesResponse.countries || []
  } catch (e) {
    error.value = e.message || 'Failed to load airports'
  } finally {
    loading.value = false
  }
}

const searchTrips = async () => {
  if (!canSearch.value) {
    error.value = 'Please select origin(s), destination(s), and specify trip duration'
    return
  }

  loading.value = true
  loadingMessage.value = 'Searching for trips...'
  error.value = null
  results.value = null
  searched.value = true
  currentPage.value = 1 // Reset to first page on new search

  try {
    if (searchParams.value.twoWayRoutes) {
      // Two-way routes with flexible matching
      await searchTwoWayTrips()
    } else {
      // One-way routes
      await searchOneWayTrips()
    }
  } catch (e) {
    error.value = e.statusCode === 404
      ? 'No trips found for the selected criteria'
      : e.message || 'Failed to search trips'
    results.value = null
  } finally {
    loading.value = false
  }
}

const searchTwoWayTrips = async () => {
  // Use the efficient batch endpoint that handles multiple origins and destinations
  // in a single request with flexible two-way matching

  try {
    const params = {
      origins: searchParams.value.origins.join(','),
      destinations: searchParams.value.destinations.join(','),
      min_days: searchParams.value.minDays,
      max_days: searchParams.value.maxDays,
      passengers: 1, // Default to 1 passenger for price display
      limit: 1000, // Backend maximum limit
      return_from_same_airport: searchParams.value.returnFromSameAirport,
      return_to_same_airport: searchParams.value.returnToSameAirport
    }

    // Add optional filters
    if (searchParams.value.dateFrom) params.date_from = searchParams.value.dateFrom
    if (searchParams.value.dateTo) params.date_to = searchParams.value.dateTo

    // Add weekday filters if they are selected
    if (searchParams.value.outboundWeekdays.length > 0) {
      params.outbound_weekdays = searchParams.value.outboundWeekdays.join(',')
    }
    if (searchParams.value.returnWeekdays.length > 0) {
      params.return_weekdays = searchParams.value.returnWeekdays.join(',')
    }

    const response = await $fetch(`${apiBaseUrl}/flights/round-trips-batch`, { params })

    results.value = {
      total: response.total,
      trips: response.trips
    }
  } catch (e) {
    console.error('Failed to search trips:', e)
    throw e
  }
}

const searchOneWayTrips = async () => {
  // Use the efficient batch endpoint for one-way flights
  try {
    const params = {
      origins: searchParams.value.origins.join(','),
      destinations: searchParams.value.destinations.join(','),
      passengers: 1, // Default to 1 passenger for price display
      limit: 1000 // Backend maximum limit
    }

    // Add optional filters
    if (searchParams.value.dateFrom) params.date_from = searchParams.value.dateFrom
    if (searchParams.value.dateTo) params.date_to = searchParams.value.dateTo

    // Add weekday filter if selected
    if (searchParams.value.outboundWeekdays.length > 0) {
      params.outbound_weekdays = searchParams.value.outboundWeekdays.join(',')
    }

    const response = await $fetch(`${apiBaseUrl}/flights/one-way-batch`, { params })

    results.value = {
      total: response.total,
      trips: response.flights.map(flight => ({
        outbound: flight,
        return: null,
        trip_duration_days: null,
        stay_duration: null,
        total_price: flight.total_price
      }))
    }
  } catch (e) {
    console.error('Failed to search one-way trips:', e)
    throw e
  }
}

const clearFilters = () => {
  searchParams.value = {
    origins: [],
    destinations: [],
    twoWayRoutes: true,
    returnFromSameAirport: true,
    returnToSameAirport: true,
    dateFrom: getTodayDate(),
    dateTo: '',
    minDays: 3,
    maxDays: 7,
    outboundWeekdays: [],
    returnWeekdays: []
  }
  destinationMode.value = 'airports'
  selectedCountries.value = []
  results.value = null
  error.value = null
  searched.value = false
  currentPage.value = 1
}

// Scroll to top functionality
const handleScroll = () => {
  showScrollTop.value = window.scrollY > 300
}

const scrollToTop = () => {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  })
}

const formatDateRange = (trip) => {
  const formatDate = (dateStr) => {
    const date = new Date(dateStr)
    const day = String(date.getDate()).padStart(2, '0')
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const year = date.getFullYear()
    return `${day}.${month}.${year}`
  }

  const outboundDate = formatDate(trip.outbound.date_out)

  if (searchParams.value.twoWayRoutes && trip.return) {
    const returnDate = formatDate(trip.return.date_out)
    return `${outboundDate}-${returnDate}`
  }

  return outboundDate
}

const buildRyanairUrl = (flight) => {
  const dateOnly = flight.date_out.split('T')[0]

  const params = new URLSearchParams({
    adults: '1',
    teens: '0',
    children: '0',
    infants: '0',
    dateOut: dateOnly,
    dateIn: '',
    isConnectedFlight: 'false',
    discount: '0',
    promoCode: '',
    isReturn: 'false',
    originIata: flight.origin,
    destinationIata: flight.destination,
    tpAdults: '1',
    tpTeens: '0',
    tpChildren: '0',
    tpInfants: '0',
    tpStartDate: dateOnly,
    tpEndDate: '',
    tpDiscount: '0',
    tpPromoCode: '',
    tpOriginIata: flight.origin,
    tpDestinationIata: flight.destination
  })

  return `https://www.ryanair.com/hr/en/trip/flights/select?${params.toString()}`
}

// Lifecycle
onMounted(async () => {
  await loadAirports()
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
/* Only animation keyframes needed for progress bar */
@keyframes progress {
  0% {
    width: 0%;
  }
  50% {
    width: 70%;
  }
  100% {
    width: 100%;
  }
}

.animate-progress {
  animation: progress 2s ease-in-out infinite;
}
</style>
