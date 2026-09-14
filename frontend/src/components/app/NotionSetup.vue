<script setup>
import { computed, ref } from 'vue'
import { useNotion } from '../../composables/useNotion'

// One step: authorize the workspace. Which database syncs, and to which
// calendar, is picked per sync afterwards. The number is a prop so the welcome
// page can run this and the Apple wizard as one sequence.
defineProps({
  numbers: {
    type: Array,
    default: function () {
      return ['1']
    },
  },
})

// Everything this wizard does goes through the Notion composable.
const notionResult = useNotion()
const state = notionResult.state
const connect = notionResult.connect

const error = ref('')

// Done once Notion has granted us the workspace.
const connected = computed(function () {
  return Boolean(state.connection)
})

// Notion gives us a workspace name most of the time, but not always.
const workspaceName = computed(function () {
  if (state.connection?.workspace_name) {
    return state.connection.workspace_name
  } else {
    return 'your workspace'
  }
})

// The error to show: the one from this wizard, otherwise the one the OAuth
// callback left behind.
const message = computed(function () {
  if (error.value) {
    return error.value
  } else {
    return state.error
  }
})

async function startConnect() {
  error.value = ''

  const result = await connect()
  if (result.error) {
    error.value = result.error
  }
}
</script>

<template>
  <div class="column setup">
    <section class="column step">
      <div class="row stephead">
        <span class="num" :class="{ done: connected }">{{ numbers[0] }}</span>
        <h3>Authorize Calnio in your Notion workspace</h3>
      </div>

      <div class="column stepbody">
        <template v-if="!connected">
          <p class="body">
            Notion asks which pages Calnio may read. Tick every database you want
            to see in your calendar, you choose which of them syncs afterwards.
            Calnio cannot see anything you do not share, and it only ever reads.
          </p>

          <button class="btn" type="button" :disabled="state.busy" @click="startConnect">
            {{ state.busy ? 'Opening Notion…' : 'Connect Notion' }}
          </button>

          <p class="note">
            You can revoke this at any time, from Notion's settings or from here.
          </p>
        </template>

        <p v-else class="body">
          Connected to <strong>{{ workspaceName }}</strong>
        </p>
      </div>
    </section>

    <p v-if="message" class="error">{{ message }}</p>
  </div>
</template>
