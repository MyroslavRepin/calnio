<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useNotion } from '../../composables/useNotion'
import { useSync } from '../../composables/useSync'

// The page owns the error box, so failures are reported upward rather than
// drawn inside this card.
const emit = defineEmits(['error'])

const notionResult = useNotion()
const notion = notionResult.state

const syncResult = useSync()
const state = syncResult.state
const fetchDateProperties = syncResult.fetchDateProperties
const setDueDateProperty = syncResult.setDueDateProperty

const hasDatabase = computed(function () {
  return Boolean(notion.connection?.data_source_id)
})

// The value the dropdown shows. Starts from whatever is already saved, so a
// reload does not blank the control while the fresh list is still loading.
const picked = ref('')

watch(
  function () {
    return state.settings?.due_date_property
  },
  function (value) {
    picked.value = value || ''
  },
  { immediate: true },
)

// The options come from Notion, so they are fetched once the database is known
// rather than on every visit. The shell has usually loaded the connection by
// the time this mounts; the watch covers a hard refresh, where the connection
// lands a moment later.
async function loadProperties() {
  if (!hasDatabase.value || state.dateProperties.length) {
    return
  }

  const result = await fetchDateProperties()
  if (result.error) {
    emit('error', result.error)
  }
}

onMounted(loadProperties)
watch(hasDatabase, loadProperties)

// Re-pulls the column list from Notion, for a column added or renamed there
// since the page loaded.
async function refresh() {
  emit('error', null)

  const result = await fetchDateProperties()
  if (result.error) {
    emit('error', result.error)
  }
}

async function choose() {
  emit('error', null)

  const result = await setDueDateProperty(picked.value)
  if (result.error) {
    emit('error', result.error)
  }
}
</script>

<template>
  <section class="card">
    <div class="card-head">
      <h2>Due date column</h2>
    </div>

    <div class="card-body">
      <p class="body">
        The Notion date property Calnio reads. Only date columns can be chosen,
        every page with a value there becomes an event.
      </p>

      <p v-if="!hasDatabase" class="note">
        Pick a Notion database first.
        <router-link :to="{ name: 'connections' }">Connections</router-link>
      </p>

      <p v-else-if="state.busy && !state.dateProperties.length" class="note">
        Reading your database…
      </p>

      <p v-else-if="!state.dateProperties.length" class="note">
        This database has no date columns, so there is nothing to sync. Add one
        in Notion, then refresh.
      </p>

      <label v-else class="column field">
        <span>Due date column</span>
        <select v-model="picked" :disabled="state.busy" @change="choose">
          <option value="" disabled>Choose a column</option>
          <option v-for="name in state.dateProperties" :key="name" :value="name">
            {{ name }}
          </option>
        </select>
      </label>

      <div v-if="hasDatabase" class="row actions">
        <button class="btn plain" type="button" :disabled="state.busy" @click="refresh">
          {{ state.busy ? 'Reading…' : 'Refresh columns' }}
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.card-body > * + * {
  margin-top: var(--app-gap-stack);
}
</style>
