<script setup>
import FinalCta from '../../components/landing/FinalCta.vue'
import LandingFooter from '../../components/landing/LandingFooter.vue'
import LandingNav from '../../components/landing/LandingNav.vue'
import PageHero from '../../components/landing/PageHero.vue'

// The iPhone and iCloud angle on the same product. Every line is checked
// against the sync code: change it and this copy has to change with it.

// What writing into iCloud gives an iPhone that a feed does not.
const reasons = [
  {
    name: 'Real events, not a feed',
    lines: [
      'Calnio writes each item into an iCloud calendar over CalDAV, the protocol Apple Calendar itself uses. To your iPhone it is an event like any other.',
    ],
  },
  {
    name: 'Alerts like any other event',
    lines: [
      'The default alert times you set for Calendar apply to them, so a due date can reach your lock screen or your wrist.',
    ],
  },
  {
    name: 'On every Apple device',
    lines: [
      'iCloud carries the events to every device signed in to your Apple Account: iPhone, iPad, Mac, Apple Watch, and Calendar on iCloud.com.',
    ],
  },
  {
    name: 'Editable from your phone',
    lines: [
      'With two-way switched on, moving, renaming or deleting the event on your iPhone changes the Notion page, and a new event in that calendar becomes a new page.',
    ],
  },
]

// The setup, as it goes on a phone.
const steps = [
  { name: '1. Sign in', lines: ['Open Calnio in Safari and sign in with Google. That creates your account.'] },
  {
    name: '2. Connect Notion',
    lines: ['Notion asks which pages Calnio may use. Tick the databases with the dates you want on your phone.'],
  },
  {
    name: '3. Connect iCloud',
    lines: [
      'At appleid.apple.com, under Sign-In and Security, App-Specific Passwords, generate a password named Calnio. Paste it into Calnio with your Apple Account email. Apple asks for two-factor authentication before it lets you make one.',
    ],
  },
  {
    name: '4. Tick your databases',
    lines: ['Each ticked database becomes an iCloud calendar named after it, and the first sync starts straight away.'],
  },
]

// What to check when the events are not on the phone yet.
const checks = [
  {
    name: 'Look at the calendar list',
    lines: ['Open Calendar, tap Calendars at the bottom, and make sure the new calendar is ticked under iCloud.'],
  },
  {
    name: 'Make sure the phone syncs iCloud Calendar',
    lines: ['If your other iCloud calendars show up on the phone, this is already fine.'],
  },
  {
    name: 'Give it a moment',
    lines: ['The first run usually takes seconds. After that Calnio checks every 15 minutes.'],
  },
  {
    name: 'Read the sync card',
    lines: ["If a run fails, that sync's card in Calnio says what broke."],
  },
]
</script>

<template>
  <div class="landing-ui column page">
    <LandingNav />

    <main class="column bands">
      <PageHero
        title="Notion dates in your iPhone calendar, through iCloud"
        lead="Your iPhone's Calendar app reads iCloud. Calnio writes your Notion due dates into iCloud as ordinary events, so they show up on your iPhone, iPad, Mac and Apple Watch, with no app to install."
      />

      <section class="section">
        <div class="container column chapter">
          <div class="column chapterhead">
            <h2 class="headline">Why iCloud, and not a calendar feed</h2>
            <p class="tagline">
              The usual workaround is a subscribed calendar: a webcal link your
              phone checks now and then. It is read-only, it stays silent, and it
              refreshes when it feels like it.
            </p>
          </div>
          <div class="column topics">
            <div v-for="reason in reasons" :key="reason.name" class="row topic">
              <h3 class="topicname">{{ reason.name }}</h3>
              <div class="column topicbody">
                <p v-for="line in reason.lines" :key="line">{{ line }}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="section">
        <div class="container column chapter">
          <h2 class="headline">Sync Notion with iCloud Calendar from your iPhone</h2>
          <ol class="column topics">
            <li v-for="step in steps" :key="step.name" class="row topic">
              <h3 class="topicname">{{ step.name }}</h3>
              <div class="column topicbody">
                <p v-for="line in step.lines" :key="line">{{ line }}</p>
              </div>
            </li>
          </ol>
          <p class="tagline">
            It works the same on a Mac. What happens to date columns, times and
            ranges is in the
            <router-link to="/notion-apple-calendar-sync">step-by-step Notion Apple Calendar sync guide</router-link>.
          </p>
        </div>
      </section>

      <section class="section">
        <div class="container column chapter">
          <h2 class="headline">If the calendar is not on your iPhone yet</h2>
          <div class="column topics">
            <div v-for="check in checks" :key="check.name" class="row topic">
              <h3 class="topicname">{{ check.name }}</h3>
              <div class="column topicbody">
                <p v-for="line in check.lines" :key="line">{{ line }}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="section">
        <div class="container column chapter">
          <h2 class="headline">What it does not do</h2>
          <p class="tagline">
            Calnio writes to iCloud only, not to Google Calendar or Outlook. It
            syncs the title and the date, so ticking a task done in Notion leaves
            its event where it is. Repeating events and invitations are never
            turned into Notion pages. Anything else you want to know, including
            what Calnio stores, is in the <router-link to="/faq">FAQ</router-link>.
          </p>
        </div>
      </section>

      <FinalCta />
    </main>

    <LandingFooter />
  </div>
</template>
