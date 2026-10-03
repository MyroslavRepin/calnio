<script setup>
import LandingFooter from '../../components/landing/LandingFooter.vue'
import LandingNav from '../../components/landing/LandingNav.vue'

// Where a visitor can go instead. The server sends this page with a real 404
// status, so a crawler never takes it for a page of its own.
const destinations = [
  { to: '/', label: 'What Calnio does' },
  { to: '/notion-apple-calendar-sync', label: 'How to sync Notion with Apple Calendar' },
  { to: '/notion-icloud-calendar', label: 'Notion dates in your iPhone calendar' },
  { to: '/faq', label: 'Questions and answers' },
]
</script>

<template>
  <div class="landing-ui column page">
    <LandingNav />

    <main class="column bands">
      <section class="section">
        <div class="container column chapter">
          <div class="column chapterhead">
            <h1 class="headline">There is no page at this address.</h1>
            <p class="tagline">It may have moved, or the link has a typo. One of these is probably what you wanted.</p>
          </div>
          <div class="column topics">
            <router-link
              v-for="destination in destinations"
              :key="destination.to"
              :to="destination.to"
              class="row topic destination"
            >
              {{ destination.label }}
            </router-link>
          </div>
        </div>
      </section>
    </main>

    <LandingFooter />
  </div>
</template>

<style scoped>
.destination {
  font-size: var(--l-text-row);
  font-weight: 600;
}

.destination:hover {
  color: var(--l-blue);
}
</style>
