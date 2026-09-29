<script setup>
import { computed, ref } from 'vue'
import AppleCalendarSetup from '../../components/app/AppleCalendarSetup.vue'
import MappingAdd from '../../components/app/MappingAdd.vue'
import NotionSetup from '../../components/app/NotionSetup.vue'
import CalnioMark from '../../components/CalnioMark.vue'
import SetupStep from '../../components/app/SetupStep.vue'
import { useAppleCalendar } from '../../composables/useAppleCalendar'
import { loadWhenSignedIn, useAuth } from '../../composables/useAuth'
import { useMappings } from '../../composables/useMappings'
import { useNotion } from '../../composables/useNotion'
import { useSetup } from '../../composables/useSetup'

// Onboarding, outside the dashboard shell so nothing competes with it. Three
// steps, one open at a time. The order is forced by the API: creating a sync
// creates iCloud calendars, so the Apple credential has to exist first.
const authResult = useAuth()
const auth = authResult.state
const login = authResult.login

const appleResult = useAppleCalendar()
const apple = appleResult.state

const notionResult = useNotion()
const notion = notionResult.state

const mappingsResult = useMappings()
const mappings = mappingsResult.state

const setupResult = useSetup()
const stages = setupResult.stages
const ready = setupResult.ready
const doneCount = setupResult.doneCount
const allDone = setupResult.allDone

// This page sits outside DashboardLayout, so it asks for its own data.
loadWhenSignedIn(appleResult.load, notionResult.load, mappingsResult.load)

const error = ref(null)

// The step being worked on: the first one not finished. Everything before it
// collapses, everything after it is locked.
const current = computed(function () {
  if (!stages.value[0].done) {
    return 1
  }
  if (!stages.value[1].done) {
    return 2
  }
  return 3
})

// Which Notion workspace the grant landed on, for the collapsed step 1.
const workspaceName = computed(function () {
  if (notion.connection?.workspace_name) {
    return notion.connection.workspace_name
  }
  return 'Connected'
})

// Which Apple Account the credential belongs to, for the collapsed step 2.
const appleEmail = computed(function () {
  if (apple.connection?.icloud_email) {
    return apple.connection.icloud_email
  }
  return 'Connected'
})

// How many syncs ended up running, for the collapsed step 3.
const syncSummary = computed(function () {
  const running = mappings.list.filter(function (mapping) {
    return mapping.eligible
  })

  if (running.length === 1) {
    return '1 sync'
  }
  return running.length + ' syncs'
})
</script>

<template>
  <div class="app-ui column page">
    <header class="topbar">
      <div class="row topbarrow">
        <router-link to="/" class="wordmark">
          <span class="plate"><CalnioMark /></span>
          Calnio
        </router-link>
        <p v-if="ready && auth.user" class="note">
          {{ doneCount }} of {{ stages.length }} done
        </p>
      </div>
    </header>

    <main class="column main">
      <p v-if="!auth.ready" class="loading">Loading…</p>

      <section v-else-if="!auth.user" class="card column panel">
        <h1 class="title">Set up Calnio</h1>
        <p class="lead">Sign in first. Your setup is stored against your account.</p>
        <button class="btn" type="button" @click="login">Continue with Google</button>
      </section>

      <template v-else>
        <header class="column page-head">
          <h1 class="title">{{ allDone ? 'You are set up' : 'Set up Calnio' }}</h1>
          <p class="lead">
            <template v-if="allDone">
              Your Notion dates are in Apple Calendar, and Calnio keeps them there
              on a schedule. Change anything from your dashboard.
            </template>
            <template v-else>
              Three steps, about two minutes. At the end your Notion dates show up
              in Apple Calendar as real events.
            </template>
          </p>

          <router-link v-if="allDone" class="btn" :to="{ name: 'dashboard' }">
            Go to your dashboard
          </router-link>
        </header>

        <p v-if="!ready" class="loading">Loading your connections…</p>

        <div v-else class="card steps">
          <SetupStep
            number="1"
            title="Connect Notion"
            :summary="workspaceName"
            :done="stages[0].done"
            :open="current === 1"
          >
            <NotionSetup />
          </SetupStep>

          <SetupStep
            number="2"
            title="Connect iCloud"
            :summary="appleEmail"
            :done="stages[1].done"
            :open="current === 2"
            :locked="current < 2"
          >
            <AppleCalendarSetup />
          </SetupStep>

          <SetupStep
            number="3"
            title="Pick your databases"
            :summary="syncSummary"
            :done="stages[2].done"
            :open="current === 3"
            :locked="current < 3"
          >
            <MappingAdd @error="error = $event" @added="error = null" />
            <p v-if="error" class="error">{{ error }}</p>
          </SetupStep>
        </div>

        <footer v-if="ready && !allDone" class="exitrow">
          <router-link :to="{ name: 'dashboard' }">Finish this later</router-link>
        </footer>
      </template>
    </main>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
}

.topbar {
  background: var(--app-canvas);
  border-bottom: 1px solid var(--app-border);
}

.plate {
  width: 22px;
  height: 22px;
  flex: none;
  margin-right: var(--app-gap-inline);
}

.topbarrow {
  --gap: var(--app-gap-block);
  flex-wrap: nowrap;
  justify-content: space-between;
  max-width: var(--app-width-narrow);
  margin: 0 auto;
  padding: 10px var(--app-pad-page);
}

.main {
  --gap: 0px;
  flex: 1;
  width: 100%;
  max-width: var(--app-width-narrow);
  margin: 0 auto;
  padding: var(--app-space-6) var(--app-pad-page) var(--app-space-8);
}

/* One card holds all three steps, so the sequence reads as one job. */
.steps {
  padding: var(--app-space-5);
}

.exitrow {
  display: flex;
  padding-top: var(--app-space-5);
  font-size: var(--app-text-body);
}
</style>
