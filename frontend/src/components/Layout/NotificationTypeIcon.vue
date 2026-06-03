<script>
const SUPPORTED_TYPES = new Set(['success', 'info', 'warning', 'error'])

export default {
  name: 'NotificationTypeIcon',
  props: {
    type: {
      type: String,
      default: 'info',
    },
  },
  computed: {
    normalizedType() {
      return SUPPORTED_TYPES.has(this.type) ? this.type : 'info'
    },
  },
}
</script>

<template>
  <svg
      v-if="normalizedType === 'success'"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2.4"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
      focusable="false"
  >
    <path d="M20 6 9 17l-5-5"></path>
  </svg>

  <svg
      v-else-if="normalizedType === 'warning'"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
      focusable="false"
  >
    <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
    <path d="M12 9v4"></path>
    <path d="M12 17h.01"></path>
  </svg>

  <svg
      v-else-if="normalizedType === 'error'"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2.2"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
      focusable="false"
  >
    <path d="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z"></path>
    <path d="m15 9-6 6"></path>
    <path d="m9 9 6 6"></path>
  </svg>

  <svg
      v-else
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
      focusable="false"
  >
    <path d="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z"></path>
    <path d="M12 16v-4"></path>
    <path d="M12 8h.01"></path>
  </svg>
</template>
