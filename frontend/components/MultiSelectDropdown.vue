<template>
  <div class="relative" ref="dropdownRef">
    <button
      @click="openDropdown"
      class="w-full p-3 text-xs sm:text-sm border border-gray-300 rounded-lg bg-white
             hover:bg-gray-50 transition-all duration-200 flex justify-between items-center shadow-sm
             text-gray-900 font-medium dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100 dark:hover:bg-gray-600"
      style="letter-spacing: 0.03em"
    >
      <div class="flex items-center flex-1 min-w-0">
        <span class="truncate">
          {{ displayText }}
        </span>
      </div>
      <div class="flex items-center ml-2">
        <button
          v-if="selectedValues.length > 0"
          @click="clearSelection"
          class="mr-2 p-0.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors dark:hover:bg-red-900"
        >
          <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
        <svg
          class="w-4 h-4 text-gray-400 transition-transform"
          :class="{ 'rotate-180': isDropdownOpen }"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
        </svg>
      </div>
    </button>

    <div
      v-if="isDropdownOpen"
      class="absolute mt-1 w-full bg-white shadow-xl rounded-lg border border-gray-200 overflow-hidden z-50 dark:bg-gray-800 dark:border-gray-600"
      style="max-height: 20rem;"
    >
      <!-- Search Input -->
      <div class="p-3" v-if="searchable">
        <div class="relative">
          <input
            ref="searchInputRef"
            v-model="searchQuery"
            type="text"
            :placeholder="searchPlaceholder"
            class="w-full pl-8 pr-3 py-2 text-sm border border-gray-300 rounded-md bg-gray-50 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-orange-500 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100 dark:placeholder-gray-400"
            @click.stop
          />
          <svg class="absolute left-2.5 top-2.5 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
          </svg>
        </div>
      </div>

      <!-- Select All / Clear All -->
      <div class="px-3 py-2 border-b border-gray-100 bg-gray-50 dark:bg-gray-700 dark:border-gray-600">
        <div class="flex justify-between items-center">
          <button
            @click="selectAll"
            class="text-xs text-orange-600 hover:text-orange-700 font-medium dark:text-orange-400 dark:hover:text-orange-300"
          >
            Zaznacz wszystko
          </button>
          <button
            @click="clearSelection"
            class="text-xs text-gray-500 hover:text-gray-700 font-medium dark:text-gray-400 dark:hover:text-gray-300"
          >
            Wyczyść wszystko
          </button>
        </div>
      </div>

      <!-- Dropdown Options -->
      <div class="overflow-y-auto" style="max-height: 12rem; padding-bottom: 4px;">
        <div v-if="filteredOptions.length > 0">
          <div
            v-for="option in filteredOptions"
            :key="option.value"
            @click="toggleOption(option.value)"
            class="flex items-center px-3 py-2 hover:bg-gray-100 cursor-pointer transition-colors dark:hover:bg-gray-700"
          >
            <div class="flex items-center w-full">
              <div class="relative flex items-center">
                <input
                  type="checkbox"
                  :checked="isSelected(option.value)"
                  class="h-4 w-4 text-orange-600 focus:ring-orange-500 border-gray-300 rounded"
                  @click.stop="toggleOption(option.value)"
                />
              </div>

              <!-- Image support -->
              <div class="flex items-center ml-3 flex-1 min-w-0">
                <img
                  v-if="option.flag || option.image"
                  :src="option.flag || option.image"
                  :alt="`${option.label} ${imageAltSuffix}`"
                  class="w-4 h-3 mr-2 object-cover rounded-sm flex-shrink-0"
                  @error="handleImageError"
                />
                <span class="text-xs sm:text-sm text-gray-700 truncate font-medium dark:text-gray-200" style="letter-spacing: 0.03em">
                  {{ option.label }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- No Results -->
        <div v-else-if="searchQuery" class="px-3 py-4 text-center">
          <p class="text-sm text-gray-500 dark:text-gray-400">Nie znaleziono opcji</p>
        </div>
      </div>
    </div>

    <!-- Selected Items Display with horizontal scroll -->
    <div v-if="selectedValues.length > 0 && showSelectedItems" class="mt-2">
      <div class="flex gap-1 overflow-x-auto pb-1 scrollbar-thin">
        <span
          v-for="value in selectedValues"
          :key="value"
          class="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-orange-100 text-orange-800 whitespace-nowrap flex-shrink-0 dark:bg-orange-900 dark:text-orange-200"
        >
          <!-- Image in selected tags -->
          <img
            v-if="getOptionImage(value)"
            :src="getOptionImage(value)"
            :alt="`${getOptionLabel(value)} ${imageAltSuffix}`"
            class="w-3 h-2 mr-1 object-cover rounded-sm"
            @error="handleImageError"
          />
          {{ getOptionLabel(value) }}
          <button
            @click="removeOption(value)"
            class="ml-1 inline-flex items-center justify-center w-4 h-4 rounded-full text-orange-400 hover:bg-orange-200 hover:text-orange-600 dark:text-orange-300 dark:hover:bg-orange-800"
          >
            ×
          </button>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted, nextTick } from 'vue'

const props = defineProps({
  options: {
    type: Array,
    required: true,
    default: () => []
  },
  selectedValues: {
    type: Array,
    required: true,
    default: () => []
  },
  placeholder: {
    type: String,
    required: true
  },
  searchPlaceholder: {
    type: String,
    default: 'Szukaj...'
  },
  searchable: {
    type: Boolean,
    default: true
  },
  showSelectedItems: {
    type: Boolean,
    default: true
  },
  imageAltSuffix: {
    type: String,
    default: 'flag'
  }
})

const emit = defineEmits(['update:selectedValues'])

// Reactive data
const isDropdownOpen = ref(false)
const searchQuery = ref('')

// Helper function to normalize text for search (removes Polish diacritics)
const normalizeText = (text) => {
  const polishMap = {
    'ą': 'a', 'Ą': 'A',
    'ć': 'c', 'Ć': 'C',
    'ę': 'e', 'Ę': 'E',
    'ł': 'l', 'Ł': 'L',
    'ń': 'n', 'Ń': 'N',
    'ó': 'o', 'Ó': 'O',
    'ś': 's', 'Ś': 'S',
    'ź': 'z', 'Ź': 'Z',
    'ż': 'z', 'Ż': 'Z'
  }

  return text
    .split('')
    .map(char => polishMap[char] || char)
    .join('')
    .toLowerCase()
}

// Computed
const displayText = computed(() => {
  if (props.selectedValues.length === 0) {
    return props.placeholder
  }
  if (props.selectedValues.length === 1) {
    return getOptionLabel(props.selectedValues[0])
  }
  return `Wybrano: ${props.selectedValues.length}`
})

const filteredOptions = computed(() => {
  if (!searchQuery.value) return props.options
  const normalizedQuery = normalizeText(searchQuery.value)
  return props.options.filter(option =>
    normalizeText(option.label).includes(normalizedQuery) ||
    normalizeText(option.value).includes(normalizedQuery)
  )
})

// Dropdown ref for click outside handling
const dropdownRef = ref(null)
const searchInputRef = ref(null)

// Methods
const toggleOption = (value) => {
  const newSelected = [...props.selectedValues]
  const index = newSelected.indexOf(value)

  if (index > -1) {
    newSelected.splice(index, 1)
  } else {
    newSelected.push(value)
  }

  emit('update:selectedValues', newSelected)
}

const isSelected = (value) => {
  return props.selectedValues.includes(value)
}

const removeOption = (value) => {
  const newSelected = props.selectedValues.filter(v => v !== value)
  emit('update:selectedValues', newSelected)
}

const clearSelection = (event) => {
  if (event) {
    event.stopPropagation()
  }
  emit('update:selectedValues', [])
}

const selectAll = () => {
  const allValues = filteredOptions.value.map(option => option.value)
  emit('update:selectedValues', allValues)
}

const getOptionLabel = (value) => {
  const option = props.options.find(opt => opt.value === value)
  return option?.label || value
}

const getOptionImage = (value) => {
  const option = props.options.find(opt => opt.value === value)
  return option?.flag || option?.image || ''
}

const handleImageError = (event) => {
  const img = event.target
  img.style.display = 'none'
}

const handleClickOutside = (event) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
    isDropdownOpen.value = false
    searchQuery.value = ''
  }
}

const openDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value
  if (!isDropdownOpen.value) {
    searchQuery.value = ''
  }
}

watch(isDropdownOpen, async (open) => {
  if (open) {
    document.addEventListener('click', handleClickOutside)
    // Auto-focus search input when dropdown opens
    if (props.searchable && searchInputRef.value) {
      await nextTick()
      searchInputRef.value.focus()
    }
  } else {
    document.removeEventListener('click', handleClickOutside)
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
