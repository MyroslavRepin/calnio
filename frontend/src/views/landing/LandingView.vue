<script setup>
import { computed } from 'vue'
import { useAuth } from '../../composables/useAuth'
import AtmosphereField from '../../components/landing/AtmosphereField.vue'
import BetaStrip from '../../components/landing/BetaStrip.vue'
import ChipBand from '../../components/landing/ChipBand.vue'
import FeatureGrid from '../../components/landing/FeatureGrid.vue'
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
  <div class="landing-ui page">
    <AtmosphereField />

    <LandingNav />

    <p v-if="errorMessage" class="wrap auth-error" role="alert">{{ errorMessage }}</p>

    <main>
      <HeroSection />
      <ChipBand />
      <BetaStrip />
      <HowItWorks />
      <FeatureGrid />
      <GetStarted />
    </main>

    <LandingFooter />
  </div>
</template>

<style scoped>
/* The circles hang off this element, so it is what crops them. `clip` rather
   than `hidden`, because `hidden` would make this a scroll container and break
   any sticky child. Without it the bottom glow runs on past the footer. */
.page {
  position: relative;
  overflow: clip;
}

.auth-error {
  position: relative;
  z-index: 1;
  font-family: var(--font-mono);
  font-size: 12.5px;
  color: var(--ink);
  padding-top: 12px;
  padding-bottom: 12px;
}
</style>
