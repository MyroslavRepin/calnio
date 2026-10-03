<script setup>
import FinalCta from '../../components/landing/FinalCta.vue'
import LandingFooter from '../../components/landing/LandingFooter.vue'
import LandingNav from '../../components/landing/LandingNav.vue'
import PageHero from '../../components/landing/PageHero.vue'
import { questions } from '../../faq'
</script>

<template>
  <div class="landing-ui column page">
    <LandingNav />

    <main class="column bands">
      <PageHero
        title="Questions about syncing Notion with Apple Calendar"
        lead="What Calnio costs, what it keeps, how often it runs, what two-way means, and how to take it all back. If something is missing here, write to me and I will add it."
      />

      <section class="section">
        <div class="container column chapter">
          <div class="column topics">
            <div v-for="entry in questions" :key="entry.question" class="row topic">
              <h2 class="topicname">{{ entry.question }}</h2>
              <div class="column topicbody">
                <p v-for="line in entry.answer" :key="line">{{ line }}</p>
              </div>
            </div>
          </div>
          <p class="tagline">
            Setting it up for the first time? Follow the
            <router-link to="/notion-apple-calendar-sync">step-by-step guide</router-link>,
            or read how it works
            <router-link to="/notion-icloud-calendar">on an iPhone with iCloud</router-link>.
          </p>
        </div>
      </section>

      <FinalCta />
    </main>

    <LandingFooter />
  </div>
</template>
