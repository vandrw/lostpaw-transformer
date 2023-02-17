<script setup lang="ts">
import { RouterView } from "vue-router";
import { Nav, Alert } from "@/components";
import { useUserStore } from "./stores";

const userStore = useUserStore();

userStore.login();
</script>

<template>
  <div class="app-container">
    <Nav />

    <div class="container">
      <Alert />
      <RouterView />
    </div>
  </div>
</template>

<style scoped>
.app-container {
  margin: 0 auto;
  font-weight: normal;
  min-height: 350px;
}

.container {
  margin: 0 auto;
  width: 100%;
}
</style>
