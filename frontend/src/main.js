import { createApp } from 'vue'
// Inter, latin subset only, one file per weight the design uses. Imported
// before the stylesheets so --app-font has a family to name.
import '@fontsource/inter/latin-400.css'
import '@fontsource/inter/latin-500.css'
import '@fontsource/inter/latin-600.css'
import '@fontsource/inter/latin-700.css'
import '@fontsource/inter/latin-800.css'
// tokens.css first: every other file reads a variable from it.
import './styles/tokens.css'
import './styles/layout.css'
import './styles/base.css'
import './styles/components.css'
import './styles/landing.css'
import App from './App.vue'
import { router } from './router'

createApp(App).use(router).mount('#app')
