<script lang="ts" setup>
import { ref } from "vue";

const show = ref(false);

function togglePopup() {
  show.value = !show.value;
}

function absorb(e: MouseEvent) {
  e.stopPropagation();
}

defineExpose({ show, togglePopup })

</script>

<template>
  <div v-if="show" class="popup" @click="togglePopup">
    <div class="popup-inner" @click="absorb">
      <slot />
      <button class="popup-close" @click="togglePopup">
        <!-- <font-awesome-icon icon="fa-solid fa-xmark" /> -->
      </button>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.popup {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 999;

  .popup-inner {
    background-color: white;
    padding: 20px;
    border-radius: 5px;
    position: relative;
    // width: 60%;
    max-width: 70%;

    .popup-close {
      position: absolute;
      top: 10px;
      right: 10px;
      border: none;
      background-color: transparent;
      cursor: pointer;
    }
  }
}
</style>
