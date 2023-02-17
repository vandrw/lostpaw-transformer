<template>
  <div>
    <button @click="togglePopup">
      <font-awesome-icon icon="fa-solid fa-dog" />
    </button>
    <Popup ref="pic_upload">
      <ImageUpload @files-uploaded="togglePopup" @pet-results="toggleResults" />
    </Popup>
    <Popup ref="pic_results">
      <div class="popup-content">
        <h2>Input image</h2>
        <img v-if="pet_result.pet_image" :src="urlFromFile(pet_result.pet_image)" />
        
        <hr />
        <h2>Results</h2>
        <div v-if="pet_result.length == 0">
          <h3>No results found</h3>
        </div>
        <div v-else>
          <div v-for="pet in pet_result.compared_pets" :key="pet.name">
            <img :src="pet.image_url" />
            <h3>{{ pet.name }}</h3>
            <ul>
              <li>Similarity: {{100/pet.distance}}</li>
              <li>Latent space distance: {{pet.distance}}</li>
            </ul>
          </div>
        </div>
      </div>
      <!-- <PetResults :result="pet_result"/> -->
    </Popup>
  </div>
</template>

<script lang="ts" setup>
import { ref } from "vue";
import { Popup, ImageUpload, PetResults } from "@/components";

const pic_upload = ref<InstanceType<typeof Popup> | null>(null);
const pic_results = ref<InstanceType<typeof Popup> | null>(null);
let pet_result: any = null;

function togglePopup() {
  pic_upload.value?.togglePopup();
}

function toggleResults(result: any) {
  pic_upload.value?.togglePopup();
  console.log(result);
  pet_result = result;
  pic_results.value?.togglePopup();
}

function urlFromFile(file: File) {
  return URL.createObjectURL(file);
}
</script>

<style scoped>
.popup-content {
  max-height: 70vh;
  overflow: scroll;
}

.popup-content>div>div {
  margin-bottom: 2rem;
}

img {
  max-width: 25rem;
}

button {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  padding: 1rem;
  border-radius: 2rem;
  font-size: 1.5rem;

  /* Make the button into a circle */
  width: 5rem;
  height: 5rem;

  animation: rainbow 30s linear infinite;
  /* transition: background-color ; */
  border: 4px solid white;
  box-shadow: 0px 0px 10px black;
  text-shadow: 0px 0px 5px white;
}

button:active {
  border-color: black;
  box-shadow: 0px 0px 10px white;
}

button:hover {
  border-color: gray;
}

@keyframes rainbow {
  0% {
    background-color: #61fadb;
  }

  20% {
    background-color: #4685d4;
  }

  40% {
    background-color: #895aeb;
  }

  60% {
    background-color: #d66fc5;
  }

  80% {
    background-color: #f5a290;
  }

  100% {
    background-color: #61fadb;
  }
}
</style>