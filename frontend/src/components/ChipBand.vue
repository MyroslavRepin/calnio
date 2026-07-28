<script setup>
// The band that sits over the blue arc. Chips are white surfaces on purpose —
// nothing else is allowed to overlap the saturated part of a circle.
const events = [
  { label: 'Ship onboarding copy', meta: 'Thu 14:00' },
  { label: 'Invoice — March', meta: 'Fri 09:00' },
  { label: 'Call with Anna', meta: 'Mon 11:30' },
]
</script>

<template>
  <section class="band">
    <div class="wrap inner">
      <div class="chips">
        <span v-for="e in events" :key="e.label" class="chip">
          <span class="label">{{ e.label }}</span>
          <span class="meta">{{ e.meta }}</span>
        </span>
      </div>

      <p class="claim">
        Notion pages with a due date become events in one Apple calendar you
        pick. Rename a task, move a date, delete a page — the calendar follows
        on the next run.
      </p>
    </div>
  </section>
</template>

<style scoped>
.band {
  position: relative;
  z-index: 1;
  padding-top: clamp(24px, 5vw, 48px);
  padding-bottom: clamp(40px, 8vw, 80px);
}

.inner {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: clamp(28px, 5vw, 56px);
  align-items: center;
}

.chips {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
}

.chip {
  display: inline-flex;
  align-items: baseline;
  gap: 12px;
  background: #fff;
  padding: 13px 18px;
  border-radius: 10px;
  box-shadow: 0 18px 40px -26px rgba(4, 32, 74, 0.85);
}

.label {
  font-size: 15px;
  color: var(--ink);
}

.meta {
  font-family: var(--font-mono);
  font-size: 12.5px;
  color: var(--muted-cool);
  white-space: nowrap;
}

/* Copy here sits near the blue, so it takes the cool body colour. */
.claim {
  font-size: clamp(16px, 1.5vw, 17px);
  line-height: 1.55;
  max-width: 46ch;
  text-wrap: pretty;
  color: var(--body-cool);
}
</style>
