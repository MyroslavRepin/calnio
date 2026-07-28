<template>
  <header class="head">
    <p class="eyebrow">Settings</p>
    <h1 class="title">Settings</h1>
    <p class="lead">
      Nothing to configure yet. Calnio sets these during beta, and they become
      yours to change when per-user syncing ships.
    </p>
  </header>

  <dl class="datarows">
    <div>
      <dt>Sync interval</dt>
      <dd>set by calnio</dd>
    </div>
    <div>
      <dt>Due date property</dt>
      <dd>set by calnio</dd>
    </div>
    <div>
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
  padding-bottom: clamp(24px, 4vw, 32px);
}
</style>
