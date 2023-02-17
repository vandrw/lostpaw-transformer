<script lang="ts" setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useUserStore, User } from "@/stores/user";

const userStore = useUserStore();
const router = useRouter();

const showForm = ref(false);
const redirectURL = ref(null as string | null);

onMounted(async () => {
  if (await userStore.login()) {
    router.push("/");
    return;
  } else {
    redirectURL.value = userStore.login_redirect_url;
  }
  showForm.value = true;
});
</script>

<template>
  <h2>Login</h2>
  <a v-if="redirectURL !== null" :href="redirectURL">Login using Google</a>
  <form v-if="showForm">
    <!-- Email input -->
    <div class="form-outline mb-4">
      <label class="form-label" for="login-user">Username</label>
      <input type="text" id="login-user" class="form-control" />
    </div>

    <!-- Password input -->
    <div class="form-outline mb-4">
      <label class="form-label" for="login-password">Password</label>
      <input type="password" id="login-password" class="form-control" />
    </div>
  </form>
</template>
