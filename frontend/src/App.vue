<script setup>
import { computed, onMounted } from 'vue'
import { useAuth } from './composables/useAuth'

// One accent on screen at a time. It is set here and read everywhere else as
// var(--accent) — step numerals and the atmosphere circles are the only things
// that consume it. Alternates: #0a0a0a, #2f7d5b, #a4670f.
const props = defineProps({
  accent: { type: String, default: '#0b63f6' },
})

const rootStyle = computed(() => ({ '--accent': props.accent }))

onMounted(() => {
  useAuth().bootstrap()
})
</script>

<template>
  <div class="app" :style="rootStyle">
    <router-view />
  </div>
</template>

<style scoped>
/* Pages position their own atmosphere layer against this. */
.app {
  min-height: 100vh;
}
</style>
