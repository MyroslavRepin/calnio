<script setup>
import { computed, onMounted } from 'vue'
import { useAuth } from './composables/useAuth'

const props = defineProps({
  accent: { type: String, default: '#0a0a0a' },
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
