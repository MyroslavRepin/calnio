<script setup></script>

<template>
  <!-- One line, not a bordered strip: the pill is here because this row can
       cross the atmosphere layer. -->
  <section class="beta">
    <div class="wrap inner">
      <span class="pill">Free while in beta</span>
      <p class="body">
        I host Calnio myself. While it is in beta there is nothing to install,
        nothing to run, and nothing to pay.
      </p>
    </div>
  </section>
</template>

<style scoped>
.beta {
  position: relative;
  z-index: 1;
  padding-bottom: clamp(40px, 8vw, 80px);
}

.inner {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: clamp(14px, 3vw, 24px);
}

.body {
  font-size: 15px;
  line-height: 1.6;
  max-width: 52ch;
  color: var(--body-cool);
}
</style>
