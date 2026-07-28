<script setup>
const steps = [
  {
    n: '01',
    title: 'Notion is the truth',
    body: 'Calnio recomputes your events from Notion on every run. Change something there and the calendar follows. Nothing is ever written back to Notion.',
  },
  {
    n: '02',
    title: 'One page, one event',
    body: 'Each Notion page id maps to a single calendar UID, so events do not pile up and anything Calnio did not create is left alone.',
  },
  {
    n: '03',
    title: 'Last edit wins',
    body: 'Move a due date and the next run updates the event. Delete the page in Notion and the event goes with it.',
  },
]
</script>

<template>
  <section id="how" class="section">
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
        Calnio writes one way: Notion → Apple Calendar. Two-way sync does not
        exist yet, and I would rather say so than imply it.
      </p>
    </div>
  </section>
</template>

<style scoped>
#how {
  scroll-margin-top: 24px;
}

.inner {
  display: flex;
  flex-direction: column;
  gap: clamp(32px, 5vw, 48px);
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: clamp(28px, 5vw, 56px);
}

.step {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.num {
  font-family: var(--font-mono);
  font-size: clamp(30px, 6vw, 40px);
  font-weight: 500;
  letter-spacing: -0.04em;
  line-height: 1;
  color: var(--accent, #0b63f6);
}

h3 {
  font-size: clamp(19px, 4.6vw, 21px);
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--ink);
}

.body {
  font-size: 15px;
  line-height: 1.6;
  color: var(--body);
}
</style>
