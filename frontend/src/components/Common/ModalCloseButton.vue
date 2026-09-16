<template>
  <button type="button" class="modal-round-close" aria-label="Закрыть" title="Закрыть">
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
      <path d="m6 6 12 12M18 6 6 18" />
    </svg>
  </button>
</template>

<style scoped>
.modal-round-close {
  --close-bg: #f1f5f9;
  --close-hover: #e2e8f0;
  --close-ink: #475569;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 36px;
  width: 36px;
  height: 36px;
  padding: 8px;
  border: 0;
  border-radius: 50%;
  background: var(--close-bg);
  color: var(--close-ink);
  cursor: pointer;
  transition: background-color 160ms ease-out, color 160ms ease-out;
}
.modal-round-close svg { width: 20px; height: 20px; }
.modal-round-close:focus-visible { outline: 2px solid #3b82f6; outline-offset: 3px; }
.modal-round-close:disabled { opacity: .45; cursor: default; }
html[data-theme='dark'] .modal-round-close {
  --close-bg: #1e293b;
  --close-hover: #334155;
  --close-ink: #cbd5e1;
}
@media (hover: hover) {
  .modal-round-close:hover:not(:disabled) { background: var(--close-hover); }
}
@media (pointer: coarse) {
  .modal-round-close { flex-basis: 44px; width: 44px; height: 44px; }
}
@media (prefers-reduced-motion: reduce) {
  .modal-round-close { transition: none; }
}
</style>
