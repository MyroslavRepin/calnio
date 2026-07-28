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
        class="link-mono quiet"
        type="button"
        @click="$emit('toggle')"
      >
        <span>{{ open ? 'close' : action }}</span>
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

/* Flex-wrap rather than a fixed grid: the status drops to its own line on a
   narrow screen without a breakpoint. */
.head {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px 24px;
  padding: 8px 0;
}

.name {
  flex: 0 0 min(220px, 100%);
  font-size: 16px;
  font-weight: 500;
  color: var(--ink);
}

.status {
  flex: 1 1 min(200px, 100%);
  font-family: var(--font-mono);
  font-size: 12.5px;
  color: var(--muted);
  overflow-wrap: anywhere;
}

.body {
  padding-bottom: 8px;
}
</style>
