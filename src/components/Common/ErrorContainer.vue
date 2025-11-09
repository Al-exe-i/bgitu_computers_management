<script>
export default {
  name: "ErrorContainer",
  props: ["containerTitle", "errorTitle", "errorText"]
}
</script>

<template>
  <div class="error-container">
    <div class="error-icon-wrapper">
      <div class="error-icon">
        <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
        </svg>
      </div>
    </div>
    <div class="error-content">
      <h2 class="error-title">{{ containerTitle }}</h2>
      <p class="error-message">{{ errorTitle }}</p>
      <div class="error-details">
        <div class="error-details-label">Детали ошибки:</div>
        <div class="error-details-text">{{ errorText }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

body {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 25%, #dbeafe 50%, #e0e7ff 75%, #ede9fe 100%);
  background-size: 400% 400%;
  animation: gradientShift 15s ease infinite;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

@keyframes gradientShift {
  0%   { background-position: 0% 50%; }
  50%  { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}


.error-container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 48px 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15), 0 0 0 1px rgba(255, 255, 255, 0.5) inset;
  border: 1px solid rgba(255, 255, 255, 0.5);
  position: relative;
  overflow: hidden;
  animation: errorAppear 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes errorAppear {
  from { opacity: 0; transform: scale(0.9) translateY(20px); }
  to   { opacity: 1; transform: scale(1) translateY(0); }
}

.error-container::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 5px;
  background: linear-gradient(90deg, #ef4444, #dc2626, #b91c1c);
  background-size: 200% 100%;
  animation: gradientFlow 3s ease infinite;
}

@keyframes gradientFlow {
  0%, 100% { background-position: 0% 50%; }
  50%      { background-position: 100% 50%; }
}

.error-icon-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.error-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #fee2e2, #fecaca);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  animation: iconPulse 2s ease-in-out infinite;
  box-shadow: 0 10px 30px rgba(239, 68, 68, 0.3), 0 0 0 8px rgba(239, 68, 68, 0.1);
}

@keyframes iconPulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 10px 30px rgba(239, 68, 68, 0.3), 0 0 0 8px rgba(239, 68, 68, 0.1);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 15px 40px rgba(239, 68, 68, 0.4), 0 0 0 12px rgba(239, 68, 68, 0.05);
  }
}

.error-icon::before {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  padding: 3px;
  background: linear-gradient(135deg, #ef4444, #dc2626);
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  opacity: 0.5;
}

.error-icon svg {
  width: 40px;
  height: 40px;
  color: #ef4444;
  animation: iconShake 0.5s ease-in-out;
}

@keyframes iconShake {
  0%, 100% { transform: rotate(0deg); }
  25%      { transform: rotate(-10deg); }
  75%      { transform: rotate(10deg); }
}

.error-content {
  text-align: center;
}

.error-title {
  font-size: 24px;
  font-weight: 800;
  color: #dc2626;
  margin-bottom: 12px;
  line-height: 1.3;
}

.error-message {
  font-size: 16px;
  color: #64748b;
  line-height: 1.6;
  margin-bottom: 28px;
  width: 50vw;
}

.error-details {
  background: rgba(248, 250, 252, 0.8);
  backdrop-filter: blur(10px);
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 28px;
  text-align: left;
}

.error-details-label {
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.error-details-text {
  font-size: 14px;
  color: #1f2937;
  font-family: 'Courier New', monospace;
  word-break: break-all;
}




@media (max-width: 640px)
{
  .error-container
  {
    padding: 32px 24px;
  }

  .error-title
  {
    font-size: 20px;
  }

  .error-message
  {
    font-size: 14px;
  }
}
</style>