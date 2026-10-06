<script setup>
import StatusLabel from './StatusLabel.vue'
import { formatDateTime, formatDuration } from '../../format'

defineProps({
  runs: { type: Array, required: true },
})

// What a run wrote into Apple Calendar: created, updated, deleted.
function calendarWork(run) {
  return run.created + ' / ' + run.updated + ' / ' + run.deleted
}

// What a run wrote back into Notion: pulled, imported, trashed.
function notionWork(run) {
  return run.pulled + ' / ' + run.imported + ' / ' + run.trashed
}

function startedLabel(value) {
  return formatDateTime(value, 'unknown')
}

function durationLabel(value) {
  return formatDuration(value, 'unknown')
}
</script>

<template>
  <p v-if="!runs.length" class="note">No runs recorded yet.</p>

  <div v-else class="tablebox">
    <table class="datatable">
      <thead>
        <tr>
          <th>Started</th>
          <th>Run</th>
          <th>Account</th>
          <th>Sync</th>
          <th>Status</th>
          <th>Took</th>
          <th title="created / updated / deleted">To calendar</th>
          <th title="pulled / imported / trashed">To Notion</th>
          <th>Error</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="run in runs" :key="run.id">
          <td>{{ startedLabel(run.started_at) }}</td>
          <td>
            <router-link
              v-if="run.run_id"
              :to="{ name: 'admin-runs', query: { run_id: run.run_id } }"
            >
              <code>{{ run.run_id }}</code>
            </router-link>
          </td>
          <td>
            <router-link :to="{ name: 'admin-user', query: { id: run.user_id } }">
              {{ run.email }}
            </router-link>
            <span class="ident"> #{{ run.user_id }}</span>
          </td>
          <td>
            <template v-if="run.mapping_id">
              <router-link :to="{ name: 'admin-sync', query: { id: run.mapping_id } }">
                {{ run.database }}
              </router-link>
              <span class="ident"> #{{ run.mapping_id }}</span>
            </template>
            <span v-else class="ident">deleted</span>
          </td>
          <td><StatusLabel :status="run.status" /></td>
          <td>{{ durationLabel(run.duration_ms) }}</td>
          <td>{{ calendarWork(run) }}</td>
          <td>{{ notionWork(run) }}</td>
          <td class="reason">{{ run.error }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
