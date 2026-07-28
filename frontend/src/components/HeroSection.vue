<script setup>
import GoogleButton from './GoogleButton.vue'
</script>

<template>
  <section class="hero">
    <div class="wrap inner">
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

      <div class="cta">
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

.inner {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: clamp(20px, 3vw, 28px);
}

.lead {
  max-width: 44ch;
}

.cta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: clamp(16px, 3vw, 28px);
}
</style>
