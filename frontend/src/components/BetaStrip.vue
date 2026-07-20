<script setup></script>

<template>
  <section class="beta">
    <div class="wrap inner">
      <span class="label">Free while in beta</span>
      <p class="body">
        I host Calnio myself, so during the beta it's free, nothing to install,
        nothing to pay.
      </p>
    </div>
  </section>
</template>

<style scoped>
.beta {
  border-top: 1px solid var(--hairline);
  border-bottom: 1px solid var(--hairline);
}

.inner {
  padding: 26px var(--pad);
  display: flex;
  align-items: baseline;
  gap: 28px;
  flex-wrap: wrap;
}

.label {
  font-family: var(--font-mono);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: var(--accent);
  white-space: nowrap;
}

.body {
  font-size: 15px;
  color: var(--body);
}
</style>
