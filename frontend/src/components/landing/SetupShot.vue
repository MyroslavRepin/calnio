<template>
  <section class="section">
    <div class="container column setup">
      <div class="column intro">
        <h2 class="headline">Set it up once. Forget about it.</h2>
        <p class="tagline">Pick a Notion database, pick a calendar, flip two-way on.</p>
      </div>

      <!-- A browser frame around the screenshot, so it reads as a page. -->
      <div class="browser">
        <div class="row chrome" aria-hidden="true">
          <i class="light red"></i>
          <i class="light amber"></i>
          <i class="light green"></i>
          <span class="url">calnio.myroslavrepin.com</span>
        </div>
        <img src="/dashboard.png" alt="The Calnio dashboard, showing one sync with two-way turned on." />
      </div>
    </div>
  </section>
</template>

<style scoped>
.setup {
  --gap: clamp(32px, 4vw, 52px);
}

.intro {
  --gap: 12px;
}

.browser {
  border-radius: 16px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 30px 70px -20px rgba(0, 0, 0, 0.25);
}

.chrome {
  --gap: 8px;
  flex-wrap: nowrap;
  height: 40px;
  background: #ececf0;
  padding: 0 16px;
}

.light {
  width: 12px;
  height: 12px;
  flex: none;
  border-radius: 50%;
}

.light.red {
  background: #ff5f57;
}

.light.amber {
  background: #febc2e;
}

.light.green {
  background: #28c840;
}

.url {
  margin-left: 10px;
  background: #fff;
  border-radius: 7px;
  padding: 4px 14px;
  color: #555;
  font-size: 13px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.browser img {
  display: block;
  width: 100%;
}
</style>
