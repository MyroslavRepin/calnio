<script setup>
import { computed, ref, watch } from 'vue'
import { useNotion } from '../composables/useNotion'

// The step numbers are a prop so the welcome page can run this and the Apple
// wizard as one 01–04 sequence. Inside a Connections row each wizard stands
// alone, so the default is its own 01/02.
defineProps({
  numbers: { type: Array, default: () => ['01', '02'] },
})

const { state, connect, fetchDatabases, selectDatabase } = useNotion()

const picked = ref('')
const error = ref('')
const fetched = ref(false)

// Step 1 until Notion has granted us the workspace, then step 2 until a
// database is picked.
const step = computed(() => (state.connection ? 2 : 1))

// The grant is shared with zero databases — the likeliest first-run mistake,
// since Notion's dialog lets you finish without ticking anything.
const empty = computed(() => fetched.value && state.databases.length === 0)

// Nothing is fetched on load; the user arrives here straight off the callback,
// so this runs once as soon as step 2 appears.
watch(
  step,
  async (value) => {
    if (value !== 2 || fetched.value) return
    const { error: err } = await fetchDatabases()
    if (err) {
      error.value = err
      return
    }
    fetched.value = true
    picked.value = state.connection.data_source_id || ''
  },
  { immediate: true },
)

async function startConnect() {
  error.value = ''
  const { error: err } = await connect()
  if (err) error.value = err
}

async function submitDatabase() {
  error.value = ''
  const { error: err } = await selectDatabase(picked.value)
  if (err) error.value = err
}
</script>

<template>
  <div class="setup">
    <!-- Step 01 — authorize --------------------------------------------->
    <section class="step" :class="{ past: step > 1 }">
      <p class="num">{{ numbers[0] }}</p>
      <div class="body">
        <h3>Authorize Calnio in your Notion workspace</h3>

        <template v-if="step === 1">
          <p class="lede">
            Notion will ask which pages Calnio may read. Tick the database that
            holds your tasks — Calnio cannot see anything you do not share, and
            it only ever reads.
          </p>

          <button
            class="btn-primary"
            type="button"
            :disabled="state.busy"
            @click="startConnect"
          >
            {{ state.busy ? 'Opening Notion…' : 'Connect Notion' }}
          </button>

          <p class="note">
            You can revoke this at any time, from Notion's settings or from here.
          </p>
        </template>

        <p v-else class="done-line">
          Connected to <strong>{{ state.connection.workspace_name || 'your workspace' }}</strong>
        </p>
      </div>
    </section>

    <!-- Step 02 — database ---------------------------------------------->
    <section class="step" :class="{ ahead: step < 2 }">
      <p class="num">{{ numbers[1] }}</p>
      <div class="body">
        <h3>Choose the database with your tasks</h3>

        <template v-if="step === 2">
          <p v-if="state.busy && !fetched" class="lede">Loading your databases…</p>

          <template v-else-if="empty">
            <p class="lede">
              Calnio can see this workspace, but no databases were shared with
              it. Re-open Notion's dialog and tick the database that holds your
              tasks.
            </p>
            <button
              class="btn-primary"
              type="button"
              :disabled="state.busy"
              @click="startConnect"
            >
              {{ state.busy ? 'Opening Notion…' : "Re-open Notion's picker" }}
            </button>
          </template>

          <template v-else>
            <p class="lede">
              Calnio reads due dates from here. Only the databases you shared are
              listed.
            </p>

            <ul class="databases">
              <li v-for="db in state.databases" :key="db.id">
                <label>
                  <input type="radio" :value="db.id" v-model="picked" />
                  <span>{{ db.title || 'Untitled' }}</span>
                </label>
              </li>
            </ul>

            <button
              class="btn-primary"
              type="button"
              :disabled="state.busy || !picked"
              @click="submitDatabase"
            >
              {{ state.busy ? 'Saving…' : 'Use this database' }}
            </button>
          </template>
        </template>
      </div>
    </section>

    <p v-if="error || state.error" class="error">{{ error || state.error }}</p>
  </div>
</template>

<style scoped>
.setup {
  display: flex;
  flex-direction: column;
}

.step {
  display: grid;
  grid-template-columns: 64px 1fr;
  gap: 24px;
  padding: 40px 0;
  border-top: 1px solid var(--hairline);
}

.step.ahead {
  opacity: 0.4;
}

.num {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.16em;
  color: var(--muted);
  padding-top: 4px;
}

.body {
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: flex-start;
  max-width: 520px;
}

h3 {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.01em;
}

.lede,
.note,
.done-line {
  font-size: 15px;
  line-height: 1.6;
  color: var(--body);
}

.note {
  font-size: 13px;
  color: var(--muted);
}

.done-line strong {
  font-weight: 500;
  color: var(--ink);
}

.databases {
  list-style: none;
  margin: 0;
  padding: 0;
  border-top: 1px solid var(--hairline);
  width: 100%;
}

.databases li {
  border-bottom: 1px solid var(--hairline);
}

.databases label {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 0;
  font-size: 15px;
  cursor: pointer;
}

.btn-primary:disabled {
  opacity: 0.4;
  cursor: default;
}

.error {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--ink);
  border-top: 1px solid var(--hairline);
  padding-top: 20px;
}
</style>
