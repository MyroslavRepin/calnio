<script setup></script>

<template>
  <footer class="footer">
    <div class="wrap inner">
      <span class="wordmark">calnio<span class="dot" aria-hidden="true"></span></span>
      <span class="center">one-way sync · free while in beta</span>
      <div class="links">
        <a href="#how">How it works</a>
        <a href="#dev">Get started</a>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  border-top: 1px solid var(--hairline);
}

.inner {
  padding: 40px var(--pad);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--muted);
}

.wordmark {
  font-size: 17px;
  font-weight: 800;
  letter-spacing: -0.035em;
  color: var(--ink);
}

.links {
  display: flex;
  gap: 20px;
}
</style>
