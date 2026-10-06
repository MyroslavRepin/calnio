<script setup>
import { computed, onMounted, ref } from 'vue'
import { useAdmin } from '../../composables/useAdmin'
import { formatDateTime } from '../../format'

const adminResult = useAdmin()
const admin = adminResult.state
const loadProblems = adminResult.loadProblems

const error = ref(null)
const busy = ref(false)
const level = ref('ERROR')
const search = ref('')

// Reads the log again. Also what the Reload button does, since a crash that
// just happened is the reason to be on this page.
async function reload() {
  busy.value = true
  error.value = null
  const result = await loadProblems()
  busy.value = false
  if (result.error) {
    error.value = result.error
  }
}

onMounted(reload)

// Whether a record is of the level chosen. CRITICAL counts as an error.
function passesLevel(record) {
  if (level.value === 'ERROR') {
    return record.level === 'ERROR' || record.level === 'CRITICAL'
  }
  if (level.value === 'WARNING') {
    return record.level === 'WARNING'
  }
  return true
}

// Whether a record matches the search, anywhere in its text.
function matchesSearch(record) {
  const term = search.value.trim().toLowerCase()
  if (!term) {
    return true
  }
  const words = [record.message, record.location, record.error_type, record.run_id]
  return words.some(function (word) {
    if (!word) {
      return false
    }
    return word.toLowerCase().includes(term)
  })
}

const groups = computed(function () {
  if (!admin.problems) {
    return []
  }
  return admin.problems.groups.filter(function (group) {
    return passesLevel(group) && matchesSearch(group)
  })
})

const entries = computed(function () {
  if (!admin.problems) {
    return []
  }
  return admin.problems.entries.filter(function (entry) {
    return passesLevel(entry) && matchesSearch(entry)
  })
})

// Clicking a group narrows the list below to the line of code it came from.
function showGroup(group) {
  search.value = group.location
}

// Errors are danger, warnings are attention, anything else is plain.
function levelTone(name) {
  if (name === 'ERROR' || name === 'CRITICAL') {
    return 'danger'
  }
  if (name === 'WARNING') {
    return 'attention'
  }
  return 'neutral'
}

function whenLabel(value) {
  return formatDateTime(value, 'unknown')
}
</script>

<template>
  <header class="column page-head">
    <h1 class="title">Errors</h1>
    <p class="lead">
      Every warning and error loguru wrote, from any part of the app: sync
      failures, crashed requests, the scheduler, Telegram. Newest first.
    </p>
  </header>

  <section class="card">
    <div class="card-head">
      <h2>Filter</h2>
      <button class="btn plain" type="button" :disabled="busy" @click="reload">
        {{ busy ? 'Reading…' : 'Reload' }}
      </button>
    </div>
    <div class="card-body row filters">
      <label class="column field">
        <span>Level</span>
        <select v-model="level">
          <option value="ERROR">Errors</option>
          <option value="WARNING">Warnings</option>
          <option value="ALL">Both</option>
        </select>
      </label>
      <label class="column field">
        <span>Search</span>
        <input v-model="search" type="search" placeholder="Message, code location, run id" />
      </label>
    </div>
  </section>

  <p v-if="error" class="error">{{ error }}</p>
  <p v-else-if="!admin.problems" class="loading">Loading…</p>

  <template v-else>
    <!-- One row per line of code that complained, the noisiest first. -->
    <section class="card">
      <div class="card-head">
        <h2>By origin</h2>
        <span class="label neutral">{{ groups.length }}</span>
      </div>
      <div class="card-body">
        <p v-if="!groups.length" class="note">Nothing logged at this level.</p>
        <div v-else class="tablebox">
          <table class="datatable">
            <thead>
              <tr>
                <th>Count</th>
                <th>Level</th>
                <th>Where</th>
                <th>Latest message</th>
                <th>Last seen</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="group in groups" :key="group.level + group.location">
                <td>{{ group.count }}</td>
                <td>
                  <span class="label" :class="levelTone(group.level)">{{ group.level }}</span>
                </td>
                <td>
                  <button class="linkbutton" type="button" @click="showGroup(group)">
                    <code>{{ group.location }}</code>
                  </button>
                </td>
                <td class="message">
                  <strong v-if="group.error_type">{{ group.error_type }}: </strong>
                  {{ group.message }}
                </td>
                <td>{{ whenLabel(group.last_time) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- Each record on its own, with the ids that lead to the rest of the story. -->
    <section class="card">
      <div class="card-head">
        <h2>Latest</h2>
        <span class="label neutral">{{ entries.length }}</span>
      </div>
      <div class="card-body column entries">
        <p v-if="!entries.length" class="note">Nothing logged at this level.</p>

        <article v-for="(entry, index) in entries" :key="index" class="column entry">
          <div class="row entryhead">
            <span class="label" :class="levelTone(entry.level)">{{ entry.level }}</span>
            <span class="note">{{ whenLabel(entry.time) }}</span>
            <code>{{ entry.location }}</code>
          </div>

          <p class="entrymessage">
            <strong v-if="entry.error_type">{{ entry.error_type }}: </strong>
            {{ entry.message }}
          </p>

          <div v-if="entry.run_id || entry.user_id || entry.mapping_id" class="row entryids">
            <router-link
              v-if="entry.run_id"
              :to="{ name: 'admin-runs', query: { run_id: entry.run_id } }"
            >
              run <code>{{ entry.run_id }}</code>
            </router-link>
            <router-link
              v-if="entry.user_id"
              :to="{ name: 'admin-user', query: { id: entry.user_id } }"
            >
              account <span class="ident">#{{ entry.user_id }}</span>
            </router-link>
            <router-link
              v-if="entry.mapping_id"
              :to="{ name: 'admin-sync', query: { id: entry.mapping_id } }"
            >
              sync <span class="ident">#{{ entry.mapping_id }}</span>
            </router-link>
          </div>

          <details v-if="entry.traceback">
            <summary>Traceback</summary>
            <pre class="traceback">{{ entry.traceback }}</pre>
          </details>
        </article>
      </div>
    </section>
  </template>
</template>

<style scoped>
.message {
  min-width: 280px;
  max-width: 480px;
  white-space: normal;
  overflow-wrap: anywhere;
}

/* A code location that filters the list, styled as the text it is. */
.linkbutton {
  padding: 0;
  border: none;
  background: none;
  cursor: pointer;
}

.entries {
  --gap: var(--app-gap-block);
}

.entry {
  --gap: var(--app-space-2);
  padding-bottom: var(--app-gap-block);
  border-bottom: 1px solid var(--app-border-subtle);
}

.entry:last-child {
  padding-bottom: 0;
  border-bottom: none;
}

.entryhead,
.entryids {
  --gap: var(--app-gap-inline);
}

.entrymessage {
  font-size: var(--app-text-body);
  color: var(--app-fg);
  overflow-wrap: anywhere;
  white-space: pre-wrap;
}

summary {
  font-size: var(--app-text-meta);
  color: var(--app-fg-muted);
  cursor: pointer;
}

.traceback {
  margin-top: var(--app-space-2);
  padding: var(--app-space-3);
  overflow-x: auto;
  font-family: var(--app-font-mono);
  font-size: var(--app-text-meta);
  line-height: var(--app-lh-body);
  color: var(--app-fg);
  background: var(--app-canvas-subtle);
  border: 1px solid var(--app-border-subtle);
  border-radius: var(--app-radius-sm);
}
</style>
