<script setup>
// One row of the setup sequence. Only the step being worked on renders its
// body, so the page is never a wall of three open forms. A finished step
// collapses to its own answer, a later one stays a dim title.
defineProps({
  number: { type: String, required: true },
  title: { type: String, required: true },
  // What the step ended up as, shown on the right once it is done.
  summary: { type: String, default: '' },
  done: { type: Boolean, default: false },
  open: { type: Boolean, default: false },
  locked: { type: Boolean, default: false },
})
</script>

<template>
  <section class="column setupstep" :class="{ locked }">
    <div class="row stepline">
      <span class="num" :class="{ done, now: open }">
        <template v-if="done">✓</template>
        <template v-else>{{ number }}</template>
      </span>

      <h2 class="steptitle">{{ title }}</h2>

      <span v-if="done && summary" class="label success">{{ summary }}</span>
      <span v-else-if="locked" class="note">Next</span>
    </div>

    <div v-if="open" class="column stepbody">
      <slot />
    </div>
  </section>
</template>

<style scoped>
.setupstep {
  --gap: var(--app-gap-stack);
  padding: var(--app-space-5) 0;
  border-top: 1px solid var(--app-border-subtle);
}

.setupstep:first-child {
  border-top: none;
  padding-top: 0;
}

.setupstep:last-child {
  padding-bottom: 0;
}

/* A step the user has not reached recedes, but stays readable: it is the map of
   what is left, not decoration. */
.locked .steptitle {
  color: var(--app-fg-subtle);
}

.stepline {
  --gap: var(--app-gap-stack);
  flex-wrap: nowrap;
}

.steptitle {
  flex: 1;
  margin: 0;
  min-width: 0;
  font-size: var(--app-text-head);
  font-weight: var(--app-weight-bold);
  letter-spacing: -0.01em;
  color: var(--app-fg);
}

.label {
  max-width: 24ch;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Indented under the numeral, so the sequence reads as one column. */
.stepbody {
  --gap: var(--app-gap-block);
  align-items: flex-start;
  padding-left: calc(var(--app-marker) + var(--app-gap-stack));
}
</style>
