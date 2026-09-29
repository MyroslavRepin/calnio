<script setup>
import { ref } from 'vue'
import { useAppleCalendar } from '../../composables/useAppleCalendar'

// Store the iCloud credential. This is the step people give up on, so the
// walkthrough lives here rather than being passed in: the requirement Apple
// imposes is the same wherever this form is shown, and stating it late is what
// makes it a dead end.
const appleResult = useAppleCalendar()
const state = appleResult.state
const connect = appleResult.connect

const email = ref('')
const password = ref('')
const error = ref('')

async function submitCredentials() {
  error.value = ''

  const result = await connect(email.value.trim(), password.value.trim())
  if (result.error) {
    error.value = result.error
    return
  }

  // No reason to keep it in memory once iCloud has accepted it.
  password.value = ''
}
</script>

<template>
  <div class="column apple">
    <p class="body">
      Apple does not offer a sign-in button for calendar access. The only way in
      is an <strong>app-specific password</strong>, which you generate yourself
      and can revoke at any time. It takes about a minute.
    </p>

    <p class="note">
      Your Apple Account needs two-factor authentication turned on. Without it
      Apple does not offer app-specific passwords at all.
    </p>

    <ol class="column walkthrough">
      <li>
        Open
        <a href="https://account.apple.com/account/manage" target="_blank" rel="noreferrer">
          account.apple.com
        </a>
        and sign in
      </li>
      <li>Go to Sign-In and Security, then App-Specific Passwords</li>
      <li>Choose Generate an app-specific password</li>
      <li>Name it <code>Calnio</code> and copy the <code>xxxx-xxxx-xxxx-xxxx</code> it shows</li>
    </ol>

    <form class="column credentials" @submit.prevent="submitCredentials">
      <label class="column field">
        <span>Apple Account email</span>
        <input
          v-model="email"
          type="email"
          required
          autocomplete="username"
          placeholder="you@icloud.com"
        />
      </label>

      <label class="column field">
        <span>App-specific password</span>
        <!-- Plain text on purpose: nobody can type a four-group string blind,
             and a typo costs a round trip to iCloud that rejects it. -->
        <input
          v-model="password"
          type="text"
          required
          autocomplete="off"
          autocapitalize="none"
          autocorrect="off"
          spellcheck="false"
          placeholder="xxxx-xxxx-xxxx-xxxx"
        />
      </label>

      <button class="btn" type="submit" :disabled="state.busy">
        {{ state.busy ? 'Checking with iCloud…' : 'Connect iCloud' }}
      </button>
    </form>

    <p class="note">
      Calnio stores this encrypted and uses it only to write events into the
      calendars you choose. Revoking it at Apple disconnects Calnio immediately.
    </p>

    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<style scoped>
.apple {
  --gap: var(--app-gap-stack);
  align-items: flex-start;
  width: 100%;
}

.walkthrough {
  --gap: var(--app-space-1);
  margin: 0;
  padding-left: var(--app-space-5);
  font-size: var(--app-text-body);
  color: var(--app-fg-muted);
  max-width: var(--app-measure);
}

.credentials {
  --gap: var(--app-gap-block);
  align-items: flex-start;
  width: 100%;
  padding-top: var(--app-space-2);
}
</style>
