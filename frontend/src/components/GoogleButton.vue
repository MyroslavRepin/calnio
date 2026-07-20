<script setup>
import { useAuth } from '../composables/useAuth'

defineProps({
  label: { type: String, default: 'Continue with Google' },
})

const { login } = useAuth()
</script>

<template>
  <button type="button" class="google-btn" @click="login">
    {{ label }}
  </button>
</template>

<style scoped>
/* Monochrome per the design system: no colored Google chrome, no logo mark. */
.google-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-ui);
  font-size: 15px;
  font-weight: 500;
  color: #fff;
  background: var(--accent);
  border: none;
  border-radius: 8px;
  padding: 14px 28px;
  cursor: pointer;
}
</style>
