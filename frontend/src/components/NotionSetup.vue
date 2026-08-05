<script setup>
import { computed, ref, watch } from 'vue'
import { useNotion } from '../composables/useNotion'

// The step numbers are a prop so the welcome page can run this and the Apple
// wizard as one 1–4 sequence. Inside a Connections row each wizard stands
// alone, so the default is its own 1/2.
defineProps({
  numbers: { type: Array, default: () => ['1', '2'] },
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
    <!-- Step 1 — authorize ----------------------------------------------->
    <section class="step">
      <div class="line">
        <span class="num" :class="{ done: step > 1 }">{{ numbers[0] }}</span>
        <h3>Authorize Calnio in your Notion workspace</h3>
      </div>

      <div class="stepbody">
        <template v-if="step === 1">
          <p class="body">
            Notion asks which pages Calnio may read. Tick the database that holds
            your tasks. Calnio cannot see anything you do not share, and it only
            ever reads.
          </p>

          <button class="btn" type="button" :disabled="state.busy" @click="startConnect">
            {{ state.busy ? 'Opening Notion…' : 'Connect Notion' }}
          </button>

          <p class="note">
            You can revoke this at any time, from Notion's settings or from here.
          </p>
        </template>

        <p v-else class="body">
          Connected to
          <strong>{{ state.connection.workspace_name || 'your workspace' }}</strong>
        </p>
      </div>
    </section>

    <!-- Step 2 — database ------------------------------------------------>
    <section class="step" :class="{ ahead: step < 2 }">
      <div class="line">
        <span class="num">{{ numbers[1] }}</span>
        <h3>Choose the database with your tasks</h3>
      </div>

      <div class="stepbody">
        <template v-if="step === 2">
          <p v-if="state.busy && !fetched" class="body">Loading your databases…</p>

          <template v-else-if="empty">
            <p class="body">
              Calnio can see this workspace, but no databases were shared with it.
              Re-open Notion's dialog and tick the database that holds your tasks.
            </p>
            <button class="btn" type="button" :disabled="state.busy" @click="startConnect">
              {{ state.busy ? 'Opening Notion…' : "Re-open Notion's picker" }}
            </button>
          </template>

          <template v-else>
            <p class="body">
              Calnio reads due dates from here. Only the databases you shared are
              listed.
            </p>

            <ul class="picklist">
              <li v-for="db in state.databases" :key="db.id">
                <label>
                  <input type="radio" :value="db.id" v-model="picked" />
                  <span>{{ db.title || 'Untitled' }}</span>
                </label>
              </li>
            </ul>

            <button
              class="btn"
              type="button"
              :disabled="state.busy || !picked"
              @click="submitDatabase"
            >
              {{ state.busy ? 'Saving…' : 'Use this database' }}
            </button>
          </template>
        </template>

        <p v-else class="body">Available once your workspace is connected.</p>
      </div>
    </section>

    <p v-if="error || state.error" class="error">{{ error || state.error }}</p>
  </div>
</template>

<style scoped>
.setup {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.step {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* A step the user has not reached yet stays visible but recedes. */
.step.ahead {
  opacity: 0.55;
}

.line {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Numbered disc: the only place the app numbers anything, so the shape has to
   carry the sequence without an icon set. */
.num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 1px solid var(--app-border);
  background: var(--app-canvas-subtle);
  font-size: 12px;
  font-weight: 600;
  color: var(--app-fg-muted);
}

.num.done {
  background: var(--app-success-subtle);
  border-color: rgba(31, 136, 61, 0.4);
  color: var(--app-success);
}

h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--app-fg);
}

/* Indented under the numeral, so the sequence reads as one column. */
.stepbody {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
  padding-left: 28px;
}
</style>
