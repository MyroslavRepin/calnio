<script setup>
import LandingFooter from '../../components/landing/LandingFooter.vue'
import LandingNav from '../../components/landing/LandingNav.vue'
import PageHero from '../../components/landing/PageHero.vue'

// The privacy policy. Every line is checked against the models, the sync code
// and index.html: change what Calnio stores or loads and this copy changes too.

// Everything Calnio keeps in its database, grouped by where it came from.
const collected = [
  {
    name: 'From Google sign-in',
    lines: [
      'Your name, email address, profile picture and Google account id. Calnio asks Google for nothing more than that, and keeps no Google tokens.',
    ],
  },
  {
    name: 'From Notion',
    lines: [
      'An access token limited to the pages you share with Calnio, plus your workspace name and icon. For each database you sync: its id, its name and which date column is used.',
      'From each page, Calnio reads only the title and that date column. Page content is never read.',
    ],
  },
  {
    name: 'From iCloud',
    lines: [
      'Your Apple Account email and an app-specific password, never your Apple Account password. The names and addresses of the calendars Calnio writes to.',
    ],
  },
  {
    name: 'For each synced item',
    lines: [
      'Its title, its start and end, whether it is all day, and the ids that link the Notion page to the calendar event. This is how Calnio tells which side was edited.',
    ],
  },
  {
    name: 'Sync history',
    lines: [
      'When each sync ran, how long it took, how many items it changed, and the error if it failed. Kept for 90 days.',
    ],
  },
]

// What Calnio does with the accounts you connect.
const writes = [
  {
    name: 'In Apple Calendar',
    lines: [
      'Calnio creates calendars named after your databases, and creates, updates and deletes the events in them. Events you made yourself are only changed when two-way sync is on for that calendar.',
    ],
  },
  {
    name: 'In Notion',
    lines: [
      'Nothing, unless you switch two-way sync on for a database. Then Calnio changes the title and date of a page when you edit its event, creates a page for a new event, and moves a page to the trash when you delete its event.',
    ],
  },
]

// Everyone besides me who handles some of it, and why.
const others = [
  {
    name: 'Google, Notion and Apple',
    lines: [
      'The services you connect. Calnio sends them only what a sync needs, and only to your own accounts.',
    ],
  },
  {
    name: 'Cloudflare',
    lines: [
      "Calnio runs on a computer I host myself, and Cloudflare's network connects it to the internet. Every request to calnio.myroslavrepin.com passes through Cloudflare.",
    ],
  },
  {
    name: 'Telegram',
    lines: [
      'When a sync keeps failing, I get a Telegram message with your account email, the database name and the error, so I can fix it.',
    ],
  },
]

// Analytics, cookies and logs: what the site itself records about a visit.
const visits = [
  {
    name: 'Analytics',
    lines: [
      'Calnio uses Umami, which I host myself at analytics.myroslavrepin.com. It counts page views, where visitors came from, device type and page speed.',
      'Its recorder also records clicks and scrolling on every page, signed in or not, for heatmaps and session replays. What you type into a field is masked, but text shown on the screen, such as your database names, can be part of a recording.',
      'No advertising trackers, and no third-party analytics.',
    ],
  },
  {
    name: 'Cookies',
    lines: [
      'Two sign-in cookies that scripts on the page cannot read: one lasts 5 minutes, the other 30 days and keeps you signed in. A short session cookie protects the sign-in itself. No advertising cookies.',
    ],
  },
  {
    name: 'Server logs',
    lines: [
      'Each sync writes what it did to a log, under your account number. Logs are kept for 14 days, warnings and errors for 30. They never contain passwords or tokens.',
    ],
  },
]

// How the stored data is protected, and how a user takes it all back.
const control = [
  {
    name: 'How it is protected',
    lines: [
      'The Notion token and the iCloud password are encrypted before they reach the database. I never sell your data, never share it for advertising, and use Google sign-in data only to create and identify your account.',
    ],
  },
  {
    name: 'Revoking access',
    lines: [
      "Disconnecting Notion in Calnio revokes the grant on Notion's side. You can also remove Calnio in Notion under Settings, Connections.",
    ],
    apple: true,
  },
  {
    name: 'Deleting a sync',
    lines: [
      'Deleting a sync deletes the events it created in Apple Calendar and the links Calnio kept for them. Its run history stays until it is 90 days old or you delete your account.',
    ],
  },
  {
    name: 'Deleting your account',
    lines: [
      'Settings, Delete account removes your account and everything in the database about it at once, and revokes Notion access. Logs age out within 30 days. Events already in Apple Calendar and pages in Notion stay. They are yours.',
    ],
  },
]
</script>

<template>
  <div class="landing-ui column page">
    <LandingNav />

    <main class="column bands">
      <PageHero
        title="Calnio privacy policy"
        lead="Calnio is run by one person, me, on a server I host myself. This page lists everything it collects, why, who else sees it, how long it is kept, and how to delete it."
      />

      <section class="section">
        <div class="container column chapter">
          <div class="column chapterhead">
            <h2 class="headline">What Calnio stores</h2>
            <p class="tagline">
              Only what a sync needs to run. Last updated October 15, 2026.
            </p>
          </div>
          <div class="column topics">
            <div v-for="topic in collected" :key="topic.name" class="row topic">
              <h3 class="topicname">{{ topic.name }}</h3>
              <div class="column topicbody">
                <p v-for="line in topic.lines" :key="line">{{ line }}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="section">
        <div class="container column chapter">
          <h2 class="headline">What Calnio changes in your accounts</h2>
          <div class="column topics">
            <div v-for="topic in writes" :key="topic.name" class="row topic">
              <h3 class="topicname">{{ topic.name }}</h3>
              <div class="column topicbody">
                <p v-for="line in topic.lines" :key="line">{{ line }}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="section">
        <div class="container column chapter">
          <h2 class="headline">Who else handles it</h2>
          <div class="column topics">
            <div v-for="topic in others" :key="topic.name" class="row topic">
              <h3 class="topicname">{{ topic.name }}</h3>
              <div class="column topicbody">
                <p v-for="line in topic.lines" :key="line">{{ line }}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="section">
        <div class="container column chapter">
          <h2 class="headline">Analytics, cookies and logs</h2>
          <div class="column topics">
            <div v-for="topic in visits" :key="topic.name" class="row topic">
              <h3 class="topicname">{{ topic.name }}</h3>
              <div class="column topicbody">
                <p v-for="line in topic.lines" :key="line">{{ line }}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="section">
        <div class="container column chapter">
          <h2 class="headline">Keeping it safe, and taking it back</h2>
          <div class="column topics">
            <div v-for="topic in control" :key="topic.name" class="row topic">
              <h3 class="topicname">{{ topic.name }}</h3>
              <div class="column topicbody">
                <p v-for="line in topic.lines" :key="line">{{ line }}</p>
                <p v-if="topic.apple">
                  For iCloud, revoke the password at
                  <a href="https://appleid.apple.com" target="_blank" rel="noopener">appleid.apple.com</a>,
                  under Sign-In and Security, App-Specific Passwords.
                </p>
              </div>
            </div>
          </div>
          <p class="tagline">
            Questions, or a request to see or delete your data: write to
            <a href="mailto:myroslavrepin@gmail.com?subject=Calnio%20privacy">myroslavrepin@gmail.com</a>.
            When this policy changes, the date at the top changes with it.
          </p>
        </div>
      </section>
    </main>

    <LandingFooter />
  </div>
</template>
