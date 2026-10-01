<script setup>
// What Calnio keeps, how, and how to take it back. Every line here is checked
// against the backend: change the code and this copy has to change with it.
const topics = [
  {
    name: 'What I store',
    lines: [
      'Your name, email and avatar from Google sign-in, but no Google tokens. A Notion access token, limited to the pages you share. Your iCloud email and an app-specific password.',
      'For each synced item, its title, its date and the ids that link the page to the event. Never the page content.',
    ],
  },
  {
    name: 'How it is protected',
    lines: [
      'The Notion token and the iCloud password are encrypted before they reach the database. Your session lives in an httpOnly cookie the page cannot read.',
      'Calnio asks for an app-specific password, never your Apple Account password, and you can cancel it on its own at any time.',
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
    name: 'Deleting your account',
    lines: [
      'Settings, Delete account. It removes your account and everything Calnio stores about it, and revokes its Notion access. Events already in your Apple Calendar stay. They are yours.',
    ],
  },
]
</script>

<template>
  <section class="section">
    <div class="container column security">
      <div class="column intro">
        <h2 class="headline">What Calnio keeps, and how to take it back.</h2>
        <p class="tagline">
          Calnio is run by one indie developer, me, on a server I host myself.
          This is everything it holds.
        </p>
      </div>

      <div class="column topics">
        <div v-for="topic in topics" :key="topic.name" class="row topic">
          <h3>{{ topic.name }}</h3>
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
    </div>
  </section>
</template>

<style scoped>
.security {
  --gap: clamp(36px, 5vw, 64px);
}

.intro {
  --gap: 16px;
}

.intro .tagline {
  max-width: 46ch;
}

.topics {
  --gap: 0px;
}

/* Hairline rows, like a spec sheet: the name on the left, the facts beside it. */
.topic {
  --gap: 8px 40px;
  align-items: baseline;
  border-top: 1px solid var(--l-line);
  padding: clamp(22px, 2.6vw, 32px) 0;
}

.topic h3 {
  flex: 0 1 260px;
  font-size: clamp(17px, 1.6vw, 21px);
  font-weight: 700;
  letter-spacing: -0.01em;
}

.topicbody {
  --gap: 10px;
  flex: 1 1 380px;
  max-width: 62ch;
  color: var(--l-muted);
  font-size: 17px;
  line-height: 1.5;
}

.topicbody a {
  color: var(--l-ink);
  font-weight: 600;
  text-decoration: underline;
  text-underline-offset: 2px;
}
</style>
