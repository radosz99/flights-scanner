<template>
  <div class="mt-8 p-6 bg-white dark:bg-gray-800 rounded-xl shadow-md">
    <h2 class="text-2xl font-semibold text-gray-800 dark:text-gray-100 border-b-2 border-gray-200 dark:border-gray-700 pb-2 mb-4">
      Search Parameters
    </h2>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-4">
      <!-- Origin -->
      <div class="flex flex-col">
        <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200">Departure Airport</label>
        <select
          :value="origin"
          @change="$emit('update:origin', $event.target.value)"
          class="px-3 py-2 border-2 border-gray-300 dark:border-gray-500 rounded-md bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 dark:focus:ring-blue-800 transition cursor-pointer"
        >
          <option value="">Select departure...</option>
          <option v-for="orig in origins" :key="orig.code" :value="orig.code">
            {{ orig.code }} - {{ orig.name }}
          </option>
        </select>
      </div>

      <!-- Destination -->
      <div class="flex flex-col">
        <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200">Destination Airport (optional)</label>
        <select
          :value="destination"
          @change="$emit('update:destination', $event.target.value)"
          :disabled="!origin || availableDestinations.length === 0"
          class="px-3 py-2 border-2 border-gray-300 dark:border-gray-500 rounded-md bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 dark:focus:ring-blue-800 transition cursor-pointer disabled:bg-gray-200 dark:disabled:bg-gray-700 disabled:text-gray-500 dark:disabled:text-gray-400 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <option value="">{{ origin ? 'All destinations' : 'Select departure first' }}</option>
          <option v-for="dest in availableDestinations" :key="dest.code" :value="dest.code">
            {{ dest.code }} - {{ dest.name }}
          </option>
        </select>
      </div>

      <!-- Min Days -->
      <div class="flex flex-col">
        <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200">Minimum Days</label>
        <input
          type="number"
          :value="minDays"
          @input="$emit('update:minDays', parseInt($event.target.value))"
          min="1"
          max="365"
          placeholder="e.g., 3"
          class="px-3 py-2 border-2 border-gray-300 dark:border-gray-500 rounded-md bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 dark:focus:ring-blue-800 transition"
        />
      </div>

      <!-- Max Days -->
      <div class="flex flex-col">
        <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200">Maximum Days</label>
        <input
          type="number"
          :value="maxDays"
          @input="$emit('update:maxDays', parseInt($event.target.value))"
          min="1"
          max="365"
          placeholder="e.g., 7"
          class="px-3 py-2 border-2 border-gray-300 dark:border-gray-500 rounded-md bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 dark:focus:ring-blue-800 transition"
        />
      </div>

      <!-- Max Results -->
      <div class="flex flex-col">
        <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200">Max Results</label>
        <input
          type="number"
          :value="limit"
          @input="$emit('update:limit', parseInt($event.target.value))"
          min="10"
          max="500"
          placeholder="e.g., 100"
          class="px-3 py-2 border-2 border-gray-300 dark:border-gray-500 rounded-md bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 dark:focus:ring-blue-800 transition"
        />
      </div>
    </div>

    <!-- Additional Filters Section -->
    <div class="mt-6 pt-6 border-t-2 border-gray-200 dark:border-gray-700">
      <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">Advanced Filters</h3>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <!-- Return from same airport checkbox -->
        <div class="flex flex-col">
          <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200">Return Flight</label>
          <div class="flex items-center h-10">
            <input
              type="checkbox"
              :checked="returnFromSameAirport"
              @change="$emit('update:returnFromSameAirport', $event.target.checked)"
              id="return-from-same-airport"
              class="w-4 h-4 text-blue-600 bg-white dark:bg-gray-600 border-gray-300 dark:border-gray-500 rounded focus:ring-blue-500 dark:focus:ring-blue-600 focus:ring-2 cursor-pointer"
            />
            <label
              for="return-from-same-airport"
              class="ml-2 text-sm text-gray-700 dark:text-gray-300 cursor-pointer"
            >
              Return from same airport
            </label>
          </div>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Uncheck to allow returns from different airports (e.g., fly to BCN, return from ALC)
          </p>
        </div>

        <!-- Outbound Weekdays -->
        <div class="flex flex-col">
          <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200">Outbound Flight Days</label>
          <MultiSelectDropdown
            :options="weekdayOptions"
            :selected-values="outboundWeekdays"
            @update:selected-values="$emit('update:outboundWeekdays', $event)"
            placeholder="Any day"
            :searchable="false"
            :show-selected-items="false"
          />
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Select specific days of the week for outbound flights
          </p>
        </div>

        <!-- Return Weekdays -->
        <div class="flex flex-col">
          <label class="font-semibold mb-2 text-gray-700 dark:text-gray-200">Return Flight Days</label>
          <MultiSelectDropdown
            :options="weekdayOptions"
            :selected-values="returnWeekdays"
            @update:selected-values="$emit('update:returnWeekdays', $event)"
            placeholder="Any day"
            :searchable="false"
            :show-selected-items="false"
          />
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Select specific days of the week for return flights
          </p>
        </div>
      </div>
    </div>

    <!-- Action Buttons -->
    <div class="flex gap-4 mt-6">
      <button
        @click="$emit('search')"
        :disabled="!canSearch"
        class="px-6 py-3 bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-700 text-white font-medium rounded-md transition transform hover:-translate-y-0.5 hover:shadow-lg disabled:opacity-60 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none disabled:bg-gray-400 dark:disabled:bg-gray-600"
      >
        Search Trips
      </button>
      <button
        @click="$emit('clear')"
        class="px-6 py-3 bg-gray-600 hover:bg-gray-700 dark:bg-gray-600 dark:hover:bg-gray-700 text-white font-medium rounded-md transition"
      >
        Clear
      </button>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  origin: String,
  destination: String,
  minDays: Number,
  maxDays: Number,
  limit: Number,
  origins: Array,
  availableDestinations: Array,
  canSearch: Boolean,
  returnFromSameAirport: Boolean,
  outboundWeekdays: Array,
  returnWeekdays: Array
})

defineEmits([
  'update:origin',
  'update:destination',
  'update:minDays',
  'update:maxDays',
  'update:limit',
  'update:returnFromSameAirport',
  'update:outboundWeekdays',
  'update:returnWeekdays',
  'search',
  'clear'
])

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
</script>
