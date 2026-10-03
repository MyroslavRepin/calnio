// The FAQ, one list read twice: FaqView draws it, and prerender.js turns it into
// FAQPage JSON-LD, so the structured data never says what the page does not.
// Every answer is checked against the backend: change the code and this copy
// has to change with it. Each answer is a list of paragraphs, plain text only.
export const questions = [
  {
    question: 'Is Calnio free?',
    answer: [
      'Yes. There is no paid plan, no trial and no card to enter. I host Calnio myself, on a Raspberry Pi on my desk, and I use it for my own tasks every day.',
    ],
  },
  {
    question: 'Is Calnio safe to connect to Notion and iCloud?',
    answer: [
      'Calnio asks for as little as it can. When you connect Notion, Notion shows a page picker, and Calnio can only see the pages and databases you tick there.',
      'For iCloud it uses an app-specific password, never your Apple Account password. You can revoke that one password at any time without touching anything else.',
      'The Notion token and the iCloud password are encrypted before they reach the database. Your session lives in an httpOnly cookie that the page itself cannot read.',
    ],
  },
  {
    question: 'What data does Calnio store?',
    answer: [
      'Your name, email address and avatar from Google sign-in, but no Google tokens. A Notion access token. Your iCloud email and app-specific password.',
      'For each sync: which database, which date column and which calendar. For each synced item: its title, its start and end, whether it is all day, and the ids that link the Notion page to the calendar event. Never the content of your pages.',
    ],
  },
  {
    question: 'Is the sync one-way or two-way?',
    answer: [
      'Notion to Apple Calendar always runs: a new date, a moved date, a renamed page or a trashed page all reach the calendar.',
      'Apple Calendar to Notion is a switch on each sync, off until you turn it on. With it on, moving an event changes the page date, renaming it renames the page, deleting it moves the page to the trash, and an event you create in that calendar becomes a new page.',
      'When both sides changed since the last run, Notion wins. Repeating events and invitations with other attendees are never imported.',
    ],
  },
  {
    question: 'How often does Calnio sync?',
    answer: [
      'Every 15 minutes. When you add a database or switch syncing on, the first run starts right away instead of waiting for the next round.',
    ],
  },
  {
    question: 'Which calendar do the events go into?',
    answer: [
      'Each database gets its own calendar in iCloud, named after the database. If a calendar with that name already exists, Calnio uses it. You can point a sync at another calendar from its card.',
    ],
  },
  {
    question: 'Why does Calnio need an app-specific password?',
    answer: [
      'Apple has no sign-in button for calendar access. iCloud Calendar speaks CalDAV, which takes an email and a password, and Apple only accepts app-specific passwords there. Creating one needs two-factor authentication on your Apple Account.',
    ],
  },
  {
    question: 'What happens when I tick a task done in Notion?',
    answer: [
      'Nothing changes in the calendar. Calnio syncs the title and the date. A page leaves the calendar when it is trashed or its date is cleared.',
    ],
  },
  {
    question: 'Does it work with Google Calendar or Outlook?',
    answer: ['No. Calnio writes to iCloud Calendar only, which is what Apple Calendar shows on your iPhone, iPad and Mac.'],
  },
  {
    question: 'How do I disconnect Calnio?',
    answer: [
      'To pause, turn off a sync on the Syncs page, or everything at once in Settings. Deleting a sync also deletes the events it created.',
      "Disconnecting Notion under Connections revokes the grant on Notion's side. Disconnecting Apple Calendar leaves the events already in your calendar. Revoke the iCloud password at appleid.apple.com, under Sign-In and Security, App-Specific Passwords.",
      'Settings, Delete account removes everything Calnio stores about you and revokes its Notion access. Events already in Apple Calendar stay. They are yours.',
    ],
  },
]
