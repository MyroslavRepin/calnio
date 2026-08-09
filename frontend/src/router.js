import { createRouter, createWebHistory } from 'vue-router'
import LandingView from './views/landing/LandingView.vue'
import ConnectionsView from './views/app/ConnectionsView.vue'
import DashboardLayout from './views/app/DashboardLayout.vue'
import MeView from './views/app/MeView.vue'
import OverviewView from './views/app/OverviewView.vue'
import SettingsView from './views/app/SettingsView.vue'
import WelcomeView from './views/app/WelcomeView.vue'

// No auth guard: bootstrap runs after the router resolves, so a guard reading
// state.user would bounce a signed-in user on every hard refresh.
// DashboardLayout renders the loading and signed-out branches instead.
export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'landing', component: LandingView },
    // Outside DashboardLayout: onboarding takes the whole screen, so it has no
    // sidebar and no dashboard chrome.
    { path: '/welcome', name: 'welcome', component: WelcomeView },
    {
      path: '/dashboard',
      component: DashboardLayout,
      children: [
        { path: '', name: 'dashboard', component: OverviewView },
        { path: 'connections', name: 'connections', component: ConnectionsView },
        { path: 'settings', name: 'settings', component: SettingsView },
        // Absolute child path: the URL stays /me, but the page renders inside
        // the shell, so the sidebar does not disappear on the profile.
        { path: '/me', name: 'me', component: MeView },
      ],
    },
  ],
})
