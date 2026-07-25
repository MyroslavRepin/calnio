<template>
  <header class="head">
    <p class="eyebrow">Settings</p>
    <h1>Settings</h1>
    <p class="lede">
      Nothing to configure yet. These are set by Calnio during beta and become
      yours to change when per-user syncing ships.
    </p>
  </header>

  <dl class="rows">
    <div class="row">
      <dt>Sync interval</dt>
      <dd>set by calnio</dd>
    </div>
    <div class="row">
      <dt>Due date property</dt>
      <dd>set by calnio</dd>
    </div>
    <div class="row">
      <dt>Notion data source</dt>
      <dd>set by calnio</dd>
    </div>
  </dl>
</template>

<style scoped>
.head {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-bottom: 32px;
  max-width: 640px;
}

h1 {
  font-size: 40px;
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.05;
}

.lede {
  font-size: 17px;
  line-height: 1.6;
  color: var(--body);
}

.rows {
  margin: 0;
  border-top: 1px solid var(--hairline);
  max-width: 640px;
}

.row {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 24px;
  padding: 14px 0;
  border-bottom: 1px solid var(--hairline);
}

dt {
  font-size: 15px;
  color: var(--ink);
}

dd {
  margin: 0;
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--muted);
}
</style>
