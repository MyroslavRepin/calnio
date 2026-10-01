<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../../composables/useAuth'
import CalnioMark from '../CalnioMark.vue'

const authResult = useAuth()
const state = authResult.state
const login = authResult.login

const router = useRouter()

// One call to action in the bar, worded for whether the visitor has an account.
const label = computed(function () {
  if (state.ready && state.user) {
    return 'Open dashboard'
  }
  return 'Sign in'
})

// Signed in goes to the app, signed out starts the Google flow.
function start() {
  if (state.ready && state.user) {
    router.push('/dashboard')
    return
  }
  login()
}
</script>

<template>
  <header class="navbar">
    <div class="container row navrow">
      <router-link to="/" class="wordmark">
        <span class="plate"><CalnioMark /></span>
        Calnio
      </router-link>

      <button class="btn" type="button" @click="start">{{ label }}</button>
    </div>
  </header>
</template>

<style scoped>
/* The bar sits on the hero's own black, so it carries no line under it. */
.navbar {
  background: var(--l-ink);
  color: #fff;
  padding: clamp(20px, 2.6vw, 34px) 0;
  --mark-plate: #ffffff;
  --mark-glyph: #0a0a0a;
}

.navrow {
  --gap: var(--app-gap-block);
  justify-content: space-between;
}

.plate {
  width: clamp(30px, 3vw, 40px);
  height: clamp(30px, 3vw, 40px);
  flex: none;
}
</style>
