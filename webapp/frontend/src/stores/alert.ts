import { defineStore } from "pinia";

export interface _Alert {
  message: string;
  type: string;
}

function emptyAlert(): _Alert {
  return {
    message: "",
    type: "",
  };
}

export const useAlertStore = defineStore({
  id: "alert",
  state: () => ({
    alert: emptyAlert(),
  }),
  actions: {
    success(message: string) {
      const type: string = "alert-success";
      this.alert = { message, type };
    },
    error(message: string) {
      const type = "alert-danger";
      this.alert = { message, type };
    },
    clear() {
      this.alert = emptyAlert();
    },
  },
});
