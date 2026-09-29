<template>
  <!-- The one component both halves of the app import. It is pure brand and
       carries no design system, so it does not break the landing/app split.
       Inline rather than an <img> so the plate flips with whatever it sits on:
       the same mark has to read on the black hero and in the white app bar. -->
  <svg class="mark" viewBox="0 0 240 240" aria-hidden="true">
    <rect width="240" height="240" rx="54" fill="var(--mark-plate, #0a0a0a)" />
    <path
      d="M163.1,158.8 A58,58 0 1 1 163.1,81.2"
      fill="none"
      stroke="var(--mark-glyph, #ffffff)"
      stroke-width="26"
      stroke-linecap="round"
    />
    <rect x="148" y="108" width="24" height="24" rx="7" fill="var(--mark-glyph, #ffffff)" />
  </svg>
</template>

<style scoped>
.mark {
  display: block;
  width: 100%;
  height: 100%;
}
</style>
