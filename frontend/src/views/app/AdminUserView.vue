<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import DayChart from '../../components/app/DayChart.vue'
import RunTable from '../../components/app/RunTable.vue'
import StatusLabel from '../../components/app/StatusLabel.vue'
import SyncTable from '../../components/app/SyncTable.vue'
import { useAdmin } from '../../composables/useAdmin'
import { formatDateTime, grepCommand } from '../../format'

const route = useRoute()

const adminResult = useAdmin()
const admin = adminResult.state
const loadUser = adminResult.loadUser

const error = ref(null)

// Loads the account in the URL, again whenever a link on this page points at
// another one, since the router reuses this view rather than remounting it.
async function load() {
  // Leaving this page changes the route before the view goes away, so a
  // missing id means there is nothing to load.
  if (!route.query.id) {
    return
  }

  error.value = null
  const result = await loadUser(route.query.id)
  if (result.error) {
    error.value = result.error
  }
}

watch(
  function () {
    return route.query.id
  },
  load,
  { immediate: true },
)

const detail = computed(function () {
  return admin.user
})

const runSeries = [
  { key: 'runs_ok', name: 'ok', tone: 'success' },
  { key: 'runs_failed', name: 'failed', tone: 'danger' },
]

// The account's display name, or a note that Google sent none.
const displayName = computed(function () {
  if (detail.value.user.name) {
    return detail.value.user.name
  } else {
    return 'none given'
  }
})

// The Notion workspace's name, which a workspace may not have.
const workspaceName = computed(function () {
  if (detail.value.notion.workspace_name) {
    return detail.value.notion.workspace_name
  } else {
    return 'unnamed'
  }
})

function yesNo(flag) {
  if (flag) {
    return 'yes'
  } else {
    return 'no'
  }
}

function onOff(flag) {
  if (flag) {
    return 'on'
  } else {
    return 'off'
  }
}

function whenLabel(value) {
  return formatDateTime(value, 'never')
}
</script>

<template>
  <p v-if="error" class="error">{{ error }}</p>
  <p v-else-if="!detail" class="loading">Loading…</p>

  <template v-else>
    <header class="column page-head">
      <h1 class="title">{{ detail.user.email }}</h1>
      <p class="lead">
        Account <span class="ident">#{{ detail.user.id }}</span>, joined
        {{ whenLabel(detail.user.joined) }}.
      </p>
    </header>

    <!-- Who this is, and how their last tick went. -->
    <section class="card">
      <div class="card-head">
        <h2>Account</h2>
        <StatusLabel :status="detail.user.last_status" />
      </div>
      <div class="card-body column status">
        <dl class="datarows">
          <div>
            <dt>ID</dt>
            <dd><code>{{ detail.user.id }}</code></dd>
          </div>
          <div>
            <dt>Name</dt>
            <dd>{{ displayName }}</dd>
          </div>
          <div>
            <dt>Admin</dt>
            <dd>{{ yesNo(detail.user.is_admin) }}</dd>
          </div>
          <div>
            <dt>Master switch</dt>
            <dd>{{ onOff(detail.master_enabled) }}</dd>
          </div>
          <div>
            <dt>Syncing right now</dt>
            <dd>{{ yesNo(detail.user.syncing) }}</dd>
          </div>
          <div>
            <dt>Last tick</dt>
            <dd>{{ whenLabel(detail.user.last_run_at) }}</dd>
          </div>
          <div>
            <dt>Events Calnio keeps in step</dt>
            <dd>{{ detail.user.events }}</dd>
          </div>
        </dl>
        <code>{{ grepCommand('user=' + detail.user.id) }}</code>
      </div>
    </section>

    <!-- The Notion grant, everything but the token. -->
    <section class="card">
      <div class="card-head">
        <h2>Notion</h2>
        <span v-if="!detail.notion" class="label neutral">not connected</span>
        <span v-else-if="detail.notion.can_write" class="label success">can write</span>
        <span v-else class="label attention">read only</span>
      </div>
      <div class="card-body">
        <p v-if="!detail.notion" class="note">This account never connected Notion.</p>
        <dl v-else class="datarows">
          <div>
            <dt>Workspace</dt>
            <dd>{{ workspaceName }}</dd>
          </div>
          <div>
            <dt>Workspace id</dt>
            <dd><code>{{ detail.notion.workspace_id }}</code></dd>
          </div>
          <div>
            <dt>Bot id</dt>
            <dd><code>{{ detail.notion.bot_id }}</code></dd>
          </div>
          <div>
            <dt>Connected</dt>
            <dd>{{ whenLabel(detail.notion.connected_at) }}</dd>
          </div>
          <div>
            <dt>Last verified</dt>
            <dd>{{ whenLabel(detail.notion.last_verified_at) }}</dd>
          </div>
        </dl>
      </div>
    </section>

    <!-- The iCloud credential, everything but the account and the password. -->
    <section class="card">
      <div class="card-head">
        <h2>iCloud</h2>
        <span v-if="detail.icloud" class="label success">connected</span>
        <span v-else class="label neutral">not connected</span>
      </div>
      <div class="card-body">
        <p v-if="!detail.icloud" class="note">This account never connected iCloud.</p>
        <dl v-else class="datarows">
          <div>
            <dt>Connected</dt>
            <dd>{{ whenLabel(detail.icloud.connected_at) }}</dd>
          </div>
          <div>
            <dt>Last verified</dt>
            <dd>{{ whenLabel(detail.icloud.last_verified_at) }}</dd>
          </div>
        </dl>
      </div>
    </section>

    <section class="card">
      <div class="card-head">
        <h2>Syncs</h2>
        <span class="label neutral">{{ detail.syncs.length }}</span>
      </div>
      <div class="card-body">
        <SyncTable :syncs="detail.syncs" />
      </div>
    </section>

    <section class="card">
      <div class="card-head">
        <h2>Runs, 30 days</h2>
      </div>
      <div class="card-body">
        <DayChart :days="detail.days" :series="runSeries" />
      </div>
    </section>

    <section class="card">
      <div class="card-head">
        <h2>Latest runs</h2>
        <router-link :to="{ name: 'admin-runs', query: { user_id: detail.user.id } }">
          All runs of this account
        </router-link>
      </div>
      <div class="card-body">
        <RunTable :runs="detail.runs" />
      </div>
    </section>
  </template>
</template>
