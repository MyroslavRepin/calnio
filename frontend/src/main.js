import { createApp } from 'vue'
// tokens.css first: every other file reads a variable from it.
import './styles/tokens.css'
import './styles/layout.css'
import './styles/base.css'
import './styles/components.css'
import './styles/landing.css'
import App from './App.vue'
import { router } from './router'

createApp(App).use(router).mount('#app')
