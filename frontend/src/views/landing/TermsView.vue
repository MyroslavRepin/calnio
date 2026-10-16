<script setup>
import LandingFooter from '../../components/landing/LandingFooter.vue'
import LandingNav from '../../components/landing/LandingNav.vue'
import PageHero from '../../components/landing/PageHero.vue'

// The terms of use. Every line about what Calnio does is checked against the
// sync code: change what a sync writes or deletes and this copy changes too.

// What the service is, and what using it means.
const service = [
  {
    name: 'What Calnio is',
    lines: [
      'A hosted service that copies dates from the Notion databases you choose into Apple Calendar, and, when you switch two-way sync on, copies calendar edits back into Notion.',
    ],
  },
  {
    name: 'Agreeing to these terms',
    lines: [
      'By signing in you agree to these terms and to the privacy policy. If you do not agree, do not use Calnio, and delete your account if you have one.',
    ],
  },
  {
    name: 'Free, as it is',
    lines: [
      'Calnio is free. I run it myself, on a computer I host, and I fix what breaks as fast as I can, but I promise no uptime, no support times and no particular feature.',
    ],
  },
]

// What a user is responsible for.
const yours = [
  {
    name: 'Your accounts',
    lines: [
      'You connect only Notion workspaces and Apple Accounts you are allowed to use, and you keep your sign-in safe. What a sync does on your behalf happens in your accounts, under your control.',
    ],
  },
  {
    name: 'Fair use',
    lines: [
      'Do not use Calnio to break the law, to break the terms of Notion or Apple, to get into accounts that are not yours, or to overload or attack the service.',
    ],
  },
  {
    name: 'Your data stays yours',
    lines: [
      'Calnio claims no rights to your pages or events. It holds only what the privacy policy lists, and only to run your syncs.',
    ],
  },
]

// What Calnio changes, said plainly, because it writes into real accounts.
const changes = [
  {
    name: 'What a sync changes',
    lines: [
      'Calnio creates, updates and deletes events in the calendars it creates for your databases. With two-way sync on, it also changes titles and dates in Notion, creates pages for new events, and moves pages to the trash when their events are deleted.',
    ],
  },
  {
    name: 'Keep your own copies',
    lines: [
      'Syncing can go wrong: a changed database, an outage on either side or a bug can move, rename or remove items. Notion keeps trashed pages for a while and iCloud.com can restore an earlier copy of your calendars, but keep your own copies of anything you cannot lose.',
    ],
  },
]

// The legal limits, said once and plainly.
const limits = [
  {
    name: 'No warranty',
    lines: [
      'Calnio is provided as it is and as available, without warranty of any kind, including that it is fit for a particular purpose or free of errors.',
    ],
  },
  {
    name: 'Limit of liability',
    lines: [
      'As far as the law allows, I am not liable for lost data, missed events or any indirect damage that comes from using Calnio. My total liability is limited to what you paid for Calnio, which is nothing.',
    ],
  },
  {
    name: 'Ending it',
    lines: [
      'You can delete your account at any time in Settings. I may suspend an account that breaks these terms, and I may shut Calnio down. If I do, I will say so by email first, with time to move your data.',
    ],
  },
  {
    name: 'Changes to these terms',
    lines: [
      'When these terms change, the date at the top changes with them. Using Calnio after a change means you accept the new terms.',
    ],
  },
]
</script>

<template>
  <div class="landing-ui column page">
    <LandingNav />

    <main class="column bands">
      <PageHero
        title="Calnio terms of use"
        lead="Calnio is free and run by one person, me. These are the few rules for using it, and what I can and cannot promise."
      />

      <section class="section">
        <div class="container column chapter">
          <div class="column chapterhead">
            <h2 class="headline">The service</h2>
            <p class="tagline">Last updated October 15, 2026.</p>
          </div>
          <div class="column topics">
            <div v-for="topic in service" :key="topic.name" class="row topic">
              <h3 class="topicname">{{ topic.name }}</h3>
              <div class="column topicbody">
                <p v-for="line in topic.lines" :key="line">{{ line }}</p>
              </div>
            </div>
          </div>
          <p class="tagline">
            What Calnio stores, and how to delete it, is in the
            <router-link to="/privacy">privacy policy</router-link>.
          </p>
        </div>
      </section>

      <section class="section">
        <div class="container column chapter">
          <h2 class="headline">Your part</h2>
          <div class="column topics">
            <div v-for="topic in yours" :key="topic.name" class="row topic">
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
            <div v-for="topic in changes" :key="topic.name" class="row topic">
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
          <h2 class="headline">Limits</h2>
          <div class="column topics">
            <div v-for="topic in limits" :key="topic.name" class="row topic">
              <h3 class="topicname">{{ topic.name }}</h3>
              <div class="column topicbody">
                <p v-for="line in topic.lines" :key="line">{{ line }}</p>
              </div>
            </div>
          </div>
          <p class="tagline">
            Questions about these terms: write to
            <a href="mailto:myroslavrepin@gmail.com?subject=Calnio%20terms">myroslavrepin@gmail.com</a>.
          </p>
        </div>
      </section>
    </main>

    <LandingFooter />
  </div>
</template>
