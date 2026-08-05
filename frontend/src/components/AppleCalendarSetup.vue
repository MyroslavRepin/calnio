<script setup>
import { computed, ref } from 'vue'
import { useAppleCalendar } from '../composables/useAppleCalendar'

// See NotionSetup: numbered 3/4 when the welcome page runs both wizards as one
// sequence, 1/2 when it stands alone in a Connections row.
defineProps({
  numbers: { type: Array, default: () => ['1', '2'] },
})

const { state, connect, createCalendar, selectCalendar } = useAppleCalendar()

const email = ref('')
const password = ref('')
const newName = ref('Calnio')
const picked = ref('')
const error = ref('')

// Step 1 until credentials are stored, then step 2 until a calendar is picked.
const step = computed(() => (state.connection ? 2 : 1))

async function submitCredentials() {
  error.value = ''
  const { error: err } = await connect(email.value.trim(), password.value.trim())
  if (err) {
    error.value = err
    return
  }
  password.value = '' // no reason to keep it in memory once it is stored
  // Pre-select a calendar named Calnio if the account already has one.
  picked.value = state.calendars.find((c) => c.name === 'Calnio')?.url || ''
}

async function submitNewCalendar() {
  error.value = ''
  const { calendar, error: err } = await createCalendar(newName.value.trim())
  if (err) {
    error.value = err
    return
  }
  picked.value = calendar.url
}

async function submitCalendar() {
  error.value = ''
  const { error: err } = await selectCalendar(picked.value)
  if (err) error.value = err
}
</script>

<template>
  <div class="setup">
    <!-- Step 1: credentials --------------------------------------------->
    <section class="step">
      <div class="line">
        <span class="num" :class="{ done: step > 1 }">{{ numbers[0] }}</span>
        <h3>Connect your iCloud account</h3>
      </div>

      <div class="stepbody">
        <template v-if="step === 1">
          <!-- The short version, for a Connections row. The welcome page fills
               the slot with the full walkthrough instead of repeating this. -->
          <p v-if="!$slots.help" class="body">
            Apple requires an app-specific password, your normal Apple Account
            password will not work. Create one at
            <a href="https://account.apple.com" target="_blank" rel="noreferrer"
              >account.apple.com</a
            >
            under Sign-In and Security → App-Specific Passwords.
          </p>
          <slot name="help" />

          <form class="form" @submit.prevent="submitCredentials">
            <label class="field">
              <span>Apple Account email</span>
              <input
                v-model="email"
                type="email"
                required
                autocomplete="username"
                placeholder="you@icloud.com"
              />
            </label>

            <label class="field">
              <span>App-specific password</span>
              <!-- Plain text on purpose: an app-specific password is a
                   four-group string nobody can type blind, and a typo costs a
                   round trip to iCloud that rejects it. -->
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
              {{ state.busy ? 'Checking with iCloud…' : 'Connect' }}
            </button>
          </form>

          <p class="note">
            Calnio stores this password encrypted and uses it only to write events
            into the calendar you choose. Revoking it in your Apple Account
            settings disconnects Calnio immediately.
          </p>
        </template>

        <p v-else class="body">
          Connected as <strong>{{ state.connection.icloud_email }}</strong>
        </p>
      </div>
    </section>

    <!-- Step 2: calendar ------------------------------------------------>
    <section class="step" :class="{ ahead: step < 2 }">
      <div class="line">
        <span class="num">{{ numbers[1] }}</span>
        <h3>Choose a calendar</h3>
      </div>

      <div class="stepbody">
        <template v-if="step === 2">
          <p class="body">
            Calnio writes your Notion due dates here. A dedicated calendar is
            easiest to live with, you can hide it in the Calendar app without
            touching anything else.
          </p>

          <ul class="picklist">
            <li v-for="cal in state.calendars" :key="cal.url">
              <label>
                <input type="radio" :value="cal.url" v-model="picked" />
                <span>{{ cal.name }}</span>
              </label>
            </li>
          </ul>

          <div class="create">
            <input v-model="newName" class="text" type="text" placeholder="Calnio" />
            <button
              type="button"
              class="btn plain"
              :disabled="state.busy || !newName.trim()"
              @click="submitNewCalendar"
            >
              Create calendar
            </button>
          </div>

          <button
            class="btn"
            type="button"
            :disabled="state.busy || !picked"
            @click="submitCalendar"
          >
            {{ state.busy ? 'Saving…' : 'Use this calendar' }}
          </button>
        </template>

        <p v-else class="body">Available once your iCloud account is connected.</p>
      </div>
    </section>

    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<style scoped>
.setup {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-5);
}

.step {
  display: flex;
  flex-direction: column;
  gap: var(--app-gap-inline);
}

.step.ahead {
  opacity: 0.55;
}

.line {
  display: flex;
  align-items: center;
  gap: var(--app-gap-inline);
}

.num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--app-marker);
  height: var(--app-marker);
  border-radius: var(--app-radius-pill);
  border: 1px solid var(--app-border);
  background: var(--app-canvas-subtle);
  font-size: var(--app-text-meta);
  font-weight: var(--app-weight-bold);
  color: var(--app-fg-muted);
}

.num.done {
  background: var(--app-success-tint);
  border-color: var(--app-success-line);
  color: var(--app-success);
}

h3 {
  margin: 0;
  font-size: var(--app-text-body);
  font-weight: var(--app-weight-bold);
  color: var(--app-fg);
}

.stepbody {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--app-gap-stack);
  padding-left: calc(var(--app-marker) + var(--app-gap-inline));
}

.form {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--app-gap-block);
  width: 100%;
}

/* The name field and its button sit on one line and wrap together. */
.create {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--app-gap-inline);
}

.create .text {
  width: 200px; /* wide enough for a calendar name, narrow enough to stay on the row */
}
</style>
