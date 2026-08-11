<script setup>
import { computed, ref } from 'vue'
import { isReminderCalendar, useAppleCalendar } from '../../composables/useAppleCalendar'

// See NotionSetup: numbered 3 and 4 when the welcome page runs both wizards as
// one sequence, 1 and 2 when it stands alone in a Connections row.
defineProps({
  numbers: {
    type: Array,
    default: function () {
      return ['1', '2']
    },
  },
})

// Everything this wizard does goes through the Apple Calendar composable.
const appleResult = useAppleCalendar()
const state = appleResult.state
const connect = appleResult.connect
const createCalendar = appleResult.createCalendar
const selectCalendar = appleResult.selectCalendar

const email = ref('')
const password = ref('')
const newName = ref('Calnio')
const picked = ref('')
const error = ref('')

// Step 1 until the credentials are stored, step 2 until a calendar is picked.
const step = computed(function () {
  if (state.connection) {
    return 2
  } else {
    return 1
  }
})

// The chosen calendar's full row, looked up by url, so its name is available.
const pickedCalendar = computed(function () {
  return state.calendars.find(function (calendar) {
    return calendar.url === picked.value
  })
})

// Blocks saving a calendar that is really iCloud's Reminders list.
const isReminderPicked = computed(function () {
  return isReminderCalendar(pickedCalendar.value)
})

async function submitCredentials() {
  error.value = ''

  const result = await connect(email.value.trim(), password.value.trim())
  if (result.error) {
    error.value = result.error
    return
  }

  password.value = '' // no reason to keep it in memory once it is stored

  // Pre-select a calendar named Calnio if the account already has one.
  const existing = state.calendars.find(function (calendar) {
    return calendar.name === 'Calnio'
  })

  if (existing) {
    picked.value = existing.url
  } else {
    picked.value = ''
  }
}

async function submitNewCalendar() {
  error.value = ''

  const result = await createCalendar(newName.value.trim())
  if (result.error) {
    error.value = result.error
    return
  }

  picked.value = result.calendar.url
}

async function submitCalendar() {
  error.value = ''

  const result = await selectCalendar(picked.value)
  if (result.error) {
    error.value = result.error
  }
}
</script>

<template>
  <div class="column setup">
    <section class="column step">
      <div class="row stephead">
        <span class="num" :class="{ done: step > 1 }">{{ numbers[0] }}</span>
        <h3>Connect your iCloud account</h3>
      </div>

      <div class="column stepbody">
        <template v-if="step === 1">
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
            into the calendar you choose. Revoking it in your Apple Account
            settings disconnects Calnio immediately.
          </p>
        </template>

        <p v-else class="body">
          Connected as <strong>{{ state.connection.icloud_email }}</strong>
        </p>
      </div>
    </section>

    <section class="column step" :class="{ ahead: step < 2 }">
      <div class="row stephead">
        <span class="num">{{ numbers[1] }}</span>
        <h3>Choose a calendar</h3>
      </div>

      <div class="column stepbody">
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
                <span v-if="isReminderCalendar(cal)" class="label attention">Reminders</span>
              </label>
            </li>
          </ul>

          <p v-if="isReminderPicked" class="error">
            {{ pickedCalendar.name }} is a Reminders list, not a calendar. Pick a
            calendar instead.
          </p>

          <div class="row newcalendar">
            <input v-model="newName" class="text" type="text" placeholder="Calnio" />
            <button type="button" class="btn plain" :disabled="state.busy || !newName.trim()"
              @click="submitNewCalendar">
              Create calendar
            </button>
          </div>

          <button class="btn" type="button" :disabled="state.busy || !picked || isReminderPicked"
            @click="submitCalendar">
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
.credentials {
  --gap: var(--app-gap-block);
  align-items: flex-start;
  width: 100%;
}

.newcalendar {
  --gap: var(--app-gap-inline);
}

.newcalendar .text {
  width: 200px;
  /* wide enough for a calendar name, narrow enough to stay on the row */
}
</style>
