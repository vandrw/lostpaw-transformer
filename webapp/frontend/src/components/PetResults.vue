<template>
    <div>
      <h2>Results</h2>
      <hr />
      <img :src="urlFromFile(result.pet_img)" />
      <!-- <div v-if="result.length == 0">
        <h3>No results found</h3>
      </div> -->
      <!-- <div v-else>
        <div v-for="pet in result.compared_pets">
          <img :src="pet.image_url" />
          <h3>{{pet.name}}</h3>
          <p>Similarity: {{pet.similarity}}</p>
        </div>
      </div> -->
    </div>
</template>
  
<script lang="ts">
import { defineComponent} from "vue";

export default defineComponent({
  name: "PetResults",
  props: {
    result: {
      type: Object,
      required: true,
    },
  },
  methods: {
    urlFromFile(file: File) {
      return URL.createObjectURL(file);
    },
  },
});
</script>