<script setup>
import StatusLabel from './StatusLabel.vue'
import { formatDateTime } from '../../format'

defineProps({
  syncs: { type: Array, required: true },
})

// A sync's state: an unfinished or paused sync says so before its last run.
function syncStatus(sync) {
  if (!sync.eligible) {
    return 'unfinished'
  }
  if (!sync.enabled) {
    return 'paused'
  }
  return sync.last_status
}

// A yes or no column, written out rather than left as true and false.
function yesNo(flag) {
  if (flag) {
    return 'yes'
  } else {
    return 'no'
  }
}

// A sync whose target is still unpicked says so rather than leaving a blank.
function orUnset(value) {
  if (value) {
    return value
  } else {
    return 'not set'
  }
}

function lastRunLabel(value) {
  return formatDateTime(value, 'never')
}
</script>

<template>
  <p v-if="!syncs.length" class="note">No syncs.</p>

  <div v-else class="tablebox">
    <table class="datatable">
      <thead>
        <tr>
          <th>ID</th>
          <th>Database</th>
          <th>Account</th>
          <th>Calendar</th>
          <th>Date column</th>
          <th>On</th>
          <th>Two-way</th>
          <th>Events</th>
          <th>Runs 7d</th>
          <th>Failed 7d</th>
          <th>Last run</th>
          <th>Status</th>
          <th>Last error</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="sync in syncs" :key="sync.id">
          <td>
            <router-link :to="{ name: 'admin-sync', query: { id: sync.id } }">
              <span class="ident">#{{ sync.id }}</span>
            </router-link>
          </td>
          <td>
            <router-link :to="{ name: 'admin-sync', query: { id: sync.id } }">
              {{ orUnset(sync.database) }}
            </router-link>
          </td>
          <td>
            <router-link :to="{ name: 'admin-user', query: { id: sync.user_id } }">
              {{ sync.email }}
            </router-link>
            <span class="ident"> #{{ sync.user_id }}</span>
          </td>
          <td>{{ orUnset(sync.calendar) }}</td>
          <td>{{ orUnset(sync.date_property) }}</td>
          <td>{{ yesNo(sync.enabled) }}</td>
          <td>{{ yesNo(sync.two_way) }}</td>
          <td>{{ sync.events }}</td>
          <td>{{ sync.runs_7d }}</td>
          <td>{{ sync.failed_7d }}</td>
          <td>{{ lastRunLabel(sync.last_run_at) }}</td>
          <td><StatusLabel :status="syncStatus(sync)" /></td>
          <td class="reason">{{ sync.last_error }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
