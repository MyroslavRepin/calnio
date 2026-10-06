<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import RunTable from '../../components/app/RunTable.vue'
import { useAdmin } from '../../composables/useAdmin'
import { grepCommand } from '../../format'

const route = useRoute()
const router = useRouter()

const adminResult = useAdmin()
const admin = adminResult.state
const loadRuns = adminResult.loadRuns

const error = ref(null)

// The filters live in the URL, so a link from a user or a sync page lands
// here already narrowed, and a filtered list can be bookmarked.
const filters = reactive({
  status: '',
  run_id: '',
  user_id: '',
  mapping_id: '',
})

// Copies the URL's filters into the form and loads the runs they describe.
async function load() {
  Object.keys(filters).forEach(function (name) {
    if (route.query[name]) {
      filters[name] = String(route.query[name])
    } else {
      filters[name] = ''
    }
  })

  error.value = null
  const result = await loadRuns({ ...filters })
  if (result.error) {
    error.value = result.error
  }
}

watch(
  function () {
    return route.query
  },
  load,
  { immediate: true },
)

// Puts the form's filters into the URL, which reloads through the watch.
function apply() {
  const query = {}
  Object.keys(filters).forEach(function (name) {
    if (filters[name].trim()) {
      query[name] = filters[name].trim()
    }
  })
  router.replace({ name: 'admin-runs', query: query })
}

function clear() {
  router.replace({ name: 'admin-runs' })
}

// A pass id is the one filter the log can answer too, so hand over the grep.
const grepForRun = computed(function () {
  if (route.query.run_id) {
    return grepCommand('run=' + route.query.run_id)
  } else {
    return null
  }
})

const runs = computed(function () {
  return admin.runs
})
</script>

<template>
  <header class="column page-head">
    <h1 class="title">Runs</h1>
    <p class="lead">
      Every run of every sync, newest first, 200 at a time. One run id covers
      every sync of one account in one pass.
    </p>
  </header>

  <section class="card">
    <div class="card-head">
      <h2>Filter</h2>
    </div>
    <form class="card-body column adminlist" @submit.prevent="apply">
      <div class="row filters">
        <label class="column field">
          <span>Status</span>
          <select v-model="filters.status">
            <option value="">Any</option>
            <option value="ok">ok</option>
            <option value="failed">Any failure</option>
            <option value="error">Failed</option>
            <option value="auth_error">Credentials rejected</option>
          </select>
        </label>
        <label class="column field">
          <span>Run id</span>
          <input v-model="filters.run_id" type="text" placeholder="c81e702b" />
        </label>
        <label class="column field">
          <span>Account id</span>
          <input v-model="filters.user_id" type="text" inputmode="numeric" />
        </label>
        <label class="column field">
          <span>Sync id</span>
          <input v-model="filters.mapping_id" type="text" inputmode="numeric" />
        </label>
      </div>
      <div class="actions">
        <button class="btn" type="submit">Show runs</button>
        <button class="btn plain" type="button" @click="clear">Clear filters</button>
      </div>
      <code v-if="grepForRun">{{ grepForRun }}</code>
    </form>
  </section>

  <section class="card">
    <div class="card-head">
      <h2>Runs</h2>
      <span v-if="runs" class="label neutral">{{ runs.length }}</span>
    </div>
    <div class="card-body">
      <p v-if="error" class="error">{{ error }}</p>
      <p v-else-if="!runs" class="loading">Loading…</p>
      <RunTable v-else :runs="runs" />
    </div>
  </section>
</template>
