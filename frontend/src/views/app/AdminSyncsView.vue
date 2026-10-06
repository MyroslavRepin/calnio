<script setup>
import { computed, onMounted, ref } from 'vue'
import SyncTable from '../../components/app/SyncTable.vue'
import { useAdmin } from '../../composables/useAdmin'

const adminResult = useAdmin()
const admin = adminResult.state
const loadSyncs = adminResult.loadSyncs

const error = ref(null)
const search = ref('')
const show = ref('all')

onMounted(async function () {
  const result = await loadSyncs()
  if (result.error) {
    error.value = result.error
  }
})

// Whether one sync passes the chosen filter.
function passesFilter(sync) {
  if (show.value === 'failing') {
    return sync.last_status === 'error' || sync.last_status === 'auth_error'
  }
  if (show.value === 'on') {
    return sync.enabled && sync.eligible
  }
  if (show.value === 'off') {
    return !sync.enabled
  }
  if (show.value === 'twoway') {
    return sync.two_way
  }
  if (show.value === 'unfinished') {
    return !sync.eligible
  }
  return true
}

// Whether one sync matches the search: its id, its owner's id or email, its
// database or its calendar.
function matchesSearch(sync) {
  const term = search.value.trim().toLowerCase()
  if (!term) {
    return true
  }
  if (String(sync.id) === term || String(sync.user_id) === term) {
    return true
  }
  const words = [sync.email, sync.database, sync.calendar]
  return words.some(function (word) {
    if (!word) {
      return false
    }
    return word.toLowerCase().includes(term)
  })
}

// The syncs on screen, newest first.
const syncs = computed(function () {
  if (!admin.syncs) {
    return []
  }
  const matching = admin.syncs.filter(function (sync) {
    return passesFilter(sync) && matchesSearch(sync)
  })
  return matching.slice().reverse()
})
</script>

<template>
  <p v-if="error" class="error">{{ error }}</p>
  <p v-else-if="!admin.syncs" class="loading">Loading…</p>

  <template v-else>
    <header class="column page-head">
      <h1 class="title">Syncs</h1>
      <p class="lead">Every sync of every account, newest first.</p>
    </header>

    <section class="card">
      <div class="card-head">
        <h2>Syncs</h2>
        <span class="label neutral">{{ syncs.length }} of {{ admin.syncs.length }}</span>
      </div>
      <div class="card-body column adminlist">
        <div class="row filters">
          <label class="column field">
            <span>Search</span>
            <input v-model="search" type="search" placeholder="Id, email, database or calendar" />
          </label>
          <label class="column field">
            <span>Show</span>
            <select v-model="show">
              <option value="all">Every sync</option>
              <option value="failing">Failing</option>
              <option value="on">On and configured</option>
              <option value="off">Switched off</option>
              <option value="twoway">Two-way</option>
              <option value="unfinished">Unfinished</option>
            </select>
          </label>
        </div>

        <SyncTable :syncs="syncs" />
      </div>
    </section>
  </template>
</template>
