<script setup>
// One connection in the Connections list, as a card that expands in place.
defineProps({
  name: { type: String, required: true },
  status: { type: String, required: true },
  // success draws the value in ink, anything else in grey.
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
        <span class="connectedas" :class="tone">{{ status }}</span>
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

.connectedas {
  color: var(--app-fg-muted);
}

.connectedas.success {
  color: var(--app-fg);
}

.name {
  font-size: var(--app-text-body);
  font-weight: var(--app-weight-bold);
  color: var(--app-fg);
}
</style>
