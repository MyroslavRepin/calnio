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
        <span class="switchlabel">
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
</style>
