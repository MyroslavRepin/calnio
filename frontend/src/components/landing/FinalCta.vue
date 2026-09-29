<script setup>
import GetStartedButton from './GetStartedButton.vue'
</script>

<template>
  <section class="section finish">
    <div class="container column finishbody">
      <h2 class="headline">Your dates, where you already look.</h2>
      <p class="tagline">
        Sign in, tick a database, and it shows up in Apple Calendar. Turn two-way
        on and your calendar edits go back to Notion.
      </p>
      <GetStartedButton label="Get started" />
    </div>
  </section>
</template>

<style scoped>
.finishbody {
  --gap: clamp(20px, 2.4vw, 28px);
  align-items: center;
  text-align: center;
}

.finishbody .tagline {
  max-width: 46ch;
}
</style>
