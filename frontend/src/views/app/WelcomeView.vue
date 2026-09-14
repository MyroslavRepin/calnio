<script setup>
import { ref } from 'vue'
import AppleCalendarSetup from '../../components/app/AppleCalendarSetup.vue'
import MappingAdd from '../../components/app/MappingAdd.vue'
import MappingCard from '../../components/app/MappingCard.vue'
import NotionSetup from '../../components/app/NotionSetup.vue'
import { useAppleCalendar } from '../../composables/useAppleCalendar'
import { loadWhenSignedIn, useAuth } from '../../composables/useAuth'
import { useMappings } from '../../composables/useMappings'
import { useNotion } from '../../composables/useNotion'
import { useSetup } from '../../composables/useSetup'

// Onboarding: the whole setup on one page, outside the dashboard shell so
// nothing competes with it. The two wizards and the sync card are the real ones
// from Connections and Syncs, renumbered 1 to 3 into a single sequence.
const authResult = useAuth()
const auth = authResult.state
const login = authResult.login

const appleResult = useAppleCalendar()
const notionResult = useNotion()

const mappingsResult = useMappings()
const mappings = mappingsResult.state

const setupResult = useSetup()
const stages = setupResult.stages
const ready = setupResult.ready
const doneCount = setupResult.doneCount
const allDone = setupResult.allDone
const percent = setupResult.percent

// This page sits outside DashboardLayout, so it asks for its own data.
loadWhenSignedIn(appleResult.load, notionResult.load, mappingsResult.load)

// One error box for the third step, which is the only part of this page that
// talks to Notion and iCloud after the grants are in.
const error = ref(null)
</script>

<template>
  <div class="app-ui column page">
    <header class="progressbar">
      <div class="row progressrow">
        <router-link to="/" class="wordmark">Calnio</router-link>
        <p class="progresscount">
          <template v-if="ready">{{ doneCount }} of {{ stages.length }} done</template>
          <template v-else>Setup</template>
        </p>
      </div>
      <div class="progresstrack" role="presentation">
        <div class="progressfill" :style="{ width: ready ? `${percent}%` : '0%' }" />
      </div>
    </header>

    <main class="main">
      <p v-if="!auth.ready" class="loading">Loading…</p>

      <section v-else-if="!auth.user" class="card column panel">
        <h1 class="title">Set up Calnio</h1>
        <p class="lead">Sign in first, your setup is stored against your account.</p>
        <button class="btn" type="button" @click="login">Continue with Google</button>
      </section>

      <template v-else>
        <header class="column page-head">
          <h1 class="title">{{ allDone ? 'You are all set' : 'Set up Calnio' }}</h1>
          <p class="lead">
            <template v-if="allDone">
              Both connections are in place. Syncing your own workspace switches
              on later in beta, nothing else is needed from you until then.
            </template>
            <template v-else>
              Five steps, once. You are connecting your accounts now; syncing
              your own workspace switches on later in beta, and everything you
              set up here carries over when it does.
            </template>
          </p>

          <router-link v-if="allDone" class="btn" :to="{ name: 'dashboard' }">
            Go to your dashboard
          </router-link>
        </header>

        <p v-if="!ready" class="loading">Loading your connections…</p>

        <template v-else>
          <section class="card">
            <div class="card-head">
              <h2>Notion</h2>
              <span class="label" :class="stages[0].done ? 'success' : 'neutral'">
                Step 1
              </span>
            </div>
            <div class="card-body">
              <NotionSetup :numbers="['1']" />
            </div>
          </section>

          <section class="card">
            <div class="card-head">
              <h2>Apple Calendar</h2>
              <span class="label" :class="stages[1].done ? 'success' : 'neutral'">
                Step 2
              </span>
            </div>
            <div class="card-body">
              <AppleCalendarSetup :numbers="['2']">
                <template #help>
                  <p class="body">
                    Apple requires an <strong>app-specific password</strong>. Your
                    Apple Account password will not work here. Your Apple Account
                    also needs two-factor authentication turned on, without it
                    Apple does not offer app-specific passwords at all.
                  </p>

                  <ol class="column substeps">
                    <li>
                      Sign in at
                      <a href="https://account.apple.com" target="_blank" rel="noreferrer"
                        >account.apple.com</a
                      >
                    </li>
                    <li>Open Sign-In and Security → App-Specific Passwords</li>
                    <li>Choose Generate an app-specific password</li>
                    <li>
                      Name it <code>Calnio</code>, then copy the
                      <code>xxxx-xxxx-xxxx-xxxx</code> it shows you
                    </li>
                  </ol>

                  <p class="note">
                    Revoking the password at Apple disconnects Calnio immediately.
                  </p>
                </template>
              </AppleCalendarSetup>
            </div>
          </section>

          <section class="column step laststep">
            <div class="row stephead">
              <span class="num" :class="{ done: stages[2].done }">3</span>
              <h3>Set up your first sync</h3>
            </div>

            <p v-if="!stages[0].done || !stages[1].done" class="body">
              Available once both accounts above are connected.
            </p>

            <template v-else>
              <MappingCard
                v-for="mapping in mappings.list"
                :key="mapping.id"
                :mapping="mapping"
                @error="error = $event"
              />
              <MappingAdd @error="error = $event" @added="error = null" />
              <p v-if="error" class="error">{{ error }}</p>
            </template>
          </section>

          <footer class="skiprow">
            <router-link :to="{ name: 'dashboard' }">
              {{ allDone ? 'Go to your dashboard' : 'Skip for now' }}
            </router-link>
          </footer>
        </template>
      </template>
    </main>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
}

.progressbar {
  position: sticky;
  top: 0;
  z-index: 2;
  background: var(--app-canvas);
  border-bottom: 1px solid var(--app-border);
}

.progressrow {
  --gap: var(--app-gap-block);
  flex-wrap: nowrap;
  justify-content: space-between;
  max-width: var(--app-width-narrow);
  margin: 0 auto;
  padding: 10px var(--app-pad-page);
}

.progresscount {
  font-size: var(--app-text-meta);
  color: var(--app-fg-muted);
}

/* No transition on the fill: the width simply reflects the stored state. */
.progresstrack {
  height: 3px;
  background: var(--app-canvas-subtle);
}

.progressfill {
  height: 3px;
  background: var(--app-success);
}

.main {
  flex: 1;
  width: 100%;
  max-width: var(--app-width-narrow);
  margin: 0 auto;
  padding: var(--app-space-5) var(--app-pad-page) var(--app-space-8);
}

/* Step 3 stands outside a card, because the sync cards are cards themselves. */
.laststep {
  margin-top: var(--app-gap-block);
}

/* Apple instructions, injected into the wizard's slot. */
.substeps {
  --gap: var(--app-space-1);
  margin: 0;
  padding-left: var(--app-space-5);
  font-size: var(--app-text-body);
  color: var(--app-fg-muted);
  max-width: var(--app-measure);
}

.skiprow {
  display: flex;
  margin-top: var(--app-gap-block);
  padding-top: var(--app-space-4);
  border-top: 1px solid var(--app-border-subtle);
  font-size: var(--app-text-body);
}
</style>
