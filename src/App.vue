<script>

import AppHeader from "@/components/appHeader.vue";
import LoginModal from "@/components/loginModal.vue";

export default {
  name: "AppView",
  components: {LoginModal, AppHeader},
  data()
  {
    return {
      isLoginModalOpen: false,
    }
  },
  methods: {
  }
}
</script>

<template>
  <app-header @open-login="isLoginModalOpen = true"></app-header>
  <login-modal :is-open="isLoginModalOpen" @close="this.isLoginModalOpen = false"></login-modal>
  <router-view></router-view>
</template>

<style>
  :root {
    --login-primary: #6366F1;
    --login-secondary: #A855F7;
    --login-accent: #EC4899;
    --login-background: #F3F4F6;
    --login-text: #1F2937;
    --login-error: #EF4444;
  }

  *
  {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  }

  body
  {
    background: linear-gradient(135deg, #e0f7fa, #bbdefb);
    min-height: 100vh;
    padding: 0;
  }
</style>
