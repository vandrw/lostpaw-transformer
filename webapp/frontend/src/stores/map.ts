import { defineStore } from "pinia";
import { useAlertStore, usePetStore } from "@/stores";
import type { Pet } from "@/stores/pet";

export const useMapStore = defineStore({
  id: "pet_map",
  state: () => ({
    loading: false,
    error: null,
  }),
  actions: {
    async addMarker(pet: Pet) {},
    async createPetLayer() {},
  },
});
