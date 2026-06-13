import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import './assets/tokens.css'
import App from './App.vue'

// Pose le cookie csrftoken avant tout POST vers Django
const BASE = import.meta.env.VITE_API_BASE ?? ''
fetch(`${BASE}/api/csrf/`, { credentials: 'include' }).catch(() => {})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
