<script setup>
import GoogleButton from './GoogleButton.vue'
</script>

<template>
  <section class="column hero">
    <span class="label accent">Notion and Apple Calendar, in step</span>

    <h1 class="display">Your Notion dates, already in your calendar.</h1>

    <p class="lead">
      Point Calnio at the Notion databases you live in. Each one gets its own
      Apple calendar, so you can colour them, hide them, and see them next to
      everything else you have on. Turn two-way on for a database and moving an
      event in your calendar moves the Notion date with it.
    </p>

    <div class="row cta">
      <GoogleButton label="Start syncing" />
      <a href="#start">See what setup takes</a>
    </div>

    <p class="note">
      Hosted, so there is nothing to install and no server to run. Free while in
      beta.
    </p>
  </section>
</template>

<style scoped>
.hero {
  --gap: var(--app-gap-block);
  align-items: flex-start;
  padding-top: var(--app-space-5);
}

/* The one place the app's five type sizes are not enough. See tokens.css. */
.display {
  font-size: var(--app-text-display);
  font-weight: var(--app-weight-bold);
  line-height: var(--app-lh-tight);
  letter-spacing: -0.02em;
  color: var(--app-fg);
  max-width: 22ch;
  margin: 0;
}

.hero .lead {
  max-width: 54ch;
}

.cta {
  --gap: var(--app-gap-block);
  padding-top: var(--app-space-2);
}
</style>
