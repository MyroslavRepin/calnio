import { createSSRApp } from 'vue'
import { renderToString } from 'vue/server-renderer'
import App from './App.vue'
import { router } from './router'
import { questions } from './faq'

// The app compiled for Node, read by prerender.js and nothing else. It never
// serves a request: it runs once per build.

// Draws one address to HTML, and hands back the route it resolved to.
export async function render(url) {
  const app = createSSRApp(App)
  app.use(router)
  await router.push(url)
  await router.isReady()
  const html = await renderToString(app)
  return { html: html, route: router.currentRoute.value }
}

export { router, questions }
