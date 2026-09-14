<script setup>
import { ref } from 'vue'
import MappingAdd from '../../components/app/MappingAdd.vue'
import MappingCard from '../../components/app/MappingCard.vue'
import { useAppleCalendar } from '../../composables/useAppleCalendar'
import { useMappings } from '../../composables/useMappings'
import { useNotion } from '../../composables/useNotion'
import { useSync } from '../../composables/useSync'

// Every sync the user has, one card each, plus the card that adds another.
const mappingsResult = useMappings()
const mappings = mappingsResult.state

const notionResult = useNotion()
const notion = notionResult.state

const appleResult = useAppleCalendar()
const apple = appleResult.state

const syncResult = useSync()
const sync = syncResult.state

// One error box for the page, at the bottom and outside every card. Every card
// reports into it.
const error = ref(null)
</script>

<template>
  <p v-if="!mappings.ready || !notion.ready || !apple.ready" class="loading">Loading…</p>

  <template v-else>
    <header class="column page-head">
      <h1 class="title">Syncs</h1>
      <p class="lead">
        Each sync reads one Notion database and writes its due dates into one
        Apple calendar. Notion is never written to.
      </p>
    </header>

    <!-- Nothing can be set up without both grants, so say which one is missing
         rather than showing a picker that cannot work. -->
    <section v-if="!notion.connection || !apple.connection" class="card">
      <div class="card-head">
        <h2>Connect your accounts first</h2>
        <span class="label attention">Not connected</span>
      </div>
      <div class="card-body">
        <p class="body">
          A sync needs a Notion workspace to read and an iCloud account to write
          to. Connect them, then come back here.
        </p>
        <router-link class="btn" :to="{ name: 'connections' }">Connections</router-link>
      </div>
    </section>

    <template v-else>
      <p v-if="!sync.settings?.enabled && mappings.list.length" class="note">
        Syncing is switched off for your whole account, so none of these run.
        <router-link :to="{ name: 'settings' }">Settings</router-link>
      </p>

      <MappingCard
        v-for="mapping in mappings.list"
        :key="mapping.id"
        :mapping="mapping"
        @error="error = $event"
      />

      <MappingAdd @error="error = $event" />
    </template>

    <p v-if="error" class="error pageerror">{{ error }}</p>
  </template>
</template>

<style scoped>
.note {
  margin-bottom: var(--app-gap-block);
}

.pageerror {
  margin-top: var(--app-gap-block);
}
</style>
