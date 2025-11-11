/**
 * Utility functions for formatting dates and prices
 */

/**
 * Format a price with PLN currency and 2 decimal places
 * @param {number} price - The price to format
 * @returns {string} Formatted price (e.g., "123.45 PLN")
 */
export function formatPrice(price) {
  if (price === null || price === undefined) return 'N/A'
  return `${parseFloat(price).toFixed(2)} PLN`
}

/**
 * Format a date from YYYY-MM-DD or ISO format to DD.MM.YYYY format
 * @param {string} dateStr - The date string to format
 * @returns {string} Formatted date (e.g., "06.12.2025")
 */
export function formatDate(dateStr) {
  if (!dateStr) return 'N/A'

  const date = new Date(dateStr)

  // Check if date is valid
  if (isNaN(date.getTime())) return dateStr

  // Format as: DD.MM.YYYY
  const day = String(date.getDate()).padStart(2, '0')
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const year = date.getFullYear()

  return `${day}.${month}.${year}`
}

/**
 * Format a datetime string to DD.MM.YYYY HH:MM format
 * @param {string} dateTimeStr - The datetime string to format
 * @returns {string} Formatted datetime (e.g., "06.12.2025 15:30")
 */
export function formatDateTime(dateTimeStr) {
  if (!dateTimeStr) return 'N/A'

  const date = new Date(dateTimeStr)

  // Check if date is valid
  if (isNaN(date.getTime())) return dateTimeStr

  // Format as: DD.MM.YYYY HH:MM
  const day = String(date.getDate()).padStart(2, '0')
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const year = date.getFullYear()
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')

  return `${day}.${month}.${year} ${hours}:${minutes}`
}

/**
 * Format a time from ISO string to HH:MM format
 * @param {string} timeStr - The time string (e.g., "2025-11-14T15:30:00.000")
 * @returns {string} Formatted time (e.g., "15:30")
 */
export function formatTime(timeStr) {
  if (!timeStr) return ''

  // Handle format: YYYY-MM-DDTHH:MM:SS.mmm
  // Extract just the time part and remove seconds
  const timePart = timeStr.split('T')[1]
  if (!timePart) return timeStr

  // Get HH:MM
  const [hours, minutes] = timePart.split(':')
  return `${hours}:${minutes}`
}

/**
 * Format a date with weekday in Polish from YYYY-MM-DD or ISO format to "Weekday, DD.MM.YYYY" format
 * @param {string} dateStr - The date string to format
 * @returns {string} Formatted date with weekday (e.g., "Poniedziałek, 16.11.2025")
 */
export function formatDateWithWeekday(dateStr) {
  if (!dateStr) return 'N/A'

  const date = new Date(dateStr)

  // Check if date is valid
  if (isNaN(date.getTime())) return dateStr

  // Polish weekday names
  const weekdays = [
    'Niedziela',      // Sunday
    'Poniedziałek',   // Monday
    'Wtorek',         // Tuesday
    'Środa',          // Wednesday
    'Czwartek',       // Thursday
    'Piątek',         // Friday
    'Sobota'          // Saturday
  ]

  const weekday = weekdays[date.getDay()]

  // Format as: DD.MM.YYYY
  const day = String(date.getDate()).padStart(2, '0')
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const year = date.getFullYear()

  return `${weekday}, ${day}.${month}.${year}`
}
