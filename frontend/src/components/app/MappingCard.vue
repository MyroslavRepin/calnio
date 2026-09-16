<script setup>
import { computed, ref } from 'vue'
import { isReminderCalendar, useAppleCalendar } from '../../composables/useAppleCalendar'
import { useMappings } from '../../composables/useMappings'
import { useNotion } from '../../composables/useNotion'
import { formatDateTime } from '../../format'

// One sync: which database, which column, which calendar, and its own switch.
// The page owns the error box, so failures are reported upward.
const props = defineProps({
  mapping: { type: Object, required: true },
})

const emit = defineEmits(['error'])

const mappingsResult = useMappings()
const mappings = mappingsResult.state
const setDateProperty = mappingsResult.setDateProperty
const setCalendar = mappingsResult.setCalendar
const setEnabled = mappingsResult.setEnabled
const setWriteBack = mappingsResult.setWriteBack
const remove = mappingsResult.remove
const fetchDateProperties = mappingsResult.fetchDateProperties

const notionResult = useNotion()
const notion = notionResult.state

const appleResult = useAppleCalendar()
const apple = appleResult.state
const fetchCalendars = appleResult.fetchCalendars

// Which of the four views is showing: the plain facts, the column picker, the
// calendar picker, or the removal confirmation.
const editingColumn = ref(false)
const editingCalendar = ref(false)
const confirming = ref(false)

const pickedColumn = ref('')
const pickedCalendar = ref('')

// Prefer the stored database name, fall back to its id.
const databaseName = computed(function () {
  if (props.mapping.data_source_name) {
    return props.mapping.data_source_name
  } else {
    return props.mapping.data_source_id
  }
})

const columnName = computed(function () {
  if (props.mapping.due_date_property) {
    return props.mapping.due_date_property
  } else {
    return 'Not chosen'
  }
})

const calendarName = computed(function () {
  if (props.mapping.calendar_name) {
    return props.mapping.calendar_name
  }
  if (props.mapping.calendar_url) {
    return props.mapping.calendar_url
  }
  return 'Not chosen'
})

// Which way this sync runs, said in words rather than left to the switch.
const directionName = computed(function () {
  if (props.mapping.write_back) {
    return 'Both ways'
  } else {
    return 'Notion to Apple Calendar'
  }
})

// Whether Notion would accept a write at all. A grant given before Calnio
// asked for write access may only read, and reconnecting is the only fix.
const canWriteBack = computed(function () {
  if (notion.connection && notion.connection.can_write) {
    return true
  } else {
    return false
  }
})

const writeBackLabel = computed(function () {
  if (props.mapping.write_back) {
    return 'Calendar edits go back to Notion'
  } else {
    return 'Calendar edits stay in the calendar'
  }
})

const lastRun = computed(function () {
  return formatDateTime(props.mapping.last_run_at, 'never')
})

// The date columns for this sync, once they have been fetched.
const columns = computed(function () {
  const listed = mappings.dateProperties[props.mapping.id]
  if (listed) {
    return listed
  } else {
    return []
  }
})

// The header pill. It repeats what the rows already say, it never carries the
// meaning alone.
const statusLabel = computed(function () {
  if (!props.mapping.eligible) {
    return { text: 'Unfinished', tone: 'attention' }
  }
  if (!props.mapping.enabled) {
    return { text: 'Paused', tone: 'neutral' }
  }
  if (props.mapping.last_status === 'error') {
    return { text: 'Last run failed', tone: 'danger' }
  }
  if (props.mapping.last_status === 'auth_error') {
    return { text: 'Connection rejected', tone: 'danger' }
  }
  if (props.mapping.last_status === 'ok') {
    return { text: 'Syncing', tone: 'success' }
  }
  return { text: 'On, not run yet', tone: 'accent' }
})

// The calendar the user is about to save, so its name is available for the
// Reminders warning.
const pickedCalendarRow = computed(function () {
  return apple.calendars.find(function (calendar) {
    return calendar.url === pickedCalendar.value
  })
})

const isReminderPicked = computed(function () {
  return isReminderCalendar(pickedCalendarRow.value)
})

// Opens the column picker. The list is fetched now, not on page load, because
// it is a call out to Notion.
async function startColumn() {
  emit('error', null)

  const result = await fetchDateProperties(props.mapping.id)
  if (result.error) {
    emit('error', result.error)
    return
  }

  if (props.mapping.due_date_property) {
    pickedColumn.value = props.mapping.due_date_property
  } else {
    pickedColumn.value = ''
  }

  editingColumn.value = true
}

async function saveColumn() {
  emit('error', null)

  const result = await setDateProperty(props.mapping.id, pickedColumn.value)
  if (result.error) {
    emit('error', result.error)
    return
  }

  editingColumn.value = false
}

// Opens the calendar picker. iCloud is slow to answer, so the same rule applies.
async function startCalendar() {
  emit('error', null)

  const result = await fetchCalendars()
  if (result.error) {
    emit('error', result.error)
    return
  }

  if (props.mapping.calendar_url) {
    pickedCalendar.value = props.mapping.calendar_url
  } else {
    pickedCalendar.value = ''
  }

  editingCalendar.value = true
}

async function saveCalendar() {
  emit('error', null)

  const result = await setCalendar(props.mapping.id, pickedCalendar.value)
  if (result.error) {
    emit('error', result.error)
    return
  }

  editingCalendar.value = false
}

async function toggle() {
  emit('error', null)

  const result = await setEnabled(props.mapping.id, !props.mapping.enabled)
  if (result.error) {
    emit('error', result.error)
  }
}

async function toggleWriteBack() {
  emit('error', null)

  const result = await setWriteBack(props.mapping.id, !props.mapping.write_back)
  if (result.error) {
    emit('error', result.error)
  }
}

async function confirmRemove() {
  emit('error', null)

  const result = await remove(props.mapping.id)
  if (result.error) {
    emit('error', result.error)
  }

  confirming.value = false
}
</script>

<template>
  <section class="card">
    <div class="card-head">
      <h2>{{ databaseName }}</h2>
      <span class="label" :class="statusLabel.tone">{{ statusLabel.text }}</span>
    </div>

    <div class="card-body">
      <dl class="datarows">
        <div>
          <dt>Due date column</dt>
          <dd>{{ columnName }}</dd>
        </div>
        <div>
          <dt>Calendar</dt>
          <dd>{{ calendarName }}</dd>
        </div>
        <div>
          <dt>Direction</dt>
          <dd>{{ directionName }}</dd>
        </div>
        <div>
          <dt>Last run</dt>
          <dd>{{ lastRun }}</dd>
        </div>
      </dl>

      <template v-if="editingColumn">
        <ul v-if="columns.length" class="picklist">
          <li v-for="name in columns" :key="name">
            <label>
              <input type="radio" :value="name" v-model="pickedColumn" />
              <span>{{ name }}</span>
            </label>
          </li>
        </ul>

        <p v-else class="body">
          This database has no date columns, so there is nothing to sync. Add one
          in Notion, then try again.
        </p>

        <div class="row actions">
          <button
            v-if="columns.length"
            class="btn"
            type="button"
            :disabled="mappings.busy || !pickedColumn"
            @click="saveColumn"
          >
            {{ mappings.busy ? 'Saving…' : 'Save' }}
          </button>
          <button class="btn plain" type="button" @click="editingColumn = false">Cancel</button>
        </div>
      </template>

      <template v-else-if="editingCalendar">
        <ul class="picklist">
          <li v-for="cal in apple.calendars" :key="cal.url">
            <label>
              <input type="radio" :value="cal.url" v-model="pickedCalendar" />
              <span>{{ cal.name }}</span>
              <span v-if="isReminderCalendar(cal)" class="label attention">Reminders</span>
            </label>
          </li>
        </ul>

        <p v-if="isReminderPicked" class="error">
          {{ pickedCalendarRow.name }} is a Reminders list, not a calendar. Pick a
          calendar instead.
        </p>

        <div class="row actions">
          <button
            class="btn"
            type="button"
            :disabled="mappings.busy || !pickedCalendar || isReminderPicked"
            @click="saveCalendar"
          >
            {{ mappings.busy ? 'Saving…' : 'Save' }}
          </button>
          <button class="btn plain" type="button" @click="editingCalendar = false">Cancel</button>
        </div>
      </template>

      <template v-else-if="confirming">
        <p class="body">
          Removing this sync deletes the events it wrote into
          <strong>{{ calendarName }}</strong>. Your Notion database is not
          touched, and your other syncs keep running.
        </p>
        <div class="row actions">
          <button class="btn danger" type="button" :disabled="mappings.busy" @click="confirmRemove">
            {{ mappings.busy ? 'Removing…' : 'Remove sync' }}
          </button>
          <button class="btn plain" type="button" @click="confirming = false">Cancel</button>
        </div>
      </template>

      <template v-else>
        <button
          class="switch"
          type="button"
          role="switch"
          :aria-checked="mapping.enabled"
          :disabled="!mapping.eligible || mappings.busy"
          @click="toggle"
        >
          <span class="track" :class="{ on: mapping.enabled }"><span class="knob"></span></span>
          <span class="switchlabel">
            {{ mapping.enabled ? 'This sync is on' : 'This sync is off' }}
          </span>
        </button>

        <p v-if="!mapping.eligible" class="note">
          Choose a date column and a calendar before turning this sync on.
        </p>

        <button
          class="switch"
          type="button"
          role="switch"
          :aria-checked="mapping.write_back"
          :disabled="!mapping.eligible || !canWriteBack || mappings.busy"
          @click="toggleWriteBack"
        >
          <span class="track" :class="{ on: mapping.write_back }"><span class="knob"></span></span>
          <span class="switchlabel">{{ writeBackLabel }}</span>
        </button>

        <p v-if="!canWriteBack" class="note">
          Calnio may only read your workspace. Reconnect Notion on the
          <router-link :to="{ name: 'connections' }">Connections</router-link>
          page to let calendar edits go back to it.
        </p>

        <p v-else-if="mapping.write_back" class="note">
          Moving, renaming or deleting one of these events in Apple Calendar
          changes the Notion page too. New events you make in that calendar
          become new pages. Notion wins when both sides changed at once.
        </p>

        <div class="row actions">
          <button class="btn plain" type="button" :disabled="mappings.busy" @click="startColumn">
            {{ mapping.due_date_property ? 'Change column' : 'Choose column' }}
          </button>
          <button class="btn plain" type="button" :disabled="apple.busy" @click="startCalendar">
            {{ mapping.calendar_url ? 'Change calendar' : 'Choose calendar' }}
          </button>
          <button class="btn plain" type="button" @click="confirming = true">Remove</button>
        </div>
      </template>
    </div>
  </section>
</template>

<style scoped>
.card-body > * + * {
  margin-top: var(--app-gap-stack);
}
</style>
