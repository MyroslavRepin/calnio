<script setup>
import { computed, ref } from 'vue'
import { useAppleCalendar } from '../composables/useAppleCalendar'

// See NotionSetup: numbered 03/04 when the welcome page runs both wizards as one
// sequence, 01/02 when it stands alone in a Connections row.
defineProps({
  numbers: { type: Array, default: () => ['01', '02'] },
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
    <!-- Step 01 — credentials ------------------------------------------->
    <section class="step">
      <span class="num">{{ numbers[0] }}</span>
      <h3>Connect your iCloud account</h3>

      <template v-if="step === 1">
        <!-- The short version, for a Connections row. The welcome page fills
             the slot with the full walkthrough instead of repeating this. -->
        <p v-if="!$slots.help" class="body">
          Apple requires an app-specific password — your normal Apple Account
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
            <input
              v-model="password"
              type="password"
              required
              autocomplete="off"
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
    </section>

    <!-- Step 02 — calendar ---------------------------------------------->
    <section class="step" :class="{ ahead: step < 2 }">
      <span class="num">{{ numbers[1] }}</span>
      <h3>Choose a calendar</h3>

      <template v-if="step === 2">
        <p class="body">
          Calnio writes your Notion due dates here. A dedicated calendar is
          easiest to live with — you can hide it in the Calendar app without
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
            class="link-mono quiet"
            :disabled="state.busy || !newName.trim()"
            @click="submitNewCalendar"
          >
            <span>Create a new calendar</span>
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
    </section>

    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<style scoped>
.setup {
  display: flex;
  flex-direction: column;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
  padding: clamp(28px, 5vw, 40px) 0;
  border-top: 1px solid var(--hairline);
}

.step.ahead {
  opacity: 0.4;
}

.num {
  font-family: var(--font-mono);
  font-size: clamp(30px, 6vw, 40px);
  font-weight: 500;
  letter-spacing: -0.04em;
  line-height: 1;
  color: var(--accent, #0b63f6);
}

h3 {
  font-size: clamp(19px, 4.6vw, 21px);
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--ink);
}

.body {
  font-size: 15px;
  line-height: 1.6;
  color: var(--body);
  max-width: 52ch;
}

.body strong {
  font-weight: 500;
  color: var(--ink);
}

.body a {
  border-bottom: 1px solid var(--field-line);
  color: var(--ink);
}

.form {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 20px;
  width: 100%;
  padding: 8px 0;
}

.create {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px 24px;
}

.create .text {
  max-width: 220px;
}
</style>
