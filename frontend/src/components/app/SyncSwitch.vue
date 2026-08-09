<script setup>
import { computed } from 'vue'
import { useSync } from '../../composables/useSync'
import { formatDateTime } from '../../format'

// The page owns the error box, so failures are reported upward rather than
// drawn inside this card.
const emit = defineEmits(['error'])

const syncResult = useSync()
const state = syncResult.state
const setEnabled = syncResult.setEnabled

const enabled = computed(function () {
  return Boolean(state.settings?.enabled)
})

const eligible = computed(function () {
  return Boolean(state.settings?.eligible)
})

const lastRun = computed(function () {
  return formatDateTime(state.settings?.last_run_at, 'never')
})

// What the last run did, in the user's terms. auth_error is the only status
// that also turned the switch off, so it has to explain itself.
const statusLine = computed(function () {
  if (state.pending) {
    return 'Syncing now, this takes a few seconds.'
  }

  const status = state.settings?.last_status

  if (status === 'ok') {
    return 'Last sync finished normally.'
  }
  if (status === 'error') {
    return 'Last sync failed. Calnio tries again on the next run.'
  }
  if (status === 'auth_error') {
    return 'A connection was rejected, so syncing was turned off. Reconnect it, then turn syncing back on.'
  }
  return 'Nothing has synced yet.'
})

async function toggle() {
  emit('error', null)

  const result = await setEnabled(!enabled.value)
  if (result.error) {
    emit('error', result.error)
  }
}
</script>

<template>
  <section class="card">
    <div class="card-head">
      <h2>Syncing</h2>
      <span class="label" :class="enabled ? 'success' : 'neutral'">
        {{ enabled ? 'On' : 'Off' }}
      </span>
    </div>

    <div class="card-body">
      <button
        class="switch"
        type="button"
        role="switch"
        :aria-checked="enabled"
        :disabled="!eligible || state.busy"
        @click="toggle"
      >
        <span class="track" :class="{ on: enabled }"><span class="knob"></span></span>
        <span class="switch-label">
          {{ enabled ? 'Syncing is on' : 'Syncing is off' }}
        </span>
      </button>

      <p v-if="!eligible" class="note">
        Connect Notion and Apple Calendar, and pick a due-date column below,
        before turning syncing on.
        <router-link :to="{ name: 'welcome' }">Finish setup</router-link>
      </p>

      <template v-else>
        <p class="note">{{ statusLine }}</p>

        <dl class="datarows">
          <div>
            <dt>Last run</dt>
            <dd>{{ lastRun }}</dd>
          </div>
        </dl>
      </template>
    </div>
  </section>
</template>

<style scoped>
.card-body > * + * {
  margin-top: var(--app-gap-stack);
}

/* State is carried by colour and by the knob's side, with no transition: it
   reads as a control, not as an animation. */
.switch {
  display: inline-flex;
  align-items: center;
  gap: var(--app-space-2);
  padding: 0;
  background: none;
  border: none;
  cursor: pointer;
  font-family: inherit;
  font-size: var(--app-text-body);
  color: var(--app-fg);
}

.switch:disabled {
  opacity: 0.6;
  cursor: default;
}

.track {
  display: inline-flex;
  align-items: center;
  width: 48px;
  height: 28px;
  padding: 3px;
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  background: var(--app-canvas-subtle);
}

.track.on {
  background: var(--app-accent);
  border-color: var(--app-accent);
}

.knob {
  width: var(--app-marker);
  height: var(--app-marker);
  border-radius: var(--app-radius-sm);
  background: var(--app-canvas);
  border: 1px solid var(--app-border);
}

.track.on .knob {
  margin-left: auto;
  border-color: var(--app-border-emphasis);
}

.switch-label {
  font-weight: var(--app-weight-medium);
}
</style>
