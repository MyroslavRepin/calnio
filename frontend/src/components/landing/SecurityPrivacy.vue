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
          This is everything it holds. More answers are in the
          <router-link to="/faq">FAQ</router-link>.
        </p>
      </div>

      <div class="column topics">
        <div v-for="topic in topics" :key="topic.name" class="row topic">
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
</style>
