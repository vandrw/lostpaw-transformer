<script setup lang="ts">
import { useRouter } from "vue-router";
import { useUserStore } from "@/stores/user";

const userStore = useUserStore();
const router = useRouter();
// const authStore = useAuthStore();
</script>

<template>
  <nav class="navbar navbar-expand navbar-dark bg-dark">
    <div class="navbar-nav">
      <router-link to="/" class="nav-item nav-link">Map</router-link>
      <router-link
        v-if="!userStore.isLoggedIn"
        to="/login"
        class="nav-item nav-link"
        >Login</router-link
      >
      <router-link
        v-if="userStore.isLoggedIn"
        to="/pets"
        class="nav-item nav-link"
        >Pets</router-link
      >
      <router-link
        v-if="userStore.isLoggedIn"
        to="/missing-pet"
        class="nav-item nav-link"
        >Missing Pet<span
          v-if="router.currentRoute.value.path !== '/missing-pet'"
          >?</span
        ></router-link
      >
    </div>
  </nav>
</template>

<style lang="scss">
// Add a margin to the nav bar elements
.navbar-nav > * {
  margin-right: 0.6rem;
  margin-left: 0.6rem;
}

.navbar-nav > .nav-item {
  margin-top: auto;
  margin-bottom: auto;
}
</style>
