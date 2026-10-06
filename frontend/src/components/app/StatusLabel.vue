<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: String, default: null },
})

// A run or sync state in words, with the tone that repeats it in colour.
const label = computed(function () {
  if (props.status === 'ok') {
    return { text: 'ok', tone: 'success' }
  }
  if (props.status === 'error') {
    return { text: 'failed', tone: 'danger' }
  }
  if (props.status === 'auth_error') {
    return { text: 'rejected', tone: 'danger' }
  }
  if (props.status === 'unfinished') {
    return { text: 'unfinished', tone: 'attention' }
  }
  if (props.status === 'paused') {
    return { text: 'paused', tone: 'neutral' }
  }
  return { text: 'never run', tone: 'neutral' }
})
</script>

<template>
  <span class="label" :class="label.tone">{{ label.text }}</span>
</template>
