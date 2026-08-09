<script setup>
// Four, per the page contract. Two of them used to restate steps 02 and 03 —
// they now cover the things the steps do not: what happens when a run fails,
// and what Calnio will not touch.
const features = [
  {
    title: 'Nothing to install',
    body: 'Calnio is hosted. Connect your two accounts once and the sync runs without you.',
  },
  {
    title: 'When a run fails',
    body: 'A failed run changes nothing and the next one picks up where it left off. No half-written calendar.',
  },
  {
    title: 'Your calendar stays yours',
    body: 'Calnio tracks only the events it created, in the one calendar you point it at. Everything else is untouched.',
  },
  {
    title: 'Built on standards',
    body: "Notion's API and CalDAV for iCloud. Open protocols, nothing proprietary in between.",
  },
]
</script>

<template>
  <section class="section">
    <div class="wrap grid features">
      <article v-for="f in features" :key="f.title" class="column feature">
        <h3>{{ f.title }}</h3>
        <p class="body">{{ f.body }}</p>
      </article>
    </div>
  </section>
</template>

<style scoped>
.features {
  --col: 220px;
  --gap: clamp(28px, 5vw, 48px);
  border-top: 1px solid var(--hairline);
  padding-top: clamp(32px, 5vw, 48px);
}

.feature {
  --gap: 10px;
}

h3 {
  font-size: 17px;
  font-weight: 600;
  color: var(--ink);
}

.body {
  font-size: 14.5px;
  line-height: 1.6;
  color: var(--body);
}
</style>
