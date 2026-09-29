<script setup>
import { computed, ref } from 'vue'
import { useMappings } from '../../composables/useMappings'
import { useNotion } from '../../composables/useNotion'

// Tick the databases, press one button, done. The server infers each date column
// and gives each database its own calendar, so this is the whole setup. Anything
// it guessed wrong is changed on the sync's own card afterwards. No card of its
// own: the setup page puts this inside a step, the Syncs page inside a card.
const emit = defineEmits(['error', 'added'])

const notionResult = useNotion()
const notion = notionResult.state
const connect = notionResult.connect
const fetchDatabases = notionResult.fetchDatabases

const mappingsResult = useMappings()
const mappings = mappingsResult.state
const create = mappingsResult.create

const fetched = ref(false)
const loading = ref(false)
const ticked = ref([])

// Only databases that are not already syncing. A database maps to one calendar,
// so offering it twice would just earn a 409.
const available = computed(function () {
  const taken = mappings.list.map(function (mapping) {
    return mapping.data_source_id
  })

  return notion.databases.filter(function (database) {
    return !taken.includes(database.id)
  })
})

// Every shared database is already syncing, which is a finished state rather
// than an error.
const allTaken = computed(function () {
  if (!fetched.value) {
    return false
  }
  if (notion.databases.length === 0) {
    return false
  }
  return available.value.length === 0
})

// Sharing the grant with zero databases is the likeliest first-run mistake,
// because Notion's dialog lets you finish without ticking anything.
const noneShared = computed(function () {
  if (fetched.value && notion.databases.length === 0) {
    return true
  }
  return false
})

// Said out loud before the button is pressed, because it writes to the user's
// iCloud account and a surprise calendar is worse than an extra sentence.
const calendarNote = computed(function () {
  if (ticked.value.length === 0) {
    return ''
  }
  if (ticked.value.length === 1) {
    return 'Calnio will use an Apple calendar of the same name, or create it.'
  }
  return (
    'Calnio will use ' +
    ticked.value.length +
    ' Apple calendars of the same names, creating any that do not exist yet.'
  )
})

// One Notion call, and the component exists to show its result, so it runs on
// mount rather than behind a button.
async function loadDatabases() {
  emit('error', null)
  loading.value = true

  const result = await fetchDatabases()
  loading.value = false

  if (result.error) {
    emit('error', result.error)
    return
  }

  fetched.value = true
}

loadDatabases()

async function submit() {
  emit('error', null)

  const result = await create(ticked.value)
  if (result.error) {
    emit('error', result.error)
    return
  }

  ticked.value = []
  emit('added', result.mappings)
}

// Sends the user back to Notion's picker so they can tick more databases.
async function shareMore() {
  emit('error', null)

  const result = await connect()
  if (result.error) {
    emit('error', result.error)
  }
}
</script>

<template>
  <div class="column addsync">
    <p v-if="loading && !fetched" class="loading">Reading your Notion databases…</p>

    <template v-else-if="noneShared">
      <p class="body">
        Calnio can see your workspace, but no databases were shared with it.
        Notion's dialog lets you finish without ticking anything, which is the
        usual cause. Open it again and tick the ones you want in your calendar.
      </p>
      <div class="row actions">
        <button class="btn" type="button" :disabled="notion.busy" @click="shareMore">
          Share databases
        </button>
      </div>
    </template>

    <template v-else-if="allTaken">
      <p class="body">
        Every database you shared is already syncing. Share another one in Notion
        to add more.
      </p>
      <div class="row actions">
        <button class="btn plain" type="button" :disabled="notion.busy" @click="shareMore">
          Share more databases
        </button>
        <button class="btn plain" type="button" :disabled="loading" @click="loadDatabases">
          Refresh
        </button>
      </div>
    </template>

    <template v-else>
      <p class="body">
        Tick the databases you want in Apple Calendar. Each one gets its own
        calendar, so you can colour and hide them separately.
      </p>

      <ul class="picklist">
        <li v-for="db in available" :key="db.id">
          <label>
            <input type="checkbox" :value="db.id" v-model="ticked" />
            <span>{{ db.title || 'Untitled' }}</span>
          </label>
        </li>
      </ul>

      <p v-if="calendarNote" class="note">{{ calendarNote }}</p>

      <div class="row actions">
        <button
          class="btn"
          type="button"
          :disabled="mappings.busy || ticked.length === 0"
          @click="submit"
        >
          {{ mappings.busy ? 'Setting up…' : 'Start syncing' }}
        </button>
        <button class="btn plain" type="button" :disabled="notion.busy" @click="shareMore">
          Share more databases
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.addsync {
  --gap: var(--app-gap-stack);
  align-items: flex-start;
  width: 100%;
}
</style>
