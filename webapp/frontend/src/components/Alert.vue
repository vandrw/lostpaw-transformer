<script setup lang="ts">
import { storeToRefs } from "pinia";

import { useAlertStore } from "@/stores";

const alertStore = useAlertStore();
const { alert } = storeToRefs(alertStore);
</script>

<template>
  <div v-if="alert.message.length != 0" class="alert-popup">
    <div class="m-3">
      <div class="alert alert-dismissable" :class="alert.type">
        <button @click="alertStore.clear()" class="btn btn-link close">
          &times;
        </button>
        {{ alert.message }}
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Put the alert in the middle of the screen, below the navbar */
.alert-popup {
  position: fixed;
  top: 5rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
}
</style>
