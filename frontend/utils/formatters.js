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
 * Format a date from YYYY-MM-DD or ISO format to a readable format
 * @param {string} dateStr - The date string to format
 * @returns {string} Formatted date (e.g., "Mon, Jan 15, 2025")
 */
export function formatDate(dateStr) {
  if (!dateStr) return 'N/A'

  const date = new Date(dateStr)

  // Check if date is valid
  if (isNaN(date.getTime())) return dateStr

  // Format as: Mon, Jan 15, 2025
  return date.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

/**
 * Format a datetime string to a readable format
 * @param {string} dateTimeStr - The datetime string to format
 * @returns {string} Formatted datetime (e.g., "1/15/2025, 3:45 PM")
 */
export function formatDateTime(dateTimeStr) {
  if (!dateTimeStr) return 'N/A'

  const date = new Date(dateTimeStr)

  // Check if date is valid
  if (isNaN(date.getTime())) return dateTimeStr

  return date.toLocaleString('en-US', {
    month: 'numeric',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  })
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
