<script setup>
import { computed, ref } from 'vue'
import { useNotion } from '../../composables/useNotion'

// Authorize the workspace. Which database syncs, and into which calendar, is
// picked afterwards. The heading and the numeral belong to whatever renders
// this, so there is no step chrome here.
const notionResult = useNotion()
const state = notionResult.state
const connect = notionResult.connect

const error = ref('')

// The error to show: this wizard's, otherwise the one the callback left behind.
const message = computed(function () {
  if (error.value) {
    return error.value
  }
  return state.error
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
  <div class="column notion">
    <p class="body">
      Notion will ask which pages Calnio may use. Tick every database you might
      want in your calendar, you choose which of them actually syncs in the next
      step. Calnio cannot see anything you do not tick.
    </p>

    <button class="btn" type="button" :disabled="state.busy" @click="startConnect">
      {{ state.busy ? 'Opening Notion…' : 'Connect Notion' }}
    </button>

    <p class="note">Takes one click. You can revoke it from Notion at any time.</p>

    <p v-if="message" class="error">{{ message }}</p>
  </div>
</template>

<style scoped>
.notion {
  --gap: var(--app-gap-stack);
  align-items: flex-start;
}
</style>
