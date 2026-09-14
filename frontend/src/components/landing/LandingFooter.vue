<template>
  <footer class="footer">
    <div class="row footerrow">
      <span class="wordmark">Calnio</span>
      <span class="note">One-way sync. Free while in beta.</span>
      <div class="row links">
        <a href="#how">How it works</a>
        <a href="#start">Get started</a>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  border-top: 1px solid var(--app-border);
  background: var(--app-canvas-subtle);
}

.footerrow {
  --gap: var(--app-gap-block);
  justify-content: space-between;
  max-width: var(--app-width-page);
  margin: 0 auto;
  padding: var(--app-space-5) var(--app-pad-page);
  /* Keeps the last row clear of the iOS home indicator. */
  padding-bottom: calc(var(--app-space-5) + env(safe-area-inset-bottom, 0px));
}

.links {
  --gap: var(--app-gap-block);
}
</style>
