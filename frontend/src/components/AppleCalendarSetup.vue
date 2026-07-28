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
    <section class="step" :class="{ past: step > 1 }">
      <p class="num">{{ numbers[0] }}</p>
      <div class="body">
        <h3>Connect your iCloud account</h3>

        <template v-if="step === 1">
          <!-- The short version, for a Connections row. The welcome page fills
               the slot with the full walkthrough instead of repeating this. -->
          <p v-if="!$slots.help" class="lede">
            Apple requires an app-specific password — your normal Apple ID password
            will not work. Create one at
            <a href="https://account.apple.com" target="_blank" rel="noreferrer"
              >account.apple.com</a
            >
            under Sign-In and Security → App-Specific Passwords.
          </p>
          <slot name="help" />

          <form class="form" @submit.prevent="submitCredentials">
            <label>
              <span class="label">Apple ID email</span>
              <input
                v-model="email"
                type="email"
                required
                autocomplete="username"
                placeholder="you@icloud.com"
              />
            </label>

            <label>
              <span class="label">App-specific password</span>
              <input
                v-model="password"
                type="password"
                required
                autocomplete="off"
                placeholder="xxxx-xxxx-xxxx-xxxx"
              />
            </label>

            <button class="btn-primary" type="submit" :disabled="state.busy">
              {{ state.busy ? 'Checking with iCloud…' : 'Connect' }}
            </button>
          </form>

          <p class="note">
            Calnio stores this password encrypted and uses it only to write events
            into the calendar you choose. You can revoke it at any time from your
            Apple ID settings, which disconnects Calnio immediately.
          </p>
        </template>

        <p v-else class="done-line">
          Connected as <strong>{{ state.connection.icloud_email }}</strong>
        </p>
      </div>
    </section>

    <!-- Step 02 — calendar ---------------------------------------------->
    <section class="step" :class="{ ahead: step < 2 }">
      <p class="num">{{ numbers[1] }}</p>
      <div class="body">
        <h3>Choose a calendar</h3>

        <template v-if="step === 2">
          <p class="lede">
            Calnio writes your Notion due dates here. A dedicated calendar is
            easiest to live with — you can hide it in the Calendar app without
            touching anything else.
          </p>

          <ul class="calendars">
            <li v-for="cal in state.calendars" :key="cal.url">
              <label>
                <input type="radio" :value="cal.url" v-model="picked" />
                <span>{{ cal.name }}</span>
              </label>
            </li>
          </ul>

          <div class="create">
            <input v-model="newName" type="text" placeholder="Calnio" />
            <button
              type="button"
              class="linkbtn"
              :disabled="state.busy || !newName.trim()"
              @click="submitNewCalendar"
            >
              Create a new calendar
            </button>
          </div>

          <button
            class="btn-primary"
            type="button"
            :disabled="state.busy || !picked"
            @click="submitCalendar"
          >
            {{ state.busy ? 'Saving…' : 'Use this calendar' }}
          </button>
        </template>
      </div>
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
  display: grid;
  grid-template-columns: 64px 1fr;
  gap: 24px;
  padding: 40px 0;
  border-top: 1px solid var(--hairline);
}

.step.ahead {
  opacity: 0.4;
}

.num {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.16em;
  color: var(--muted);
  padding-top: 4px;
}

.body {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 520px;
}

h3 {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.01em;
}

.lede,
.note,
.done-line {
  font-size: 15px;
  line-height: 1.6;
  color: var(--body);
}

.note {
  font-size: 13px;
  color: var(--muted);
}

.done-line strong {
  font-weight: 500;
  color: var(--ink);
}

a {
  border-bottom: 1px solid var(--hairline);
}

.form {
  display: flex;
  flex-direction: column;
  gap: 20px;
  align-items: flex-start;
}

label {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.label {
  font-family: var(--font-mono);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: var(--muted);
}

input[type='email'],
input[type='password'],
input[type='text'] {
  font-family: var(--font-ui);
  font-size: 15px;
  color: var(--ink);
  background: none;
  border: none;
  border-bottom: 1px solid var(--frame);
  border-radius: 0;
  padding: 8px 0;
  width: 100%;
}

input:focus {
  outline: none;
  border-bottom-color: var(--ink);
}

.calendars {
  list-style: none;
  margin: 0;
  padding: 0;
  border-top: 1px solid var(--hairline);
}

.calendars li {
  border-bottom: 1px solid var(--hairline);
}

.calendars label {
  flex-direction: row;
  align-items: center;
  gap: 12px;
  padding: 14px 0;
  font-size: 15px;
  cursor: pointer;
}

.create {
  display: flex;
  align-items: baseline;
  gap: 16px;
}

.create input {
  max-width: 200px;
}

.linkbtn {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--muted);
  background: none;
  border: none;
  border-bottom: 1px solid var(--hairline);
  padding: 0 0 2px;
  cursor: pointer;
  white-space: nowrap;
}

.btn-primary:disabled,
.linkbtn:disabled {
  opacity: 0.4;
  cursor: default;
}

.error {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--ink);
  border-top: 1px solid var(--hairline);
  padding-top: 20px;
}
</style>
