<script setup>
import GoogleButton from './GoogleButton.vue'
</script>

<template>
  <section class="hero">
    <div class="wrap column hero">
      <p class="eyebrow">Notion → Apple Calendar · one way, for now</p>

      <!-- The breaks are authored, not wrapped: they set the rhythm. -->
      <h1 class="display">
        Plan it once.<br />
        See it<br />
        everywhere.
      </h1>

      <p class="lead">
        Calnio keeps your Apple Calendar in step with Notion. Notion stays the
        source of truth, and every task with a due date lands on your calendar
        on its own.
      </p>

      <div class="row cta">
        <GoogleButton label="Start syncing" />
        <a href="#start" class="link-mono"><span>See what setup takes</span></a>
      </div>
    </div>
  </section>
</template>

<style scoped>
.hero {
  position: relative;
  z-index: 1;
  padding-top: clamp(40px, 9vw, 84px);
  padding-bottom: var(--sec-bottom);
}

.hero {
  --gap: clamp(20px, 3vw, 28px);
  align-items: flex-start;
}

.lead {
  max-width: 44ch;
}

.cta {
  --gap: clamp(16px, 3vw, 28px);
}
</style>
