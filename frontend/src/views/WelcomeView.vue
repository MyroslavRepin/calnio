<script setup>
import { computed, onMounted, watch } from 'vue'
import AppleCalendarSetup from '../components/AppleCalendarSetup.vue'
import AtmosphereField from '../components/AtmosphereField.vue'
import NotionSetup from '../components/NotionSetup.vue'
import { useAppleCalendar } from '../composables/useAppleCalendar'
import { useAuth } from '../composables/useAuth'
import { useNotion } from '../composables/useNotion'

// Full-screen onboarding: the whole setup on one scrolling page, outside the
// dashboard shell so nothing competes with it. The two wizards are the real
// ones from Connections, renumbered 01–04 into a single sequence.
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
  <div class="page">
    <AtmosphereField variant="short" />

    <!-- Sticky progress ---------------------------------------------------->
    <header class="bar">
      <div class="wrap barinner">
        <router-link to="/" class="wordmark">calnio</router-link>
        <p class="count">
          <template v-if="ready">{{ doneCount }} of {{ stages.length }}</template>
          <template v-else>setup</template>
        </p>
      </div>
      <!-- No transition on the fill: the design system has no motion. -->
      <div class="track" role="presentation">
        <div class="fill" :style="{ width: ready ? `${percent}%` : '0%' }" />
      </div>
    </header>

    <main class="wrap main">
      <p v-if="!auth.ready" class="loading">Loading…</p>

      <!-- Signed out ------------------------------------------------------->
      <section v-else-if="!auth.user" class="hero">
        <p class="eyebrow">Welcome</p>
        <h1 class="title">Set up Calnio.</h1>
        <p class="lead">Log in first — your setup is stored against your account.</p>
        <button class="btn" type="button" @click="login">Continue with Google</button>
      </section>

      <template v-else>
        <section class="hero">
          <p class="eyebrow">Welcome</p>
          <h1 class="title">{{ allDone ? 'You are all set.' : 'Set up Calnio.' }}</h1>
          <p class="lead">
            <template v-if="allDone">
              Both connections are in place. Syncing your own workspace switches
              on later in beta — nothing else is needed from you until then.
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
        </section>

        <p v-if="!ready" class="loading">Loading your connections…</p>

        <!-- The wizards carry forms and small print, so they ride on a
             surface rather than sitting straight on the atmosphere. -->
        <div v-else class="wizards surface">
          <!-- Steps 01–02 ------------------------------------------------->
          <NotionSetup :numbers="['01', '02']" />

          <!-- Steps 03–04 ------------------------------------------------->
          <AppleCalendarSetup :numbers="['03', '04']">
            <template #help>
              <p class="help">
                Apple requires an <strong>app-specific password</strong>. Your
                Apple Account password will not work here.
              </p>
              <p class="help">
                Your Apple Account also needs two-factor authentication turned on
                — without it, Apple does not offer app-specific passwords at all.
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
                  Name it <span class="mono">Calnio</span>, then copy the
                  <span class="mono">xxxx-xxxx-xxxx-xxxx</span> it shows you
                </li>
              </ol>

              <p class="note">
                Revoking the password at Apple disconnects Calnio immediately.
              </p>
            </template>
          </AppleCalendarSetup>

          <footer class="foot">
            <router-link class="link-mono quiet" :to="{ name: 'dashboard' }">
              <span>{{ allDone ? 'Go to your dashboard' : 'Skip for now' }}</span>
            </router-link>
          </footer>
        </div>
      </template>
    </main>
  </div>
</template>

<style scoped>
/* `clip`, not `hidden`: hidden would make this a scroll container and the
   progress bar would stop sticking. */
.page {
  position: relative;
  min-height: 100vh;
  overflow: clip;
  display: flex;
  flex-direction: column;
}

/* Progress ------------------------------------------------------------- */
.bar {
  position: sticky;
  top: 0;
  z-index: 2;
  /* Translucent because the atmosphere layer runs underneath it. */
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(10px);
}

.barinner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding-top: 8px;
  padding-bottom: 8px;
}

.wordmark {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  font-size: 19px;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: var(--ink);
}

.count {
  font-family: var(--font-mono);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: var(--muted);
}

.track {
  height: 2px;
  background: var(--hairline);
}

.fill {
  height: 2px;
  background: var(--ink);
}

/* Content -------------------------------------------------------------- */
.main {
  position: relative;
  z-index: 1;
  flex: 1;
  padding-bottom: var(--sec-bottom);
}

.hero {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: clamp(16px, 2.5vw, 24px);
  padding: clamp(40px, 9vw, 84px) 0 clamp(32px, 6vw, 56px);
  max-width: 640px;
}

.wizards {
  max-width: 760px;
}

/* The panel already opens the block; the first step's own rule would double it. */
.wizards > :first-child :deep(.step:first-child) {
  border-top: none;
  padding-top: 0;
}

/* Apple instructions, injected into the wizard's slot ------------------- */
.help {
  font-size: 15px;
  line-height: 1.6;
  color: var(--body);
  max-width: 52ch;
}

.help strong {
  font-weight: 500;
  color: var(--ink);
}

.sub {
  list-style: none;
  margin: 0;
  padding: 0;
  counter-reset: substep;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 52ch;
}

.sub li {
  counter-increment: substep;
  display: grid;
  grid-template-columns: 24px 1fr;
  gap: 12px;
  font-size: 15px;
  line-height: 1.6;
  color: var(--body);
}

.sub li::before {
  content: counter(substep, lower-alpha);
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.16em;
  color: var(--muted);
  padding-top: 3px;
}

.sub a {
  border-bottom: 1px solid var(--field-line);
  color: var(--ink);
}

.mono {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--ink);
}

.foot {
  display: flex;
  padding-top: clamp(24px, 4vw, 40px);
  border-top: 1px solid var(--hairline);
}
</style>
