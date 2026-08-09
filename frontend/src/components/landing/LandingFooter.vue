<template>
  <footer class="footer">
    <div class="wrap row footerrow">
      <span class="wordmark">calnio</span>
      <span class="claim">one-way sync · free while in beta</span>
      <div class="row links">
        <a href="#how">How it works</a>
        <a href="#start">Get started</a>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  position: relative;
  z-index: 1;
  border-top: 1px solid var(--hairline-strong);
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(10px);
}

.footerrow {
  --gap: clamp(16px, 4vw, 40px);
  justify-content: space-between;
  padding-top: 28px;
  /* Keeps the last row clear of the iOS home indicator. */
  padding-bottom: calc(28px + env(safe-area-inset-bottom, 0px));
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--link);
}

.links {
  --gap: clamp(16px, 3vw, 24px);
}

.wordmark {
  font-family: var(--font-ui);
  font-size: 19px;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: var(--ink);
}


.links a {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  color: var(--link);
}

.links a:hover {
  color: var(--ink);
}
</style>
