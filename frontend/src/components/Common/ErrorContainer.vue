<script>
export default {
  name: "ErrorContainer",
  props: {
    containerTitle: {
      type: String,
      default: "Произошла ошибка",
    },
    errorTitle: {
      type: String,
      default: "Не удалось выполнить запрошенное действие.",
    },
    errorText: {
      type: String,
      default: "",
    },
  },
  computed: {
    normalizedErrorText() {
      return String(this.errorText ?? "").trim();
    },

    hasErrorDetails() {
      return Boolean(this.normalizedErrorText);
    },
  },
};
</script>

<template>
  <section class="error-shell" role="alert" aria-live="assertive">
    <article class="error-card">
      <div class="error-layout">
        <aside class="error-side">
          <span class="error-status">
            <span class="error-status-dot"></span>
            Ошибка загрузки
          </span>

          <div class="error-icon-stack" aria-hidden="true">
            <div class="error-icon-glow"></div>
            <div class="error-icon-frame">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 10.5v3.75m-9.303 3.376C1.83 19.126 2.914 21 4.645 21h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 4.88c-.866-1.501-3.032-1.501-3.898 0L2.697 17.626ZM12 17.25h.007v.008H12v-.008Z"/></svg>
            </div>
          </div>
        </aside>

        <div class="error-body">
          <p class="error-kicker">Что-то пошло не так</p>
          <h2 class="error-title">{{ containerTitle }}</h2>
          <p class="error-message">{{ errorTitle }}</p>

          <div v-if="hasErrorDetails" class="error-details-card">
            <div class="error-details-head">
              <span class="error-details-label">Подробности</span>
            </div>
            <p class="error-details-text">{{ normalizedErrorText }}</p>
          </div>
        </div>
      </div>
    </article>
  </section>
</template>

<style scoped>
.error-shell {
  --error-card-border: rgba(203, 213, 225, 0.88);
  --error-card-bg:
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.1), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.98));
  --error-card-shadow:
    0 24px 54px rgba(15, 23, 42, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.72);
  --error-orb-bg: radial-gradient(circle, rgba(59, 130, 246, 0.08), transparent 70%);
  --error-side-border: rgba(203, 213, 225, 0.8);
  --error-side-bg: linear-gradient(180deg, rgba(248, 250, 252, 0.96), rgba(241, 245, 249, 0.82));
  --error-status-border: rgba(248, 113, 113, 0.18);
  --error-status-bg: rgba(254, 242, 242, 0.92);
  --error-status-text: #b91c1c;
  --error-icon-glow: linear-gradient(135deg, rgba(248, 113, 113, 0.14), rgba(59, 130, 246, 0.12));
  --error-icon-border: rgba(248, 113, 113, 0.16);
  --error-icon-bg: linear-gradient(135deg, #fff7ed, #fff1f2 58%, #ffffff);
  --error-icon-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.84),
    0 16px 30px rgba(239, 68, 68, 0.12);
  --error-icon-color: #dc2626;
  --error-kicker-color: #64748b;
  --error-details-border: rgba(203, 213, 225, 0.82);
  --error-details-bg: rgba(248, 250, 252, 0.86);
  --error-details-label: #64748b;
  --error-details-text: #334155;

  width: min(100%, 860px);
  padding: 24px 0;
}

.error-card {
  position: relative;
  overflow: hidden;
  border-radius: 28px;
  border: 1px solid var(--error-card-border);
  background: var(--error-card-bg);
  box-shadow: var(--error-card-shadow);
}

.error-card::after {
  content: "";
  position: absolute;
  inset: auto -60px -70px auto;
  width: 220px;
  height: 220px;
  border-radius: 50%;
  background: var(--error-orb-bg);
  pointer-events: none;
}

.error-layout {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 188px minmax(0, 1fr);
}

.error-side {
  padding: 28px 24px;
  border-right: 1px solid var(--error-side-border);
  background: var(--error-side-bg);
  display: flex;
  flex-direction: column;
  gap: 20px;
  align-items: flex-start;
  justify-content: space-between;
}

.error-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid var(--error-status-border);
  background: var(--error-status-bg);
  color: var(--error-status-text);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  white-space: nowrap;
}

.error-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: currentColor;
}

.error-icon-stack {
  position: relative;
  width: 88px;
  height: 88px;
}

.error-icon-glow {
  position: absolute;
  inset: 10px;
  border-radius: 26px;
  background: var(--error-icon-glow);
  transform: rotate(-10deg);
}

.error-icon-frame {
  position: absolute;
  inset: 0;
  border-radius: 28px;
  border: 1px solid var(--error-icon-border);
  background: var(--error-icon-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--error-icon-shadow);
}

.error-icon-frame svg {
  width: 36px;
  height: 36px;
  color: var(--error-icon-color);
}

.error-body {
  padding: 30px 32px;
}

.error-kicker {
  margin: 0 0 12px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--error-kicker-color);
}

.error-title {
  margin: 0;
  font-size: clamp(24px, 3vw, 32px);
  line-height: 1.12;
  font-weight: 800;
  color: var(--text-primary, #0f172a);
}

.error-message {
  margin: 14px 0 0;
  max-width: 620px;
  font-size: 15px;
  line-height: 1.7;
  color: var(--text-secondary, #64748b);
}

.error-details-card {
  margin-top: 22px;
  padding: 16px 18px;
  border-radius: 18px;
  border: 1px solid var(--error-details-border);
  background: var(--error-details-bg);
}

.error-details-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.error-details-label {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--error-details-label);
}

.error-details-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.65;
  color: var(--error-details-text);
  word-break: break-word;
  white-space: pre-wrap;
}

:global(html[data-theme='dark']) .error-shell {
  --error-card-border: #334155;
  --error-card-bg:
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.14), transparent 28%),
    linear-gradient(180deg, rgba(15, 23, 42, 0.98), rgba(17, 24, 39, 0.96));
  --error-card-shadow:
    0 28px 58px rgba(2, 6, 23, 0.42),
    inset 0 1px 0 rgba(255, 255, 255, 0.04);
  --error-orb-bg: radial-gradient(circle, rgba(59, 130, 246, 0.12), transparent 70%);
  --error-side-border: #334155;
  --error-side-bg: linear-gradient(180deg, rgba(11, 18, 32, 0.9), rgba(15, 23, 42, 0.82));
  --error-status-border: rgba(248, 113, 113, 0.2);
  --error-status-bg: rgba(127, 29, 29, 0.24);
  --error-status-text: #fecaca;
  --error-icon-glow: linear-gradient(135deg, rgba(244, 63, 94, 0.18), rgba(59, 130, 246, 0.14));
  --error-icon-border: rgba(248, 113, 113, 0.16);
  --error-icon-bg: linear-gradient(135deg, rgba(127, 29, 29, 0.34), rgba(30, 41, 59, 0.96));
  --error-icon-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.05),
    0 18px 34px rgba(2, 6, 23, 0.32);
  --error-icon-color: #fda4af;
  --error-kicker-color: #94a3b8;
  --error-details-border: #334155;
  --error-details-bg: rgba(15, 23, 42, 0.76);
  --error-details-label: #94a3b8;
  --error-details-text: #e2e8f0;
}

@media (max-width: 760px) {
  .error-layout {
    grid-template-columns: 1fr;
  }

  .error-side {
    border-right: none;
    border-bottom: 1px solid var(--error-side-border);
    flex-direction: row;
    align-items: center;
  }

  .error-body {
    padding: 24px 24px 26px;
  }
}

@media (max-width: 520px) {
  .error-shell {
    padding: 18px 0;
  }

  .error-card {
    border-radius: 22px;
  }

  .error-side {
    padding: 20px 18px 16px;
    gap: 14px;
  }

  .error-icon-stack {
    width: 74px;
    height: 74px;
  }

  .error-icon-frame {
    border-radius: 22px;
  }

  .error-icon-frame svg {
    width: 30px;
    height: 30px;
  }

  .error-body {
    padding: 20px 18px 22px;
  }

  .error-message {
    font-size: 14px;
    line-height: 1.6;
  }

  .error-details-card {
    margin-top: 18px;
    padding: 14px 15px;
    border-radius: 16px;
  }
}
</style>
