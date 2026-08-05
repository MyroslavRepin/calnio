<script setup>
import { computed, onMounted, watch } from 'vue'
import AppleCalendarSetup from '../components/AppleCalendarSetup.vue'
import NotionSetup from '../components/NotionSetup.vue'
import { useAppleCalendar } from '../composables/useAppleCalendar'
import { useAuth } from '../composables/useAuth'
import { useNotion } from '../composables/useNotion'

// Onboarding: the whole setup on one page, outside the dashboard shell so
// nothing competes with it. The two wizards are the real ones from Connections,
// renumbered 1–4 into a single sequence.
const { state: auth, login } = useAuth()
const { state: apple, load: loadApple } = useAppleCalendar()
const { state: notion, load: loadNotion } = useNotion()

// Same four stages the dashboard counts: a grant stored, then a target picked,
// for each of the two connections.
const stages = computed(() => [
  Boolean(notion.connection),
  Boolean(notion.connection?.data_source_id),
  Boolean(apple.connection),
  Boolean(apple.connection?.calendar_url),
])

const ready = computed(() => notion.ready && apple.ready)
const doneCount = computed(() => stages.value.filter(Boolean).length)
const allDone = computed(() => doneCount.value === stages.value.length)
const percent = computed(() => (doneCount.value / stages.value.length) * 100)

// DashboardLayout loads these for its own children; this page sits outside it,
// so it asks for them itself once a user exists.
function loadIfAuthed() {
  if (!auth.ready || !auth.user) return
  loadApple()
  loadNotion()
}

onMounted(loadIfAuthed)
watch(() => [auth.ready, auth.user], loadIfAuthed)
</script>

<template>
  <div class="app-ui page">
    <!-- Sticky progress ---------------------------------------------------->
    <header class="bar">
      <div class="barinner">
        <router-link to="/" class="wordmark">calnio</router-link>
        <p class="count">
          <template v-if="ready">{{ doneCount }} of {{ stages.length }} done</template>
          <template v-else>Setup</template>
        </p>
      </div>
      <div class="track" role="presentation">
        <div class="fill" :style="{ width: ready ? `${percent}%` : '0%' }" />
      </div>
    </header>

    <main class="main">
      <p v-if="!auth.ready" class="loading">Loading…</p>

      <!-- Signed out ------------------------------------------------------->
      <section v-else-if="!auth.user" class="card intro">
        <h1 class="title">Set up Calnio</h1>
        <p class="lead">Sign in first, your setup is stored against your account.</p>
        <button class="btn" type="button" @click="login">Continue with Google</button>
      </section>

      <template v-else>
        <header class="page-head">
          <h1 class="title">{{ allDone ? 'You are all set' : 'Set up Calnio' }}</h1>
          <p class="lead">
            <template v-if="allDone">
              Both connections are in place. Syncing your own workspace switches
              on later in beta, nothing else is needed from you until then.
            </template>
            <template v-else>
              Four steps, once. You are connecting your accounts now; syncing
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
              <span class="label" :class="stages[1] ? 'success' : 'neutral'">
                Steps 1 and 2
              </span>
            </div>
            <div class="card-body">
              <NotionSetup :numbers="['1', '2']" />
            </div>
          </section>

          <section class="card">
            <div class="card-head">
              <h2>Apple Calendar</h2>
              <span class="label" :class="stages[3] ? 'success' : 'neutral'">
                Steps 3 and 4
              </span>
            </div>
            <div class="card-body">
              <AppleCalendarSetup :numbers="['3', '4']">
                <template #help>
                  <p class="body">
                    Apple requires an <strong>app-specific password</strong>. Your
                    Apple Account password will not work here. Your Apple Account
                    also needs two-factor authentication turned on, without it
                    Apple does not offer app-specific passwords at all.
                  </p>

                  <ol class="sub">
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

          <footer class="foot">
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
  display: flex;
  flex-direction: column;
}

/* Progress ------------------------------------------------------------- */
.bar {
  position: sticky;
  top: 0;
  z-index: 2;
  background: var(--app-canvas);
  border-bottom: 1px solid var(--app-border);
}

.barinner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--app-gap-block);
  max-width: var(--app-width-narrow);
  margin: 0 auto;
  padding: 10px var(--app-pad-page);
}

.wordmark {
  display: inline-flex;
  align-items: center;
  min-height: var(--app-control-height);
  font-size: var(--app-text-head);
  font-weight: var(--app-weight-bold);
  letter-spacing: -0.01em;
  color: var(--app-fg);
}

.wordmark:hover {
  text-decoration: none;
}

.count {
  font-size: var(--app-text-meta);
  color: var(--app-fg-muted);
}

/* No transition on the fill: the width simply reflects the stored state. */
.track {
  height: 3px;
  background: var(--app-canvas-subtle);
}

.fill {
  height: 3px;
  background: var(--app-success);
}

/* Content -------------------------------------------------------------- */
.main {
  flex: 1;
  width: 100%;
  max-width: var(--app-width-narrow);
  margin: 0 auto;
  padding: var(--app-space-5) var(--app-pad-page) var(--app-space-8);
}

.intro {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--app-gap-block);
  max-width: var(--app-width-panel);
  margin: var(--app-space-7) auto;
  padding: var(--app-space-5);
}

/* Apple instructions, injected into the wizard's slot ------------------- */
.sub {
  margin: 0;
  padding-left: var(--app-space-5);
  display: flex;
  flex-direction: column;
  gap: var(--app-space-1);
  font-size: var(--app-text-body);
  color: var(--app-fg-muted);
  max-width: var(--app-measure);
}

.foot {
  display: flex;
  margin-top: var(--app-gap-block);
  padding-top: var(--app-space-4);
  border-top: 1px solid var(--app-border-subtle);
  font-size: var(--app-text-body);
}
</style>
