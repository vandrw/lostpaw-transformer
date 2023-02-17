<script lang="ts" setup>
import { onMounted } from "vue";
import { useRouter } from "vue-router";
import { useUserStore, User } from "@/stores/user";
import { useAlertStore } from "@/stores/alert";

const alertStore = useAlertStore();
const userStore = useUserStore();
const router = useRouter();

onMounted(async () => {
  const windowURL = new URL(window.location.href);
  const params = windowURL.searchParams;

  const fetchURL = new URL(windowURL);
  fetchURL.hash = "";
  fetchURL.pathname = "/api/v1/login/confirm";
  fetchURL.search = "";
  fetchURL.searchParams.append("state", params.get("state") || "");
  fetchURL.searchParams.append("code", params.get("code") || "");
  const response = await fetch(fetchURL);

  if (response.status == 200) {
    userStore.login();
    router.push({ path: "/", params: {} });
  } else {
    alertStore.error("Failed to log in, server returned non 200 code.");
  }
});
</script>

<template>
  <h2>Logging in, please wait...</h2>
</template>
