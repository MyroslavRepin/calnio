<script setup>
import { computed } from 'vue'
import { useAuth } from '../composables/useAuth'
import AtmosphereField from '../components/AtmosphereField.vue'
import TheNav from '../components/TheNav.vue'
import HeroSection from '../components/HeroSection.vue'
import ChipBand from '../components/ChipBand.vue'
import BetaStrip from '../components/BetaStrip.vue'
import HowItWorks from '../components/HowItWorks.vue'
import FeatureGrid from '../components/FeatureGrid.vue'
import GetStarted from '../components/GetStarted.vue'
import TheFooter from '../components/TheFooter.vue'

defineProps({
  // The two page-level switches from the design contract.
  showField: { type: Boolean, default: true },
  showBeta: { type: Boolean, default: true },
})

const { state } = useAuth()

const errorMessage = computed(() => {
  if (!state.error) return null
  if (state.error === 'oauth') return "Google sign-in didn't finish. Try again."
  if (state.error === 'userinfo') return 'Google returned no profile. Try again.'
  return 'Sign-in failed. Try again.'
})
</script>

<template>
  <div class="page">
    <AtmosphereField v-if="showField" />

    <TheNav />

    <p v-if="errorMessage" class="wrap auth-error" role="alert">{{ errorMessage }}</p>

    <main>
      <HeroSection />
      <ChipBand />
      <BetaStrip v-if="showBeta" />
      <HowItWorks />
      <FeatureGrid />
      <GetStarted />
    </main>

    <TheFooter />
  </div>
</template>

<style scoped>
/* The circles hang off this element, so it is what crops them — `clip` rather
   than `hidden` because `hidden` would make this a scroll container and break
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
