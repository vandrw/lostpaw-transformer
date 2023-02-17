import { defineStore } from "pinia";
import { useAlertStore } from "@/stores";

export class Pet {
  id: number;
  location: {
    lat: number;
    lng: number;
  };
  name: string | null;
  age: number | string | null;
  sex: string | null;
  breed: string | null;
  color: string | null;
  size: string | null;

  constructor(pet: any) {
    this.id = pet.id;
    this.location = pet.location;
    this.name = pet.name ? pet.name : null;
    this.age = pet.age ? pet.age : null;
    this.sex = pet.sex ? pet.sex : null;
    this.breed = pet.breed ? pet.breed : null;
    this.color = pet.color ? pet.color : null;
    this.size = pet.size ? pet.size : null;
  }
}

export const usePetStore = defineStore({
  id: "pets",
  state: () => ({
    pets: new Array<Pet>(),
    loading: false,
    error: null,
  }),
  actions: {
    async add(pet: Pet) {
      // TODO: add pet to system
    },
    async getAll() {
      // TODO: get all pets from system
    },
    async update(id: number, newPet: Pet) {
      // TODO: update pet in system
    },
    async delete(id: number) {
      // TODO: delete pet from system
    },
  },
});
