<script setup>
const steps = [
  {
    n: '01',
    title: 'Notion is the truth',
    body: 'Calnio recomputes your events from Notion on every run. Change something there and the calendar follows.',
  },
  {
    n: '02',
    title: 'One page, one event',
    body: 'Each Notion page id maps to a single calendar UID, so events never duplicate and foreign calendar entries are never touched.',
  },
  {
    n: '03',
    title: 'Last edit wins',
    body: 'Move a due date and the next reconcile loop updates the calendar. Deletes in Notion remove the matching event.',
  },
]
</script>

<template>
  <section id="how" class="how">
    <div class="wrap inner">
      <p class="eyebrow">How sync works</p>

      <div class="grid">
        <article v-for="s in steps" :key="s.n" class="step">
          <span class="num">{{ s.n }}</span>
          <h3>{{ s.title }}</h3>
          <p class="body">{{ s.body }}</p>
        </article>
      </div>

      <p class="note">
        Today Calnio writes one way: Notion → Apple Calendar. Two-way sync is
        next on the roadmap.
      </p>
    </div>
  </section>
</template>

<style scoped>
.how {
  border-top: 1px solid var(--hairline);
}

.inner {
  padding: 96px 0;
  display: flex;
  flex-direction: column;
  gap: 48px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 56px;
}

.step {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.num {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--muted);
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

.note {
  font-family: var(--font-mono);
  font-size: 13px;
  line-height: 1.6;
  color: var(--muted);
  max-width: 560px;
}
</style>
