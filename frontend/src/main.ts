import { createApp } from 'vue'
import PrimeVue from 'primevue/config'
import Aura from '@primevue/themes/aura'
import 'primeicons/primeicons.css'
import 'primeflex/primeflex.css'
import './main.css'

import Tooltip from 'primevue/tooltip'
import App from './App.vue'

const app = createApp(App)
app.use(PrimeVue, {
    theme: {
        preset: Aura
    }
})
app.directive('tooltip', Tooltip)
app.mount('#app')
