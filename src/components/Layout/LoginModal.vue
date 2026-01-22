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

    async handleLogin() {
      if (!this.validate()) return

      this.serverError = null

      try
      {
        await this.authStore.login(this.email, this.password)

        this.closeModal()
        this.notify.success(`Вы успешно вошли в систему!`, 3500)
      }
      catch (err)
      {
        console.error(err);

        const backendMessage = err.response?.data?.detail;

        let userMsg = 'Ошибка входа';

        if (backendMessage === 'Invalid credentials' || err.response?.status === 401)
        {
          userMsg = 'Неверный логин или пароль!';
        }

        this.notify.error(userMsg);
        this.password = '';
        this.serverError = userMsg;
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
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div class="login-container-inner">
          <img class="login-logo" src="../../assets/logo_IT.png" alt="Logo">
          <h2 class="login-title">Войти в аккаунт</h2>
          <form @submit.prevent="handleLogin" class="login-form">
            <div class="login-form-group">
              <label for="login-email" class="login-label" :class="{'error' : serverError}">Логин</label>
              <div class="input-wrapper">
                <input
                  v-model="email"
                  type="text"
                  id="login-email"
                  name="login"
                  required
                  class="login-input"
                  :class="{ 'error': serverError }"
                  placeholder="Введите ваш логин"
                >
                <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </svg>
              </div>
              <div v-if="errors.email" class="login-error-message">
                {{ errors.email }}
              </div>
            </div>

            <div class="login-form-group">
              <label for="login-password" class="login-label" :class="{'error' : serverError}">Пароль</label>
              <div class="input-wrapper">
                <input
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  id="login-password"
                  name="password"
                  required
                  class="login-input"
                  :class="{ 'error': serverError }"
                  placeholder="Введите ваш пароль"
                >

                <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                </svg>

                <svg @click="showPassword = !showPassword" class="toggle-password" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path v-if="!showPassword" d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                  <circle v-if="!showPassword" cx="12" cy="12" r="3"></circle>
                  <path v-if="showPassword" d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                  <line v-if="showPassword" x1="1" y1="1" x2="23" y2="23"></line>
                </svg>
              </div>
              <div v-if="errors.password" class="login-error-message">
                {{ errors.password }}
              </div>
            </div>

            <button class="login-button" :disabled="authStore.loading">
              {{ authStore.loading ? 'Входим...' : 'Войти' }}
            </button>

          </form>

          <div class="divider">
            <span>или</span>
          </div>

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
  position: absolute;
  top: 20px;
  right: 20px;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  z-index: 10;
}

.close svg
{
  width: 20px;
  height: 20px;
  stroke: rgba(0, 0, 0, 0.7);
}

.close:hover
{
  background: rgba(255, 255, 255, 0.8);
  border-color: rgba(0, 0, 0, 0.12);
  transform: rotate(90deg);
}

.close:hover svg
{
  stroke: rgb(232, 3, 24);
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

.login-container:hover
{
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
  animation: float 3s ease-in-out infinite;
}

@keyframes float
{
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-4px); }
}

.login-logo path {
  fill: var(--login-primary);
}

.login-title {
  font-size: 32px;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.85);
  text-align: center;
  margin-bottom: 32px;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.login-title:hover
{
  color: rgba(59, 130, 246, 0.9);
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

.input-wrapper {
  position: relative;
}

.input-icon {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  color: rgba(0, 0, 0, 0.4);
  pointer-events: none;
  transition: color 0.3s;
}

.toggle-password {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  color: rgba(0, 0, 0, 0.4);
  cursor: pointer;
  transition: color 0.3s;
}

.toggle-password:hover {
  color: rgba(59, 130, 246, 0.8);
}

.login-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.7);
  margin-bottom: 8px;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.5);
}

.login-label.error
{
  color: #dc2626;
}

.login-input {
  width: 100%;
  padding: 14px 48px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  font-family: inherit;
  font-size: 15px;
  transition: all 0.3s;
  color: rgba(0, 0, 0, 0.85);
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(10px);
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.03);
}

.login-input:focus {
  outline: none;
  border-color: rgba(59, 130, 246, 0.4);
  background: rgba(255, 255, 255, 0.7);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1),
  inset 0 2px 4px rgba(0, 0, 0, 0.03);
}

.login-input:focus + .input-icon {
  color: rgba(59, 130, 246, 0.8);
}

.login-input::placeholder {
  color: rgba(0, 0, 0, 0.3);
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

.login-button
{
  width: 100%;
  padding: 16px;
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 12px;
  background: rgba(59, 130, 246, 0.15);
  backdrop-filter: blur(10px);
  color: rgba(59, 130, 246, 1);
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.15),
  inset 0 1px 0 rgba(255, 255, 255, 0.5);
  font-family: inherit;
}

.login-button:hover {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.4);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.5);
}

.login-button:active
{
  transform: translateY(0);
}

.divider {
  text-align: center;
  margin: 32px 0;
  position: relative;
}

.divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0, 0, 0, 0.1), transparent);
}

.divider span {
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 0, 0, 0.08);
  padding: 6px 16px;
  position: relative;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.6);
  border-radius: 20px;
}

.login-signup-link {
  text-align: center;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.6);
}

.login-signup-link a {
  color: rgba(59, 130, 246, 0.9);
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s;
  padding: 4px 8px;
  border-radius: 6px;
}

.login-signup-link a:hover {
  background: rgba(59, 130, 246, 0.1);
  backdrop-filter: blur(10px);
}

::-ms-reveal
{
  display: none;
}

@media (max-width: 480px)
{
  .login-container
  {
    width: 90%;
  }
}
</style>