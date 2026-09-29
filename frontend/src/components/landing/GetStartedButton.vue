<script setup>
import { useRouter } from 'vue-router'
import { useAuth } from '../../composables/useAuth'

defineProps({
  label: { type: String, default: 'Get started' },
})

const authResult = useAuth()
const state = authResult.state
const login = authResult.login

const router = useRouter()

// A visitor with an account goes to the dashboard, everyone else starts the
// Google flow. Login is a real navigation, not a fetch: the browser has to
// follow the redirects to Google and back.
function start() {
  if (state.ready && state.user) {
    router.push('/dashboard')
    return
  }
  login()
}
</script>

<template>
  <button type="button" class="btn" @click="start">{{ label }}</button>
</template>
