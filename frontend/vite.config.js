import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(function (env) {
  return {
    plugins: [vue()],
    server: { host: true, port: 5173 },
    // The Node build (dist-ssr) is thrown away after prerendering, so it does
    // not need its own copy of the videos in public/.
    build: { copyPublicDir: !env.isSsrBuild },
  }
})
