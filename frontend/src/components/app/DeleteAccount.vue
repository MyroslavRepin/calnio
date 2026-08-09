<script setup>
import { computed, ref } from 'vue'
import { useAuth } from '../../composables/useAuth'

// Two steps: the trigger only opens the block, and the confirm button stays
// dead until the signed-in email is typed back. The error belongs inside this
// card, next to the button that caused it, so it is not reported upward.
const authResult = useAuth()
const auth = authResult.state
const deleteAccount = authResult.deleteAccount

const confirming = ref(false)
const typedEmail = ref('')
const deleting = ref(false)
const error = ref(null)

const signedInEmail = computed(function () {
  if (auth.user?.email) {
    return auth.user.email
  } else {
    return ''
  }
})

// The confirm button stays dead until the typed email matches the signed-in
// one. Case does not have to match, whitespace does not count.
const canDelete = computed(function () {
  if (signedInEmail.value === '') {
    return false
  }

  const typed = typedEmail.value.trim().toLowerCase()
  const signedIn = signedInEmail.value.toLowerCase()

  if (typed === signedIn) {
    return true
  } else {
    return false
  }
})

function open() {
  confirming.value = true
  error.value = null
}

function cancel() {
  confirming.value = false
  typedEmail.value = ''
  error.value = null
}

async function confirm() {
  if (!canDelete.value || deleting.value) return
  deleting.value = true
  error.value = null

  const result = await deleteAccount(typedEmail.value.trim())
  if (result.error) {
    error.value = result.error
    deleting.value = false
    return
  }

  // A real navigation, not a router push: the composables keep their state at
  // module level, and it would otherwise still be sitting there describing an
  // account that no longer exists.
  window.location.href = '/'
}
</script>

<template>
  <section class="card danger">
    <div class="card-head">
      <h2>Delete account</h2>
    </div>

    <div class="card-body">
      <template v-if="!confirming">
        <p class="body">
          Removes your account and everything Calnio stores about it. This
          cannot be undone.
        </p>
        <button class="btn danger" type="button" @click="open">
          Delete my account
        </button>
      </template>

      <template v-else>
        <p class="body">
          Deleting your account removes your Google sign-in, your iCloud
          password, your Notion connection and everything Calnio remembers
          about what it synced. Calnio's access to your Notion workspace is
          revoked. Events already in your Apple Calendar are yours, they stay,
          and Calnio can no longer remove them. If you ever sign up again,
          remove those old events first, or Apple Calendar may end up with
          duplicates. This cannot be undone.
        </p>

        <label class="column field">
          <span>Type {{ signedInEmail }} to confirm</span>
          <input
            v-model="typedEmail"
            type="email"
            autocomplete="off"
            autocapitalize="none"
            spellcheck="false"
            :disabled="deleting"
          />
        </label>

        <div class="row actions">
          <button
            class="btn danger"
            type="button"
            :disabled="!canDelete || deleting"
            @click="confirm"
          >
            {{ deleting ? 'Deleting…' : 'Delete my account' }}
          </button>

          <button class="btn plain" type="button" :disabled="deleting" @click="cancel">
            Cancel
          </button>
        </div>

        <p v-if="error" class="error">{{ error }}</p>
      </template>
    </div>
  </section>
</template>

<style scoped>
.card-body > * + * {
  margin-top: var(--app-gap-stack);
}

.card.danger {
  border-color: var(--app-danger-line);
}

.card.danger .card-head {
  background: var(--app-danger-tint);
  border-bottom-color: var(--app-danger-line);
}
</style>
