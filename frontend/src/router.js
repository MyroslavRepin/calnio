import { createRouter, createWebHistory } from 'vue-router'
import LandingPage from './views/LandingPage.vue'
import MeView from './views/MeView.vue'
import WelcomeView from './views/WelcomeView.vue'
import ConnectionsView from './views/dashboard/ConnectionsView.vue'
import DashboardLayout from './views/dashboard/DashboardLayout.vue'
import OverviewView from './views/dashboard/OverviewView.vue'
import SettingsView from './views/dashboard/SettingsView.vue'

// No auth guard: useAuth's bootstrap runs after the router resolves, so a guard
// reading state.user would bounce a logged-in user on every hard refresh.
// DashboardLayout renders the loading / logged-out branch instead.
export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'landing', component: LandingPage },
    // Deliberately outside DashboardLayout: onboarding takes the whole screen,
    // so it has no sidebar and no dashboard chrome.
    { path: '/welcome', name: 'welcome', component: WelcomeView },
    {
      path: '/dashboard',
      component: DashboardLayout,
      children: [
        { path: '', name: 'dashboard', component: OverviewView },
        { path: 'connections', name: 'connections', component: ConnectionsView },
        { path: 'settings', name: 'settings', component: SettingsView },
      ],
    },
    { path: '/me', name: 'me', component: MeView },
  ],
})
