<script setup>
import FinalCta from '../../components/landing/FinalCta.vue'
import LandingFooter from '../../components/landing/LandingFooter.vue'
import LandingNav from '../../components/landing/LandingNav.vue'
import PageHero from '../../components/landing/PageHero.vue'

// The step-by-step guide. Every line is checked against the setup flow and the
// sync code: change either and this copy has to change with it.

// What a reader needs before the first click.
const needs = [
  {
    name: 'A Notion database with a date column',
    lines: [
      'Any database works as long as one column is a date: a due date, a deadline, a meeting time. Calnio reads the title and that date, nothing else on the page.',
    ],
  },
  {
    name: 'An Apple Account with two-factor authentication',
    lines: [
      'Calnio connects to iCloud with an app-specific password, and Apple only lets you create one when two-factor authentication is on. Most accounts already have it.',
    ],
  },
  {
    name: 'A Google account',
    lines: ['It is how you sign in. Calnio keeps your name, email and avatar from it, and no Google tokens.'],
  },
]

// The four steps, in the order the API forces: the calendar has to exist
// before a database can be synced into it.
const steps = [
  {
    name: '1. Sign in with Google',
    lines: ['Signing in for the first time creates your account. There is no form to fill in.'],
    substeps: [],
  },
  {
    name: '2. Connect Notion',
    lines: [
      'Notion opens a page picker. Tick every database you might want in your calendar. Calnio cannot see anything you do not tick, and you choose which of them actually sync in step 4.',
    ],
    substeps: [],
  },
  {
    name: '3. Connect iCloud',
    lines: ['Apple has no sign-in button for calendars, so this step takes an app-specific password.'],
    substeps: [
      'Open appleid.apple.com and sign in.',
      'Go to Sign-In and Security, then App-Specific Passwords.',
      'Choose Generate an app-specific password, name it Calnio, and copy the xxxx-xxxx-xxxx-xxxx it shows.',
      'Paste it into Calnio together with your Apple Account email.',
    ],
  },
  {
    name: '4. Tick your databases',
    lines: [
      'Calnio lists the databases you shared. Tick one or several. For each one it finds the date column, creates a calendar named after the database, and starts the first sync right away.',
    ],
    substeps: [],
  },
]

// What a ticked database turns into on the calendar side.
const results = [
  {
    name: 'One calendar per database',
    lines: [
      'Each database gets its own iCloud calendar, so you can colour it, hide it or share it like any other. If a calendar with that name already exists, Calnio uses it. You can point a sync at another calendar from its card.',
    ],
  },
  {
    name: 'The date column, found for you',
    lines: [
      'A database with one date column needs no decision. With several, Calnio picks the one called Due Date, Due, Deadline, Date, When or Start Date. If none of them match, the sync waits until you pick a column on its card.',
    ],
  },
  {
    name: 'Dates become events',
    lines: [
      'A date without a time becomes an all-day event. A date with a time becomes an event at that time, an hour long unless the Notion date has an end. A date range spans the whole range.',
    ],
  },
  {
    name: 'Checked every 15 minutes',
    lines: [
      'A renamed page or a moved date updates its event on the next run. A page that is trashed, or whose date is cleared, loses its event.',
    ],
  },
]

// The two-way switch, edit by edit.
const edits = [
  { name: 'Move an event', lines: ["The page's date moves with it."] },
  { name: 'Rename an event', lines: ['The page is renamed.'] },
  { name: 'Delete an event', lines: ['The page goes to the Notion trash, where you can still restore it.'] },
  {
    name: 'Create an event',
    lines: [
      'A new page appears in the database. Only events made after you switched two-way on are imported, and only when that calendar belongs to a single sync.',
    ],
  },
]
</script>

<template>
  <div class="landing-ui column page">
    <LandingNav />

    <main class="column bands">
      <PageHero
        title="How to sync Notion with Apple Calendar"
        lead="Calnio puts the dates from your Notion databases into Apple Calendar as real iCloud events, and can send your calendar edits back to Notion. Setup is three connections and about two minutes."
      />

      <section class="section">
        <div class="container column chapter">
          <h2 class="headline">Before you start</h2>
          <div class="column topics">
            <div v-for="need in needs" :key="need.name" class="row topic">
              <h3 class="topicname">{{ need.name }}</h3>
              <div class="column topicbody">
                <p v-for="line in need.lines" :key="line">{{ line }}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="section">
        <div class="container column chapter">
          <h2 class="headline">Set up Notion Apple Calendar sync in four steps</h2>
          <ol class="column topics">
            <li v-for="step in steps" :key="step.name" class="row topic">
              <h3 class="topicname">{{ step.name }}</h3>
              <div class="column topicbody">
                <p v-for="line in step.lines" :key="line">{{ line }}</p>
                <ol v-if="step.substeps.length">
                  <li v-for="substep in step.substeps" :key="substep">{{ substep }}</li>
                </ol>
              </div>
            </li>
          </ol>
        </div>
      </section>

      <section class="section">
        <div class="container column chapter">
          <h2 class="headline">What ends up in Apple Calendar</h2>
          <div class="column topics">
            <div v-for="result in results" :key="result.name" class="row topic">
              <h3 class="topicname">{{ result.name }}</h3>
              <div class="column topicbody">
                <p v-for="line in result.lines" :key="line">{{ line }}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="section">
        <div class="container column chapter">
          <div class="column chapterhead">
            <h2 class="headline">Turn on two-way sync</h2>
            <p class="tagline">
              Each sync has a two-way switch on its card, and it starts off. Switch
              it on, and what you do in Apple Calendar reaches Notion.
            </p>
          </div>
          <div class="column topics">
            <div v-for="edit in edits" :key="edit.name" class="row topic">
              <h3 class="topicname">{{ edit.name }}</h3>
              <div class="column topicbody">
                <p v-for="line in edit.lines" :key="line">{{ line }}</p>
              </div>
            </div>
          </div>
          <p class="tagline">
            When both sides changed since the last run, Notion wins. Repeating
            events and invitations with other attendees are never imported. If you
            connected Notion before two-way existed, the card asks you to reconnect
            once, so Notion can let Calnio edit pages.
          </p>
          <p class="tagline">
            On an iPhone? Read
            <router-link to="/notion-icloud-calendar">Notion dates in your iPhone calendar</router-link>.
            Privacy, data and disconnecting are in the
            <router-link to="/faq">FAQ</router-link>.
          </p>
        </div>
      </section>

      <FinalCta />
    </main>

    <LandingFooter />
  </div>
</template>
