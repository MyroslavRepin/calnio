<script setup>
import { computed, ref, watch } from 'vue'
import { useNotion } from '../../composables/useNotion'

// The step numbers are a prop so the welcome page can run this and the Apple
// wizard as one 1 to 4 sequence. Inside a Connections row each wizard stands
// alone, so the default is its own 1 and 2.
defineProps({
  numbers: {
    type: Array,
    default: function () {
      return ['1', '2']
    },
  },
})

// Everything this wizard does goes through the Notion composable.
const notionResult = useNotion()
const state = notionResult.state
const connect = notionResult.connect
const fetchDatabases = notionResult.fetchDatabases
const selectDatabase = notionResult.selectDatabase

const picked = ref('')
const error = ref('')
const fetched = ref(false)

// Step 1 until Notion grants us the workspace, step 2 until a database is
// picked.
const step = computed(function () {
  if (state.connection) {
    return 2
  } else {
    return 1
  }
})

// Sharing the grant with zero databases is the likeliest first-run mistake,
// because Notion's dialog lets you finish without ticking anything.
const empty = computed(function () {
  if (fetched.value && state.databases.length === 0) {
    return true
  } else {
    return false
  }
})

// The error to show: the one from this wizard, otherwise the one the OAuth
// callback left behind.
const message = computed(function () {
  if (error.value) {
    return error.value
  } else {
    return state.error
  }
})

// The user arrives here straight off the OAuth callback, so the database list
// is fetched as soon as step 2 appears rather than on mount.
watch(step, async function (value) {
  if (value !== 2 || fetched.value) {
    return
  }

  const result = await fetchDatabases()
  if (result.error) {
    error.value = result.error
    return
  }

  fetched.value = true

  if (state.connection.data_source_id) {
    picked.value = state.connection.data_source_id
  } else {
    picked.value = ''
  }
}, { immediate: true })

async function startConnect() {
  error.value = ''

  const result = await connect()
  if (result.error) {
    error.value = result.error
  }
}

async function submitDatabase() {
  error.value = ''

  const result = await selectDatabase(picked.value)
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
        <h3>Authorize Calnio in your Notion workspace</h3>
      </div>

      <div class="column stepbody">
        <template v-if="step === 1">
          <p class="body">
            Notion asks which pages Calnio may read. Tick the database that holds
            your tasks. Calnio cannot see anything you do not share, and it only
            ever reads.
          </p>

          <button class="btn" type="button" :disabled="state.busy" @click="startConnect">
            {{ state.busy ? 'Opening Notion…' : 'Connect Notion' }}
          </button>

          <p class="note">
            You can revoke this at any time, from Notion's settings or from here.
          </p>
        </template>

        <p v-else class="body">
          Connected to
          <strong>{{ state.connection.workspace_name || 'your workspace' }}</strong>
        </p>
      </div>
    </section>

    <section class="column step" :class="{ ahead: step < 2 }">
      <div class="row stephead">
        <span class="num">{{ numbers[1] }}</span>
        <h3>Choose the database with your tasks</h3>
      </div>

      <div class="column stepbody">
        <template v-if="step === 2">
          <p v-if="state.busy && !fetched" class="body">Loading your databases…</p>

          <template v-else-if="empty">
            <p class="body">
              Calnio can see this workspace, but no databases were shared with it.
              Re-open Notion's dialog and tick the database that holds your tasks.
            </p>
            <button class="btn" type="button" :disabled="state.busy" @click="startConnect">
              {{ state.busy ? 'Opening Notion…' : "Re-open Notion's picker" }}
            </button>
          </template>

          <template v-else>
            <p class="body">
              Calnio reads due dates from here. Only the databases you shared are
              listed.
            </p>

            <ul class="picklist">
              <li v-for="db in state.databases" :key="db.id">
                <label>
                  <input type="radio" :value="db.id" v-model="picked" />
                  <span>{{ db.title || 'Untitled' }}</span>
                </label>
              </li>
            </ul>

            <button
              class="btn"
              type="button"
              :disabled="state.busy || !picked"
              @click="submitDatabase"
            >
              {{ state.busy ? 'Saving…' : 'Use this database' }}
            </button>
          </template>
        </template>

        <p v-else class="body">Available once your workspace is connected.</p>
      </div>
    </section>

    <p v-if="message" class="error">{{ message }}</p>
  </div>
</template>
