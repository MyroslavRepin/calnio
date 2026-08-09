<script setup>
const recentSyncs = [
  { title: 'Write proposal', status: 'Synced', tone: 'success', time: '2 min ago' },
  { title: 'Update deck', status: 'Synced', tone: 'success', time: '10 min ago' },
  { title: 'Fix invoice', status: 'Failed', tone: 'danger', time: '1 hour ago' },
]
</script>

<template>
  <section class="card">
    <div class="card-head">
      <h2>Recent syncs</h2>
    </div>
    <div class="card-body column">
      <section class="card" v-for="sync in recentSyncs">
        <div class="card-body">
          <p>{{ sync.title }}</p>
          <div class="details">
            <p>{{ sync.status }}</p>
            <p>{{ sync.time }}</p>
          </div>
        </div>
      </section>
    </div>
  </section>
</template>

<style scoped>
.card-body {
  width: 100%;
  display: flex;
  justify-content: space-between;
}

.details {
  display: flex;
  gap: --var(gap);
}

.column {
  gap: 0;
}
</style>
