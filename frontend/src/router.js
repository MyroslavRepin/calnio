import { createMemoryHistory, createRouter, createWebHistory } from 'vue-router'
import FaqView from './views/landing/FaqView.vue'
import IcloudGuideView from './views/landing/IcloudGuideView.vue'
import LandingView from './views/landing/LandingView.vue'
import NotFoundView from './views/landing/NotFoundView.vue'
import SyncGuideView from './views/landing/SyncGuideView.vue'
import AdminView from './views/app/AdminView.vue'
import ConnectionsView from './views/app/ConnectionsView.vue'
import DashboardLayout from './views/app/DashboardLayout.vue'
import MeView from './views/app/MeView.vue'
import OverviewView from './views/app/OverviewView.vue'
import SettingsView from './views/app/SettingsView.vue'
import SyncsView from './views/app/SyncsView.vue'
import WelcomeView from './views/app/WelcomeView.vue'

// The prerender runs this file in Node, where there is no address bar to read.
function pickHistory() {
  if (import.meta.env.SSR) {
    return createMemoryHistory()
  }
  return createWebHistory()
}

// A route with `public: true` is a marketing page: prerender.js draws it into
// finished HTML with this title and description, lists it in the sitemap with
// `updated` as its lastmod, and lets crawlers index it. Bump `updated` when the
// page's copy changes. Every other route ships as an empty shell marked noindex
// and is drawn in the browser.
//
// No auth guard: bootstrap runs after the router resolves, so a guard reading
// state.user would bounce a signed-in user on every hard refresh.
// DashboardLayout renders the loading and signed-out branches instead.
export const router = createRouter({
  history: pickHistory(),
  routes: [
    {
      path: '/',
      name: 'landing',
      component: LandingView,
      meta: {
        public: true,
        title: 'Calnio: two-way Notion Apple Calendar sync',
        description:
          'Calnio syncs Notion with iCloud Calendar, so your Notion dates show up in your iPhone calendar as real events. Two-way, free, hosted, nothing to install.',
        updated: '2026-10-03',
      },
    },
    {
      path: '/notion-apple-calendar-sync',
      name: 'sync-guide',
      component: SyncGuideView,
      meta: {
        public: true,
        title: 'How to sync Notion with Apple Calendar, step by step · Calnio',
        description:
          'Connect Notion, add an iCloud app-specific password, tick a database. A step-by-step guide to putting Notion dates into Apple Calendar, and getting edits back.',
        updated: '2026-10-03',
      },
    },
    {
      path: '/notion-icloud-calendar',
      name: 'icloud-guide',
      component: IcloudGuideView,
      meta: {
        public: true,
        title: 'Notion tasks in your iPhone calendar with iCloud · Calnio',
        description:
          'Put Notion due dates into iCloud Calendar so they appear on your iPhone, iPad, Mac and Apple Watch. What syncs, what does not, and how to set it up.',
        updated: '2026-10-03',
      },
    },
    {
      path: '/faq',
      name: 'faq',
      component: FaqView,
      meta: {
        public: true,
        title: 'Calnio FAQ: Notion and Apple Calendar sync questions',
        description:
          'Is Calnio free, is it safe, what does it store, one-way or two-way, how often does it sync, and how to disconnect. Straight answers about Calnio.',
        updated: '2026-10-03',
      },
    },
    // Outside DashboardLayout: onboarding takes the whole screen, so it has no
    // sidebar and no dashboard chrome.
    { path: '/welcome', name: 'welcome', component: WelcomeView },
    {
      path: '/dashboard',
      component: DashboardLayout,
      children: [
        { path: '', name: 'dashboard', component: OverviewView },
        { path: 'syncs', name: 'syncs', component: SyncsView },
        { path: 'connections', name: 'connections', component: ConnectionsView },
        { path: 'settings', name: 'settings', component: SettingsView },
        // Reachable by anyone who types it, and empty for them: the API
        // answers 404 unless the account is an admin.
        { path: 'admin', name: 'admin', component: AdminView },
        // Absolute child path: the URL stays /me, but the page renders inside
        // the shell, so the sidebar does not disappear on the profile.
        { path: '/me', name: 'me', component: MeView },
      ],
    },
    // Last, so it only catches what nothing above matched. The server answers
    // those addresses with this page prerendered and a real 404 status.
    {
      path: '/:missing(.*)*',
      name: 'not-found',
      component: NotFoundView,
      meta: { title: 'Page not found · Calnio' },
    },
  ],
  // A click between two marketing pages starts the next one at its top, and
  // the back button returns to where the reader was.
  scrollBehavior: function (to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    return { top: 0 }
  },
})
