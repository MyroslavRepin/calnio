<script setup>
import { computed } from 'vue'
import { useAuth } from '../../composables/useAuth'
import FinalCta from '../../components/landing/FinalCta.vue'
import HeroSection from '../../components/landing/HeroSection.vue'
import IndieDev from '../../components/landing/IndieDev.vue'
import LandingFooter from '../../components/landing/LandingFooter.vue'
import LandingNav from '../../components/landing/LandingNav.vue'
import RealAlerts from '../../components/landing/RealAlerts.vue'
import SecurityPrivacy from '../../components/landing/SecurityPrivacy.vue'
import SetupShot from '../../components/landing/SetupShot.vue'
import TwoWaySync from '../../components/landing/TwoWaySync.vue'

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
  <div class="landing-ui column page">
    <LandingNav />

    <main class="column bands">
      <div v-if="errorMessage" class="notice">
        <p class="container error" role="alert">{{ errorMessage }}</p>
      </div>

      <HeroSection />
      <RealAlerts />
      <SecurityPrivacy />
      <TwoWaySync />
      <SetupShot />
      <IndieDev />
      <FinalCta />
    </main>

    <LandingFooter />
  </div>
</template>

<style scoped>
/* The sign-in failure sits on the hero's own black, above everything else. */
.notice {
  background: var(--l-ink);
  padding-top: 24px;
}
</style>
