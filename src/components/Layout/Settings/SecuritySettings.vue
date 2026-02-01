<script>
import api from "@/services/api";
import { useNotificationsStore } from "@/stores/notifications";

export default {
  name: "SecuritySettings",

  data() {
    return {
      loading: false,
      form: {
        current_password: '',
        new_password: '',
        confirm_password: ''
      }
    };
  },

  computed: {
    notify() {
      return useNotificationsStore();
    },
    passwordsMatch() {
      return this.form.new_password === this.form.confirm_password;
    },
    isFormValid() {
      return (
          this.form.current_password.length > 0 &&
          this.form.new_password.length >= 4 &&
          this.passwordsMatch
      );
    }
  },

  methods: {
    async handleChangePassword() {
      if (!this.isFormValid) return;

      this.loading = true;

      try
      {
        await api.post('/users/me/password', {
          current_password: this.form.current_password,
          new_password: this.form.new_password
        });

        this.notify.success('Пароль успешно изменен');

        this.form.current_password = '';
        this.form.new_password = '';
        this.form.confirm_password = '';

      }
      catch (error)
      {
        const msg = error.response?.data?.detail || 'Не удалось изменить пароль';
        this.notify.error(msg);
      }
      finally
      {
        this.loading = false;
      }
    }
  }
};

</script>

<template>
  <div class="security-card">
    <h2 class="section-title">Безопасность</h2>

    <div class="alert-box">
      <div class="alert-icon">🔒</div>
      <div class="alert-text">
        Рекомендуем использовать сложный пароль, содержащий буквы и цифры.
      </div>
    </div>

    <form @submit.prevent="handleChangePassword" class="password-form">
      <!-- Текущий пароль -->
      <div class="form-group">
        <label>Текущий пароль</label>
        <input
            type="password"
            v-model="form.current_password"
            class="form-input"
            required
            placeholder="••••••"
        >
      </div>

      <!-- Новый пароль -->
      <div class="form-group">
        <label>Новый пароль</label>
        <input
            type="password"
            v-model="form.new_password"
            class="form-input"
            required
            placeholder="••••••"
            minlength="4"
        >
      </div>

      <!-- Подтверждение -->
      <div class="form-group">
        <label>Подтвердите новый пароль</label>
        <input
            type="password"
            v-model="form.confirm_password"
            class="form-input"
            :class="{ 'error': !passwordsMatch && form.confirm_password }"
            required
            placeholder="••••••"
        >
        <span v-if="!passwordsMatch && form.confirm_password" class="error-text">
              Пароли не совпадают
            </span>
      </div>

      <button
          type="submit"
          class="save-btn"
          :disabled="loading || !isFormValid"
      >
        {{ loading ? 'Обновление...' : 'Обновить пароль' }}
      </button>
    </form>
  </div>
</template>

<style scoped>
.security-card {
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}
.section-title { margin-bottom: 20px; font-size: 18px; color: #0f172a; }

.alert-box {
  background: #fff7ed;
  border: 1px solid #ffedd5;
  color: #c2410c;
  padding: 15px;
  border-radius: 8px;
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  font-size: 14px;
  line-height: 1.5;
}

.password-form {
  display: grid;
  gap: 20px;
  max-width: 400px;
}

.form-group { display: flex; flex-direction: column; gap: 6px; }

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
}

.form-input {
  padding: 10px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
}

.form-input.error {
  border-color: #ef4444;
}

.error-text {
  font-size: 12px;
  color: #ef4444;
}

.save-btn {
  padding: 10px 20px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  width: fit-content;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.save-btn:hover { background: #2563eb; }
.save-btn:disabled { background: #94a3b8; cursor: not-allowed; }
</style>
