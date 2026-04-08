<script>
export default {
  name: "NotFoundView",
  computed: {
    currentPath() {
      const rawPath = String(this.$route?.fullPath || "/").trim();

      if (rawPath.length <= 56) {
        return rawPath;
      }

      return `${rawPath.slice(0, 53)}...`;
    },
  },
  methods: {
    goHome() {
      this.$router.push({name: "Home"});
    },

    goBack() {
      if (window.history.length > 1) {
        this.$router.back();
        return;
      }

      this.goHome();
    },
  },
};
</script>

<template>
  <section class="not-found-view">
    <div class="not-found-ambient not-found-ambient-a" aria-hidden="true"></div>
    <div class="not-found-ambient not-found-ambient-b" aria-hidden="true"></div>
    <div class="not-found-grid" aria-hidden="true"></div>

    <div class="not-found-shell">
      <article class="not-found-card">
        <div class="not-found-copy">
          <div class="not-found-heading">
            <div class="not-found-code">404</div>

            <div class="not-found-text-block">
              <h1 class="not-found-title">Страница не найдена</h1>
              <p class="not-found-message">
                Запрошенный раздел недоступен, был перемещён или адрес введён с ошибкой.
              </p>
            </div>
          </div>

          <div class="not-found-actions">
            <button class="nf-btn nf-btn-primary" type="button" @click="goHome">
              На главную
            </button>
            <button class="nf-btn nf-btn-secondary" type="button" @click="goBack">
              Назад
            </button>
          </div>
        </div>

        <aside class="not-found-side">
          <div class="not-found-side-card">
            <span class="not-found-side-label">Адрес</span>
            <code class="not-found-path">{{ currentPath }}</code>
          </div>

          <div class="not-found-tip-list">
            <div class="not-found-tip">
              <div class="not-found-tip-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path
                    d="M9.75 9.75A2.25 2.25 0 0 1 12 7.5h.01A2.24 2.24 0 0 1 14.25 9.74c0 1.3-.86 1.9-1.73 2.48-.83.56-1.77 1.19-1.77 2.53"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="1.8"
                  />
                  <path
                    d="M12 16.5h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="1.8"
                  />
                </svg>
              </div>

              <div class="not-found-tip-copy">
                <strong>Проверьте адрес</strong>
                <span>В ссылке может быть опечатка или устаревший путь.</span>
              </div>
            </div>

            <div class="not-found-tip">
              <div class="not-found-tip-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path
                    d="M4.5 12h15m-7.5-7.5L19.5 12 12 19.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="1.8"
                  />
                </svg>
              </div>

              <div class="not-found-tip-copy">
                <strong>Вернитесь в рабочий раздел</strong>
                <span>Используйте переход назад или вернитесь на главную страницу.</span>
              </div>
            </div>

            <div class="not-found-tip">
              <div class="not-found-tip-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path
                    d="M12 6v6l4 2m5-2a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="1.8"
                  />
                </svg>
              </div>

              <div class="not-found-tip-copy">
                <strong>Если страница была здесь раньше</strong>
                <span>Маршрут мог измениться после обновления системы.</span>
              </div>
            </div>
          </div>
        </aside>
      </article>
    </div>
  </section>
</template>

<style scoped>
.not-found-view {
  --nf-surface:
      linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(248, 250, 252, 0.96));
  --nf-surface-soft: rgba(255, 255, 255, 0.64);
  --nf-border: rgba(148, 163, 184, 0.2);
  --nf-border-strong: rgba(148, 163, 184, 0.28);
  --nf-shadow:
      0 24px 64px rgba(15, 23, 42, 0.12),
      inset 0 1px 0 rgba(255, 255, 255, 0.56);
  --nf-code-fill: linear-gradient(135deg, #0f172a 0%, #1d4ed8 58%, #38bdf8 100%);
  --nf-side-bg: rgba(248, 250, 252, 0.72);
  --nf-side-icon-bg: linear-gradient(135deg, rgba(37, 99, 235, 0.14), rgba(14, 165, 233, 0.12));
  --nf-side-icon-text: #2563eb;
  --nf-tip-text: #475569;
  --nf-path-bg: rgba(15, 23, 42, 0.04);
  --nf-path-text: #0f172a;
  --nf-primary-shadow: 0 14px 32px rgba(37, 99, 235, 0.22);

  position: relative;
  min-height: calc(100vh - 176px);
  padding: clamp(32px, 6vw, 72px) 24px clamp(48px, 8vw, 88px);
  overflow: clip;
}

.not-found-shell {
  position: relative;
  z-index: 1;
  width: min(100%, 1140px);
  margin: 0 auto;
}

.not-found-card {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(280px, 0.92fr);
  gap: 22px;
  padding: clamp(24px, 4vw, 40px);
  border-radius: 34px;
  border: 1px solid var(--nf-border);
  background: var(--nf-surface);
  box-shadow: var(--nf-shadow);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}

.not-found-card::after {
  content: "";
  position: absolute;
  inset: auto -72px -96px auto;
  width: 240px;
  height: 240px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.12), transparent 68%);
  pointer-events: none;
}

.not-found-copy,
.not-found-side {
  position: relative;
  z-index: 1;
}

.not-found-copy {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.not-found-heading {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: clamp(18px, 3vw, 26px);
  align-items: start;
}

.not-found-code {
  font-size: clamp(88px, 16vw, 164px);
  line-height: 0.86;
  font-weight: 900;
  letter-spacing: -0.06em;
  background: var(--nf-code-fill);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  user-select: none;
}

.not-found-text-block {
  padding-top: 10px;
}

.not-found-title {
  margin: 0;
  font-size: clamp(30px, 4vw, 46px);
  line-height: 1.04;
  font-weight: 900;
  color: var(--text-primary, #0f172a);
}

.not-found-message {
  margin: 16px 0 0;
  max-width: 560px;
  font-size: 16px;
  line-height: 1.72;
  color: var(--text-secondary, #64748b);
}

.not-found-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.nf-btn {
  min-height: 48px;
  padding: 0 20px;
  border-radius: 16px;
  border: 1px solid transparent;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition:
      transform 0.2s ease,
      box-shadow 0.2s ease,
      background-color 0.2s ease,
      border-color 0.2s ease,
      color 0.2s ease;
}

.nf-btn:hover {
  transform: translateY(-1px);
}

.nf-btn-primary {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #f8fafc;
  box-shadow: var(--nf-primary-shadow);
}

.nf-btn-primary:hover {
  box-shadow: 0 18px 36px rgba(37, 99, 235, 0.28);
}

.nf-btn-secondary {
  background: rgba(255, 255, 255, 0.58);
  border-color: var(--nf-border-strong);
  color: var(--text-primary, #0f172a);
}

.nf-btn-secondary:hover {
  background: rgba(255, 255, 255, 0.8);
}

.not-found-side {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.not-found-side-card,
.not-found-tip {
  border-radius: 24px;
  border: 1px solid var(--nf-border);
  background: var(--nf-side-bg);
}

.not-found-side-card {
  padding: 18px 20px;
}

.not-found-side-label {
  display: block;
  margin-bottom: 10px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-secondary, #64748b);
}

.not-found-path {
  display: block;
  padding: 12px 14px;
  border-radius: 16px;
  background: var(--nf-path-bg);
  color: var(--nf-path-text);
  font-size: 13px;
  line-height: 1.55;
  white-space: normal;
  word-break: break-word;
}

.not-found-tip-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.not-found-tip {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr);
  gap: 14px;
  padding: 16px 18px;
}

.not-found-tip-icon {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: var(--nf-side-icon-bg);
  color: var(--nf-side-icon-text);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.not-found-tip-icon svg {
  width: 20px;
  height: 20px;
}

.not-found-tip-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.not-found-tip-copy strong {
  font-size: 14px;
  font-weight: 800;
  color: var(--text-primary, #0f172a);
}

.not-found-tip-copy span {
  font-size: 13px;
  line-height: 1.6;
  color: var(--nf-tip-text);
}

.not-found-ambient,
.not-found-grid {
  position: absolute;
  pointer-events: none;
}

.not-found-ambient {
  width: 320px;
  height: 320px;
  border-radius: 50%;
  filter: blur(12px);
  opacity: 0.82;
}

.not-found-ambient-a {
  top: -120px;
  left: max(-60px, 4vw);
  background: radial-gradient(circle, rgba(59, 130, 246, 0.18), transparent 70%);
}

.not-found-ambient-b {
  right: max(-80px, 2vw);
  bottom: -120px;
  background: radial-gradient(circle, rgba(14, 165, 233, 0.14), transparent 72%);
}

.not-found-grid {
  inset: 28px 24px 24px;
  border-radius: 36px;
  background-image:
      linear-gradient(rgba(148, 163, 184, 0.08) 1px, transparent 1px),
      linear-gradient(90deg, rgba(148, 163, 184, 0.08) 1px, transparent 1px);
  background-size: 34px 34px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.18), transparent 72%);
}

:global(html[data-theme='dark']) .not-found-view {
  --nf-surface:
      linear-gradient(180deg, rgba(15, 23, 42, 0.92), rgba(17, 24, 39, 0.96));
  --nf-surface-soft: rgba(15, 23, 42, 0.64);
  --nf-border: rgba(71, 85, 105, 0.56);
  --nf-border-strong: rgba(71, 85, 105, 0.8);
  --nf-shadow:
      0 28px 72px rgba(2, 6, 23, 0.36),
      inset 0 1px 0 rgba(255, 255, 255, 0.04);
  --nf-code-fill: linear-gradient(135deg, #f8fafc 0%, #93c5fd 52%, #38bdf8 100%);
  --nf-side-bg: rgba(15, 23, 42, 0.68);
  --nf-side-icon-bg: linear-gradient(135deg, rgba(37, 99, 235, 0.24), rgba(14, 165, 233, 0.18));
  --nf-side-icon-text: #93c5fd;
  --nf-tip-text: #cbd5e1;
  --nf-path-bg: rgba(2, 6, 23, 0.34);
  --nf-path-text: #e2e8f0;
  --nf-primary-shadow: 0 16px 36px rgba(29, 78, 216, 0.28);
}

:global(html[data-theme='dark']) .not-found-grid {
  background-image:
      linear-gradient(rgba(71, 85, 105, 0.18) 1px, transparent 1px),
      linear-gradient(90deg, rgba(71, 85, 105, 0.18) 1px, transparent 1px);
}

:global(html[data-theme='dark']) .nf-btn-secondary {
  background: rgba(15, 23, 42, 0.72);
  color: #e2e8f0;
}

:global(html[data-theme='dark']) .nf-btn-secondary:hover {
  background: rgba(30, 41, 59, 0.92);
}

@media (max-width: 980px) {
  .not-found-card {
    grid-template-columns: 1fr;
  }

  .not-found-side {
    display: grid;
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .not-found-view {
    min-height: auto;
    padding: 26px 16px 52px;
  }

  .not-found-card {
    padding: 20px;
    border-radius: 26px;
  }

  .not-found-heading {
    grid-template-columns: 1fr;
    gap: 14px;
  }

  .not-found-text-block {
    padding-top: 0;
  }

  .not-found-message {
    font-size: 15px;
  }

  .not-found-actions {
    flex-direction: column;
  }

  .nf-btn {
    width: 100%;
  }
}

@media (max-width: 520px) {
  .not-found-card {
    gap: 16px;
    padding: 16px;
  }

  .not-found-side-card {
    padding: 14px;
    border-radius: 20px;
  }

  .not-found-tip {
    padding: 14px;
    grid-template-columns: 38px minmax(0, 1fr);
    gap: 12px;
    border-radius: 20px;
  }

  .not-found-tip-icon {
    width: 38px;
    height: 38px;
    border-radius: 12px;
  }

  .not-found-grid {
    inset: 20px 12px 18px;
    border-radius: 26px;
    background-size: 26px 26px;
  }
}
</style>
