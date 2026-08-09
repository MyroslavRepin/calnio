<script setup>
// One connection in the Connections list, as a card that expands in place —
// no modal, no second page, so the dashboard stays a single view.
defineProps({
  name: { type: String, required: true },
  status: { type: String, required: true },
  // success / attention / neutral, matching the .label tones in components.css.
  tone: { type: String, default: 'neutral' },
  // Empty action = inert row (a connection the user cannot configure yet).
  action: { type: String, default: '' },
  open: { type: Boolean, default: false },
})

defineEmits(['toggle'])
</script>

<template>
  <div class="card">
    <div class="card-head">
      <div class="row ident">
        <span class="name">{{ name }}</span>
        <span class="label" :class="tone">{{ status }}</span>
      </div>

      <button v-if="action" class="btn plain" type="button" @click="$emit('toggle')">
        {{ open ? 'Close' : action }}
      </button>
    </div>

    <div v-if="open" class="card-body">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.ident {
  --gap: var(--app-gap-inline) var(--app-gap-stack);
  min-width: 0;
}

.name {
  font-size: var(--app-text-body);
  font-weight: var(--app-weight-bold);
  color: var(--app-fg);
}
</style>
