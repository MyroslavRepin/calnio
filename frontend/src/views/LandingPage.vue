<script setup>
import { computed } from 'vue'
import { useAuth } from '../composables/useAuth'
import TheNav from '../components/TheNav.vue'
import HeroSection from '../components/HeroSection.vue'
import BetaStrip from '../components/BetaStrip.vue'
import HowItWorks from '../components/HowItWorks.vue'
import FeatureGrid from '../components/FeatureGrid.vue'
import GetStarted from '../components/GetStarted.vue'
import TheFooter from '../components/TheFooter.vue'

defineProps({
  showBeta: { type: Boolean, default: true },
})

const { state } = useAuth()

const errorMessage = computed(() => {
  if (!state.error) return null
  if (state.error === 'oauth') return "Google sign-in didn't complete. Please try again."
  if (state.error === 'userinfo') return 'Google returned no profile. Please try again.'
  return 'Sign-in failed. Please try again.'
})
</script>

<template>
  <TheNav />
  <p v-if="errorMessage" class="auth-error wrap" role="alert">{{ errorMessage }}</p>
  <main>
    <HeroSection />
    <BetaStrip v-if="showBeta" />
    <HowItWorks />
    <FeatureGrid />
    <GetStarted />
  </main>
  <TheFooter />
</template>

<style scoped>
.auth-error {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--ink);
  padding-top: 12px;
  padding-bottom: 12px;
}
</style>
