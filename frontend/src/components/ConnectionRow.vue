<script setup>
// One line in the Connections list. Rows expand in place — no modal, no
// second page — so the dashboard stays a single view.
defineProps({
  name: { type: String, required: true },
  status: { type: String, required: true },
  // Empty action = inert row (a connection the user cannot configure yet).
  action: { type: String, default: '' },
  open: { type: Boolean, default: false },
})

defineEmits(['toggle'])
</script>

<template>
  <div class="row">
    <div class="head">
      <p class="name">{{ name }}</p>
      <p class="status">{{ status }}</p>
      <button
        v-if="action"
        class="linkbtn"
        type="button"
        @click="$emit('toggle')"
      >
        {{ open ? 'close' : action }}
      </button>
      <span v-else />
    </div>

    <div v-if="open" class="body">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.row {
  border-bottom: 1px solid var(--hairline);
}

.head {
  display: grid;
  grid-template-columns: 220px 1fr auto;
  gap: 24px;
  align-items: baseline;
  padding: 18px 0;
}

.name {
  font-size: 16px;
  font-weight: 500;
  color: var(--ink);
}

.status {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--muted);
  overflow-wrap: anywhere;
}

.body {
  padding-bottom: 8px;
}

.linkbtn {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--muted);
  background: none;
  border: none;
  border-bottom: 1px solid var(--hairline);
  padding: 0 0 2px;
  cursor: pointer;
  white-space: nowrap;
}

.linkbtn:hover {
  color: var(--ink);
  border-bottom-color: var(--ink);
}

@media (max-width: 720px) {
  .head {
    grid-template-columns: 1fr auto;
    gap: 8px 24px;
  }

  .status {
    grid-column: 1 / -1;
  }
}
</style>
