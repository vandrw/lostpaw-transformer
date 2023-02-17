import { createRouter, createWebHistory } from "vue-router";
import MapView from "./views/MapView.vue";
import PetsView from "./views/PetsView.vue";
import Login from "./views/LoginView.vue";
import LoginConfirm from "./views/LoginConfirmView.vue";
import MissingPet from "./views/MissingPetView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "home",
      component: MapView,
    },
    {
      path: "/pets",
      name: "pets",
      component: PetsView,
      meta: {
        auth: true, // A protected route
      },
    },
    {
      path: "/missing-pet",
      name: "missing-pet",
      component: MissingPet,
      meta: {
        auth: true, // A protected route
      },
    },
    {
      path: "/login",
      name: "login",
      component: Login,
    },
    {
      path: "/login/confirm",
      name: "confirm-login",
      component: LoginConfirm,
    },
  ],
});

// router.beforeEach((from, to) => {
//   return !to.meta.auth;
// })

export default router;
