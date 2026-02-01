<script>

import AppHeader from "@/components/Layout/AppHeader.vue";
import LoginModal from "@/components/Layout/LoginModal.vue";
import NotificationsModal from "@/components/Layout/NotificationsModal.vue";

export default {
  name: "AppView",
  components: {NotificationsModal, LoginModal, AppHeader},
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
  <NotificationsModal></NotificationsModal>
</template>

<style>
  :root {
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
    background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
    min-height: 100vh;
    padding: 0;
  }

  .pt-1 {
    padding-top: 1rem !important;
  }
</style>
