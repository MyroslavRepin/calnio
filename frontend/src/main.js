import { createApp, createSSRApp } from 'vue'
// tokens.css first: every other file reads a variable from it.
import './styles/tokens.css'
import './styles/layout.css'
import './styles/base.css'
import './styles/components.css'
import './styles/landing.css'
import App from './App.vue'
import { router } from './router'

// The marketing pages arrive prerendered, so Vue adopts the markup already on
// screen instead of drawing it again. Every app page arrives with an empty #app
// and is drawn from scratch.
const container = document.getElementById('app')
let app = null
if (container.firstElementChild) {
  app = createSSRApp(App)
} else {
  app = createApp(App)
}
app.use(router)

// The tab title follows the route. The prerender already wrote it into the
// HTML, so this only matters after a click inside the app.
router.afterEach(function (to) {
  if (to.meta.title) {
    document.title = to.meta.title
    return
  }
  document.title = 'Calnio'
})

// Hydration has to meet the same page the prerender drew, so it waits for the
// first route to resolve.
router.isReady().then(function () {
  app.mount(container)
})
