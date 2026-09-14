<script setup>
import { useAuth } from '../../composables/useAuth'

defineProps({
  label: { type: String, default: 'Continue with Google' },
  // The green fill appears once per page, so the second call to action asks for
  // the grey one. No Google chrome, no logo mark, no arrow glyph either way.
  plain: { type: Boolean, default: false },
})

const authResult = useAuth()
const login = authResult.login
</script>

<template>
  <button type="button" class="btn" :class="{ plain }" @click="login">
    {{ label }}
  </button>
</template>
