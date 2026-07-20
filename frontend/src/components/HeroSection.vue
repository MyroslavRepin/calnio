<script setup>
import GoogleButton from './GoogleButton.vue'
</script>

<template>
  <section class="hero">
    <div class="wrap inner">
      <p class="eyebrow">Notion → Apple Calendar · one-way, for now</p>

      <h1>
        Plan it once.<br />
        See it everywhere.
      </h1>

      <p class="sub">
        Calnio keeps your Apple Calendar in step with Notion. Notion is the
        source of truth, every task with a due date lands on your calendar
        automatically.
      </p>

      <div class="cta-row">
        <GoogleButton label="Start syncing with Google" />
        <a href="#dev" class="link-mono">free while in beta →</a>
      </div>
    </div>
  </section>
</template>

<style scoped>
.hero {
  padding: 64px 0 72px;
}

.inner {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

h1 {
  font-family: var(--font-ui);
  font-size: 84px;
  line-height: 0.94;
  font-weight: 700;
  letter-spacing: -0.045em;
  color: var(--ink);
}

.sub {
  max-width: 560px;
  font-size: 20px;
  line-height: 1.55;
  color: var(--body);
}

.cta-row {
  display: flex;
  align-items: center;
  gap: 26px;
  margin-top: 8px;
}
</style>
