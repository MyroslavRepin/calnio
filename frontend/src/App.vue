<script setup>
import { onMounted } from 'vue'
import { useAuth } from './composables/useAuth'

// Ask the server who is signed in, once, when the app starts.
const authResult = useAuth()

onMounted(authResult.bootstrap)
</script>

<template>
  <div class="app">
    <router-view />
  </div>
</template>

<style scoped>
/* Pages position their own atmosphere layer against this. */
.app {
  min-height: 100vh;
}
</style>
