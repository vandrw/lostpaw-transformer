import { createApp } from "vue";
import { createPinia } from "pinia";

import App from "./App.vue";
import router from "./router";

/* import font awesome icon component */
import { library } from '@fortawesome/fontawesome-svg-core';
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { faDog } from '@fortawesome/free-solid-svg-icons'

import "./assets/base.css";

library.add(faDog);

const pinia = createPinia()
const app = createApp(App);

app.use(pinia);
app.use(router);
app.component("font-awesome-icon", FontAwesomeIcon);

app.mount("#app");
