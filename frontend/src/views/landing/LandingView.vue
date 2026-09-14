<script setup>
import { computed } from 'vue'
import { useAuth } from '../../composables/useAuth'
import GetStarted from '../../components/landing/GetStarted.vue'
import HeroSection from '../../components/landing/HeroSection.vue'
import HowItWorks from '../../components/landing/HowItWorks.vue'
import LandingFooter from '../../components/landing/LandingFooter.vue'
import LandingNav from '../../components/landing/LandingNav.vue'

const authResult = useAuth()
const state = authResult.state

// The sign-in failure the Google callback bounced back with, in plain words.
const errorMessage = computed(function () {
  if (!state.error) {
    return null
  }
  if (state.error === 'oauth') {
    return "Google sign-in didn't finish. Try again."
  }
  if (state.error === 'userinfo') {
    return 'Google returned no profile. Try again.'
  }
  return 'Sign-in failed. Try again.'
})
</script>

<template>
  <div class="app-ui column page">
    <LandingNav />

    <main class="column main">
      <p v-if="errorMessage" class="error" role="alert">{{ errorMessage }}</p>

      <HeroSection />
      <HowItWorks />
      <GetStarted />
    </main>

    <LandingFooter />
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
}

.main {
  --gap: var(--app-space-8);
  flex: 1;
  width: 100%;
  max-width: var(--app-width-page);
  margin: 0 auto;
  padding: var(--app-space-7) var(--app-pad-page) var(--app-space-8);
}
</style>
