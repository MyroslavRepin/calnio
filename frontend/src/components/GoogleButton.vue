<script setup>
import { useAuth } from '../composables/useAuth'

defineProps({
  label: { type: String, default: 'Continue with Google' },
})

const { login } = useAuth()
</script>

<template>
  <!-- Plain ink button: no Google chrome, no logo mark, no arrow glyph. The
       accent is never used on a button. -->
  <button type="button" class="btn" @click="login">{{ label }}</button>
</template>
