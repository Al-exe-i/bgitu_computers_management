<script>
import router from "@/router/index.js";
export default {
  name: "NotFoundView",
  methods: {
    goHome()
    {
      router.push({name: "Home"})
    }
  }
}
</script>

<template>
  <!-- Плавающие формы -->
  <div class="floating-shapes">
    <div class="shape"></div>
    <div class="shape"></div>
    <div class="shape"></div>
  </div>

  <!-- Частицы -->
  <div class="particles" id="particles">
    <div v-for="i in 30" class="particle"
         :style="{'left': Math.random() * 100 + `%`,
         'animationDelay': Math.random() * 15 + `s`,
         'animationDuration': (10 + Math.random() * 10) + `s`}"
    >
    </div>
  </div>

  <!-- Основной контент -->
  <div class="container">

    <div class="error-code">404</div>

    <h1 class="error-title">Упс! Такой страницы нет</h1>

    <p class="error-message">
      Похоже, эта страница решила устроить себе внеплановый отпуск.
      Или же мы случайно отключили не тот кабель... 🔌
    </p>

    <div class="action-buttons">
      <button class="btn btn-secondary" @click="goHome()">
        <span>Перейти на главную</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-size: 400% 400%;
  animation: gradientShift 15s ease infinite;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
}

@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.floating-shapes {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: hidden;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
}

.shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  animation: float 20s infinite ease-in-out;
  opacity: 0.3;
}

.shape:nth-child(1) {
  width: 300px;
  height: 300px;
  background: #ff6b6b;
  top: 10%;
  left: 10%;
  animation-delay: 0s;
}

.shape:nth-child(2) {
  width: 250px;
  height: 250px;
  background: #4ecdc4;
  top: 60%;
  right: 10%;
  animation-delay: 3s;
}

.shape:nth-child(3) {
  width: 200px;
  height: 200px;
  background: #ffe66d;
  bottom: 20%;
  left: 50%;
  animation-delay: 6s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) translateX(0) scale(1);
  }
  33% {
    transform: translateY(-50px) translateX(50px) scale(1.1);
  }
  66% {
    transform: translateY(50px) translateX(-50px) scale(0.9);
  }
}

.container {
  text-align: center;
  padding: 40px;
  position: relative;
  z-index: 10;
}

.error-code {
  font-size: 180px;
  font-weight: 900;
  color: white;
  text-shadow:
      0 0 20px rgba(255, 255, 255, 0.5),
      0 0 40px rgba(255, 255, 255, 0.3),
      0 10px 30px rgba(0, 0, 0, 0.3);
  line-height: 1;
  margin-bottom: 20px;
  animation: glitch 3s infinite;
  position: relative;
}

@keyframes glitch {
  0%, 90%, 100% {
    transform: translate(0);
  }
  92% {
    transform: translate(-2px, 2px);
  }
  94% {
    transform: translate(2px, -2px);
  }
  96% {
    transform: translate(-2px, -2px);
  }
  98% {
    transform: translate(2px, 2px);
  }
}


.error-title {
  font-size: 48px;
  font-weight: 800;
  color: white;
  margin-bottom: 20px;
  text-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  animation: fadeInUp 0.8s ease;
}

.error-message {
  font-size: 20px;
  color: rgba(255, 255, 255, 0.95);
  margin-bottom: 40px;
  line-height: 1.6;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  animation: fadeInUp 0.8s ease 0.2s backwards;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Кнопки */
.action-buttons {
  display: flex;
  gap: 20px;
  justify-content: center;
  flex-wrap: wrap;
  animation: fadeInUp 0.8s ease 0.4s backwards;
}

.btn {
  padding: 16px 40px;
  border-radius: 50px;
  font-size: 18px;
  font-weight: 700;
  text-decoration: none;
  border: none;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s;
}

.btn:hover::before {
  width: 300px;
  height: 300px;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.5);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-5px);
  border-color: white;
}

.btn span {
  position: relative;
  z-index: 1;
}

.particles {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.particle {
  position: absolute;
  width: 6px;
  height: 6px;
  background: white;
  border-radius: 50%;
  opacity: 0.6;
  animation: particleFloat 15s infinite linear;
}

@keyframes particleFloat {
  0% {
    transform: translateY(100vh) translateX(0) rotate(0deg);
    opacity: 0;
  }
  10% {
    opacity: 0.6;
  }
  90% {
    opacity: 0.6;
  }
  100% {
    transform: translateY(-100px) translateX(100px) rotate(360deg);
    opacity: 0;
  }
}

@media (max-width: 768px) {
  .error-code {
    font-size: 120px;
  }

  .error-title {
    font-size: 32px;
  }

  .error-message {
    font-size: 16px;
    padding: 0 20px;
  }

  .btn {
    padding: 14px 30px;
    font-size: 16px;
  }

  .action-buttons {
    flex-direction: column;
    align-items: stretch;
    padding: 0 20px;
  }
}
</style>