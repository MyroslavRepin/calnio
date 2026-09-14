<script setup>
import { computed, ref } from 'vue'
import { useAppleCalendar } from '../../composables/useAppleCalendar'
import { formatDateTime } from '../../format'

// Everything this block does goes through the Apple Calendar composable. The
// credential is all that lives here now: which calendar each sync writes to is
// the Syncs page's business.
const appleResult = useAppleCalendar()
const state = appleResult.state
const disconnect = appleResult.disconnect

const confirming = ref(false)
const error = ref('')

// When the credentials were last checked against iCloud.
const verified = computed(function () {
  return formatDateTime(state.connection?.last_verified_at, '—')
})

async function confirmDisconnect() {
  error.value = ''

  const result = await disconnect()
  if (result.error) {
    error.value = result.error
  }

  confirming.value = false
}
</script>

<template>
  <div class="column status">
    <dl class="datarows">
      <div>
        <dt>Apple Account</dt>
        <dd>{{ state.connection.icloud_email }}</dd>
      </div>
      <div>
        <dt>Last verified</dt>
        <dd>{{ verified }}</dd>
      </div>
    </dl>

    <template v-if="confirming">
      <p class="body">
        Disconnecting forgets your app-specific password, so nothing can sync
        until you reconnect. Events Calnio already wrote stay in your calendars,
        delete them yourself if you want them gone.
      </p>
      <div class="row actions">
        <button class="btn danger" type="button" :disabled="state.busy" @click="confirmDisconnect">
          {{ state.busy ? 'Disconnecting…' : 'Disconnect' }}
        </button>
        <button class="btn plain" type="button" @click="confirming = false">Cancel</button>
      </div>
    </template>

    <div v-else class="row actions">
      <button class="btn plain" type="button" @click="confirming = true">
        Disconnect
      </button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>
