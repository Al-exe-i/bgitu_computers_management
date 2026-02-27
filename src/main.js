import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import {useAuthStore} from "@/stores/auth.js";
import {useThemeStore} from "@/stores/theme.js";

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)
const themeStore = useThemeStore(pinia)
const authStore = useAuthStore(pinia)

themeStore.initTheme()

authStore.fetchUser().then(() => {
    app.mount('#app')
})

