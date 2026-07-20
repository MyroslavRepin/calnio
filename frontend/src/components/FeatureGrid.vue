<script setup>
const features = [
  {
    title: 'Nothing to install',
    body: 'Calnio runs on my server. Connect your accounts once and sync just happens in the background.',
  },
  {
    title: 'No duplicates',
    body: 'A lean link index tracks only the events Calnio owns, nothing else in your calendar is at risk.',
  },
  {
    title: 'Smart scheduler',
    body: 'A reconcile loop handles creates, updates and deletes on a schedule you set.',
  },
  {
    title: 'Built on standards',
    body: "Notion's API and CalDAV (iCloud), open protocols, no lock-in.",
  },
]
</script>

<template>
  <section class="features">
    <div class="wrap">
      <div class="grid">
        <article
          v-for="(f, i) in features"
          :key="f.title"
          class="cell"
          :class="{ right: i % 2 === 1, top: i >= 2 }"
        >
          <h3>{{ f.title }}</h3>
          <p class="body">{{ f.body }}</p>
        </article>
      </div>
    </div>
  </section>
</template>

<style scoped>
.features {
  border-top: 1px solid var(--hairline);
  padding: 96px 0;
}

.grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
}

.cell {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 40px;
}

.cell:first-child {
  padding-left: 0;
}

.cell.right {
  border-left: 1px solid var(--hairline);
}

.cell.top {
  border-top: 1px solid var(--hairline);
}

h3 {
  font-family: var(--font-ui);
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--ink);
}

.body {
  font-size: 16px;
  line-height: 1.55;
  color: var(--body);
}
</style>
