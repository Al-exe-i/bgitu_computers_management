<script>
export default {
  name: "AppFooter"
}
</script>

<template>
  <footer class="site-footer">
    <div class="footer-container">
      <p class="footer-text">
        BGITU Computers Management System
      </p>
    </div>
  </footer>
</template>

<style scoped>
.site-footer {
  position: relative;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  padding: 28px 0;
  margin-top: 1rem;
}

.footer-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.footer-text {
  font-size: 12px;
  color: #6b7280;
  text-align: center;
  font-weight: 500;
}
</style>