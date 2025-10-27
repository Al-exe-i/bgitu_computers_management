<script>
export default {
  name: "row",
  props: {
    row: {
      type: Object,
      required: true
    }
  }
}
</script>

<template>
  <div class="row-container">
    <div class="row-header">
      <div class="row-number">{{ row.name.slice(4) }}</div>
      <h2 class="row-title">Ряд 1</h2>
    </div>


  </div>
</template>

<style scoped>
.row-container {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
  padding: 28px;
}

.row-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.row-number {
  width: 52px;
  height: 52px;
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  font-weight: 800;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.row-title {
  font-size: 26px;
  font-weight: 700;
  color: #1f2937;
}

.computers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 20px;
}

.computer-card {
  background: linear-gradient(135deg, #dcfce7, #bbf7d0);
  border: 3px solid #86efac;
  border-radius: 16px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.computer-card.broken {
  background: linear-gradient(135deg, #fee2e2, #fecaca);
  border-color: #fca5a5;
}

.computer-card:hover {
  transform: translateY(-8px) scale(1.02);
  box-shadow: 0 12px 30px rgba(0,0,0,0.15);
}

.computer-icon {
  width: 70px;
  height: 70px;
  margin: 0 auto 16px;
  background: #22c55e;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.computer-card:hover .computer-icon {
  transform: scale(1.1) rotate(5deg);
}

.computer-icon.broken {
  background: #ef4444;
}

.computer-icon svg {
  width: 36px;
  height: 36px;
  color: white;
}

.computer-number {
  font-size: 17px;
  font-weight: 700;
  margin-bottom: 8px;
  color: #1f2937;
}

.computer-status {
  font-size: 14px;
  font-weight: 600;
  color: #16a34a;
}

.computer-status.broken {
  color: #dc2626;
}

.status-dot {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.2);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.2);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(34, 197, 94, 0.1);
  }
}

.status-dot.broken {
  background: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.2);
}

/* Responsive */
@media (max-width: 768px) {
  .computers-grid {
    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
    gap: 12px;
  }
}
</style>