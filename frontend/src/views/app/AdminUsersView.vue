<script setup>
import { computed, onMounted, ref } from 'vue'
import StatusLabel from '../../components/app/StatusLabel.vue'
import { useAdmin } from '../../composables/useAdmin'
import { formatDateTime } from '../../format'

const adminResult = useAdmin()
const admin = adminResult.state
const loadUsers = adminResult.loadUsers

const error = ref(null)
const search = ref('')
const show = ref('all')

onMounted(async function () {
  const result = await loadUsers()
  if (result.error) {
    error.value = result.error
  }
})

// Whether one account passes the chosen filter.
function passesFilter(person) {
  if (show.value === 'syncing') {
    return person.syncing
  }
  if (show.value === 'stuck') {
    return !person.syncing
  }
  if (show.value === 'failing') {
    return person.failing_mappings > 0
  }
  if (show.value === 'twoway') {
    return person.two_way_mappings > 0
  }
  if (show.value === 'admins') {
    return person.is_admin
  }
  return true
}

// Whether one account matches the search, by email, name or id.
function matchesSearch(person) {
  const term = search.value.trim().toLowerCase()
  if (!term) {
    return true
  }
  if (String(person.id) === term) {
    return true
  }
  if (person.email.toLowerCase().includes(term)) {
    return true
  }
  if (person.name && person.name.toLowerCase().includes(term)) {
    return true
  }
  return false
}

// The accounts on screen, newest first, so a fresh signup is at the top.
const people = computed(function () {
  if (!admin.users) {
    return []
  }
  const matching = admin.users.filter(function (person) {
    return passesFilter(person) && matchesSearch(person)
  })
  return matching.slice().reverse()
})

// Notion has three states worth telling apart, not two.
function notionLabel(person) {
  if (!person.notion) {
    return 'no'
  }
  if (person.notion_can_write) {
    return 'yes'
  }
  return 'read only'
}

function yesNo(flag) {
  if (flag) {
    return 'yes'
  } else {
    return 'no'
  }
}

function whenLabel(value) {
  return formatDateTime(value, 'never')
}
</script>

<template>
  <p v-if="error" class="error">{{ error }}</p>
  <p v-else-if="!admin.users" class="loading">Loading…</p>

  <template v-else>
    <header class="column page-head">
      <h1 class="title">Accounts</h1>
      <p class="lead">Every account, newest first. Open one for its grants, syncs and runs.</p>
    </header>

    <section class="card">
      <div class="card-head">
        <h2>Accounts</h2>
        <span class="label neutral">{{ people.length }} of {{ admin.users.length }}</span>
      </div>
      <div class="card-body column adminlist">
        <div class="row filters">
          <label class="column field">
            <span>Search</span>
            <input v-model="search" type="search" placeholder="Email, name or id" />
          </label>
          <label class="column field">
            <span>Show</span>
            <select v-model="show">
              <option value="all">Everybody</option>
              <option value="syncing">Syncing</option>
              <option value="stuck">Not syncing</option>
              <option value="failing">With a failing sync</option>
              <option value="twoway">Using two-way</option>
              <option value="admins">Admins</option>
            </select>
          </label>
        </div>

        <p v-if="!people.length" class="note">No account matches.</p>

        <div v-else class="tablebox">
          <table class="datatable">
            <thead>
              <tr>
                <th>ID</th>
                <th>Email</th>
                <th>Joined</th>
                <th>Notion</th>
                <th>iCloud</th>
                <th>Syncs</th>
                <th>On</th>
                <th>Two-way</th>
                <th>Failing</th>
                <th>Events</th>
                <th>Last run</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="person in people" :key="person.id">
                <td>
                  <router-link :to="{ name: 'admin-user', query: { id: person.id } }">
                    <span class="ident">#{{ person.id }}</span>
                  </router-link>
                </td>
                <td>
                  <router-link :to="{ name: 'admin-user', query: { id: person.id } }">
                    {{ person.email }}
                  </router-link>
                  <span v-if="person.is_admin" class="label accent">admin</span>
                </td>
                <td>{{ whenLabel(person.joined) }}</td>
                <td>{{ notionLabel(person) }}</td>
                <td>{{ yesNo(person.icloud) }}</td>
                <td>{{ person.mappings }}</td>
                <td>{{ person.enabled_mappings }}</td>
                <td>{{ person.two_way_mappings }}</td>
                <td>{{ person.failing_mappings }}</td>
                <td>{{ person.events }}</td>
                <td>{{ whenLabel(person.last_run_at) }}</td>
                <td><StatusLabel :status="person.last_status" /></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  </template>
</template>
