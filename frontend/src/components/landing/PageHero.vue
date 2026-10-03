<script setup>
import GetStartedButton from './GetStartedButton.vue'

// The dark band that opens every guide page: its one h1, the paragraph that
// answers the search, and the sign-in button.
defineProps({
  title: { type: String, required: true },
  lead: { type: String, required: true },
})
</script>

<template>
  <section class="section dark pagehero">
    <div class="container column pageherobody">
      <h1 class="headline hero">{{ title }}</h1>
      <p class="tagline pagelead">{{ lead }}</p>
      <div class="row pagecta">
        <GetStartedButton />
        <p class="tagline">Free. Nothing to install.</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* The nav band pays for the space above the headline. */
.pagehero {
  padding-top: clamp(28px, 4vw, 56px);
}

.pageherobody {
  --gap: clamp(20px, 2.6vw, 32px);
}

.pagelead {
  max-width: 52ch;
}

.pagecta {
  --gap: var(--app-space-5);
  margin-top: 8px;
}
</style>
