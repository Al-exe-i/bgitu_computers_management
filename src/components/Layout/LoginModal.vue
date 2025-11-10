<script>
import { useAuthStore } from '@/stores/auth.js'
import {useNotificationsStore} from "@/stores/notifications.js";

export default {
  name: 'LoginModal',
  props: {
    isOpen: {
      type: Boolean,
      required: true
    }
  },
  emits: ['close'],
  data() {
    return {
      email: '',
      password: '',
      showPassword: false,
      serverError: null,
      errors: {
        email: null,
        password: null
      },
      hidden: null,
    }
  },
  computed: {
    authStore()
    {
      return useAuthStore()
    },
    notify()
    {
      return useNotificationsStore()
    }
  },
  methods: {
    validate()
    {
      let valid = true
      this.errors.email = null
      this.errors.password = null

      if (!this.email)
      {
        this.errors.email = 'Введите email'
        valid = false
      }
      // } else if (!/\S+@\S+\.\S+/.test(this.email)) {
      //   this.errors.email = 'Введите корректный email'
      //   valid = false
      // }

      if (!this.password)
      {
        this.errors.password = 'Введите пароль'
        valid = false
      }

      return valid
    },

    async handleLogin()
    {
      if (!this.validate()) return

      this.serverError = null

      try
      {
        await this.authStore.login(this.email, this.password)
        await this.authStore.fetchUser()
        this.closeModal()
        this.notify.success(`Вы успешно вошли в систему!`, 3500)
      }
      catch (err)
      {
        let errMsg = this.authStore.error === `Invalid credentials` ? `Неверный логин или пароль!` : `Ошибка входа`
        this.notify.error(errMsg)
        this.password = ''
        this.serverError = this.authStore.error || 'Ошибка входа'
      }
    },

    closeModal()
    {
      this.email = ''
      this.password = ''
      this.hidden = true
      this.serverError = this.errors.email = this.errors.password = null
      setTimeout(()=>{this.$emit('close'); this.hidden = null}, 700)
    }
  }
}
</script>


<template>
  <div v-if="isOpen" class="container-in">
    <div class="centre">
      <div class="login-container" :class="{'hidden': hidden}">
        <div class="close-container">
          <button class="close" @click="closeModal">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24">
              <path fill="none" stroke="#f10e3c" stroke-linecap="round" stroke-width="2" d="M20 20L4 4m16 0L4 20"></path>
            </svg>
          </button>
        </div>
        <div class="login-container-inner">
          <img class="login-logo" src="../../assets/logo_IT.png" alt="Logo">
          <h2 class="login-title">Войти в аккаунт</h2>
          <form @submit.prevent="handleLogin" class="login-form">
            <div class="login-form-group">
              <label for="login-email" class="login-label" :class="{'error' : serverError}">Логин</label>
              <input
                  v-model="email"
                  type="text"
                  id="login-email"
                  name="login"
                  required
                  class="login-input"
                  :class="{ 'error': serverError }"
              >
              <div v-if="errors.email" class="login-error-message">
                {{ errors.email }}
              </div>
            </div>

            <div class="login-form-group">
              <label for="login-password" class="login-label" :class="{'error' : serverError}">Пароль</label>
              <input
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  id="login-password"
                  name="password"
                  required
                  class="login-input"
                  :class="{ 'error': serverError }"
              >
              <div v-if="errors.password" class="login-error-message">
                {{ errors.password }}
              </div>
              <div class="login-show-password">
                <input type="checkbox" id="login-showPassword" v-model="showPassword">
                <label class="checkbox-label" for="login-showPassword">Показать пароль</label>
              </div>
            </div>

            <button class="login-button" :disabled="authStore.loading">
              {{ authStore.loading ? 'Входим...' : 'Войти' }}
            </button>

          </form>
          <div class="login-signup-link">
            Нет аккаунта? <a href="mailto:mail@gmail.com?subject=Создание аккаунта&body=Здравствуйте, мне нужно создать аккаунт">Напишите нам</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>

.container-in {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 100;
}


.close-container
{
  display: flex;
  justify-content: end;
}

.close
{
  display: block;
  width: 65px;
  height: 65px;
  border-radius: 50px;
  border: none;
  background: none;
  cursor: pointer;
  transition: all 550ms ease;
}

.close:hover
{
  scale: 110%;
}

.login-container {
  max-width: 400px;
  width: 100%;
  margin: 2rem auto;
  background: white;
  border-radius: 1.5rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 1;
  animation: login-fadeIn 0.8s ease-out;
}


.login-container-inner
{
  padding: 2.5rem;
}

.login-container:hover {
  transform: translateY(-5px);
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
}

.login-container.hidden
{
  animation: login-fadeOut .8s ease-out !important;
}

@keyframes login-fadeIn {
  from {opacity: 0; transform: translateY(20px);}
  to {opacity: 1; transform: translateY(0);}
}

@keyframes login-fadeOut {
  from {opacity: 1; transform: translateY(0);}
  to {opacity: 0; transform: translateY(20px);}
}

.login-logo {
  width: 3rem;
  height: 3rem;
  margin: 0 auto 1.5rem;
  display: block;
  transition: transform .8s ease-in-out;
}

.login-logo:hover{
  transform: rotate(360deg);
}

.login-logo path {
  fill: var(--login-primary);
}

.login-title {
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--login-text);
  text-align: center;
  margin-bottom: 0.5rem;
  transition: .4s hover ease;
}

.login-title:hover
{
  color: #1e40af;
  text-shadow: 1px 1px 3px rgba(0,0,0,0.1);
  cursor: default;
}


.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.login-form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.login-label {
  font-size: 0.875rem;
  color: #4B5563;
}

.login-label.error
{
  color: #dc2626;
}

.login-input {
  padding: 0.75rem 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 0.5rem;
  font-size: 1rem;
  transition: all 0.3s ease;
  width: 100%;
  box-sizing: border-box;
}

.login-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
}

.login-error-message
{
  color: var(--login-error);
  font-size: 1rem;
}

.error
{
  border-color: #dc2626;
}

.login-show-password {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.login-show-password input {
  width: 1rem;
  height: 1rem;
  accent-color: #2563eb;
  cursor: pointer;
}

.login-show-password label
{
  cursor: pointer;
}

.login-button
{
  padding: 14px;
  border-radius: 12px;
  font-weight: 700;
  font-size: 16px;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
}

.login-signup-link {
  text-align: center;
  margin-top: 1.5rem;
  font-size: 0.875rem;
  color: #6B7280;
}

.login-signup-link a {
  color: var(--login-primary);
  text-decoration: none;
  font-weight: 500;
  text-shadow: none !important;
}

.login-signup-link a:hover {
  color: #4F46E5;
}

.checkbox-label
{
  font-size: 0.875rem;
  color: #4B5563;
}

@media (max-width: 480px)
{
  .login-container
  {
    width: 90%;
  }
}
</style>