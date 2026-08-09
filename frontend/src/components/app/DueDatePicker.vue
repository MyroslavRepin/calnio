<script setup>
import { computed, onMounted, watch } from 'vue'
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

async function choose(name) {
  emit('error', null)

  const result = await setDueDateProperty(name)
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
        in Notion, then reload this page.
      </p>

      <ul v-else class="picklist">
        <li v-for="name in state.dateProperties" :key="name">
          <label>
            <input
              type="radio"
              name="due-date-property"
              :value="name"
              :checked="state.settings?.due_date_property === name"
              :disabled="state.busy"
              @change="choose(name)"
            />
            <span>{{ name }}</span>
          </label>
        </li>
      </ul>
    </div>
  </section>
</template>

<style scoped>
.card-body > * + * {
  margin-top: var(--app-gap-stack);
}
</style>
