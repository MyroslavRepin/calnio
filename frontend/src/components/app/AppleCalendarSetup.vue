<script setup>
import { computed, ref } from 'vue'
import { useAppleCalendar } from '../../composables/useAppleCalendar'

// One step: store the credential. Which calendar each sync writes to is picked
// per sync, so this wizard no longer chooses one. The number is a prop so the
// welcome page can run this and the Notion wizard as one sequence.
defineProps({
  numbers: {
    type: Array,
    default: function () {
      return ['1']
    },
  },
})

// Everything this wizard does goes through the Apple Calendar composable.
const appleResult = useAppleCalendar()
const state = appleResult.state
const connect = appleResult.connect

const email = ref('')
const password = ref('')
const error = ref('')

// Done once the credential is stored.
const connected = computed(function () {
  return Boolean(state.connection)
})

async function submitCredentials() {
  error.value = ''

  const result = await connect(email.value.trim(), password.value.trim())
  if (result.error) {
    error.value = result.error
    return
  }

  password.value = '' // no reason to keep it in memory once it is stored
}
</script>

<template>
  <div class="column setup">
    <section class="column step">
      <div class="row stephead">
        <span class="num" :class="{ done: connected }">{{ numbers[0] }}</span>
        <h3>Connect your iCloud account</h3>
      </div>

      <div class="column stepbody">
        <template v-if="!connected">
          <!-- The short version, for a Connections row. The welcome page fills
               the slot with the full walkthrough instead of repeating this. -->
          <p v-if="!$slots.help" class="body">
            Apple requires an app-specific password, your normal Apple Account
            password will not work. Create one at
            <a href="https://account.apple.com" target="_blank" rel="noreferrer">account.apple.com</a>
            under Sign-In and Security → App-Specific Passwords.
          </p>
          <slot name="help" />

          <form class="column credentials" @submit.prevent="submitCredentials">
            <label class="column field">
              <span>Apple Account email</span>
              <input v-model="email" type="email" required autocomplete="username" placeholder="you@icloud.com" />
            </label>

            <label class="column field">
              <span>App-specific password</span>
              <!-- Plain text on purpose: an app-specific password is a
                   four-group string nobody can type blind, and a typo costs a
                   round trip to iCloud that rejects it. -->
              <input v-model="password" type="text" required autocomplete="off" autocapitalize="none" autocorrect="off"
                spellcheck="false" placeholder="xxxx-xxxx-xxxx-xxxx" />
            </label>

            <button class="btn" type="submit" :disabled="state.busy">
              {{ state.busy ? 'Checking with iCloud…' : 'Connect' }}
            </button>
          </form>

          <p class="note">
            Calnio stores this password encrypted and uses it only to write events
            into the calendars you choose. Revoking it in your Apple Account
            settings disconnects Calnio immediately.
          </p>
        </template>

        <p v-else class="body">
          Connected as <strong>{{ state.connection.icloud_email }}</strong>
        </p>
      </div>
    </section>

    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<style scoped>
.credentials {
  --gap: var(--app-gap-block);
  align-items: flex-start;
  width: 100%;
}
</style>
