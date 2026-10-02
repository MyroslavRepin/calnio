<script setup>
import { onMounted } from 'vue'
import { useAuth } from './composables/useAuth'
import { consumeEventFlag } from './composables/useAnalytics'

// Ask the server who is signed in, once, when the app starts.
const authResult = useAuth()

onMounted(function () {
  consumeEventFlag()
  authResult.bootstrap()
})
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
