import { defineStore } from "pinia";
import { useAlertStore } from "@/stores";

export class User {
  email: string;

  constructor(email: string) {
    this.email = email;
  }
}

export const useUserStore = defineStore({
  id: "user",
  state: () => ({
    user: null as User | null,
    login_redirect_url: null as string | null,
  }),
  actions: {
    async login(): Promise<boolean> {
      if (this.user) {
        return true;
      }

      const response = await fetch("/api/v1/login", { method: "POST" });
      const data = await response.json();

      if (data.action === "done") {
        this.user = new User(data.email);
      } else if (data.action === "redirect") {
        this.login_redirect_url = data.url;
      }
      return this.isLoggedIn;
    },
  },
  getters: {
    isLoggedIn(): boolean {
      return this.user !== null;
    },
  },
});
