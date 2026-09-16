<script>
import { passwordStrength } from '@/utils/passwordStrength.js';
export default {
  props: { value: { type: String, default: '' } },
  computed: { strength() { return passwordStrength(this.value); } },
};
</script>
<template>
  <div class="password-strength" :class="`strength-${strength.score}`" title="Ориентировочная оценка на этом устройстве. Не проверяет утечки и не гарантирует стойкость.">
    <div class="strength-track" aria-hidden="true"><span v-for="step in 3" :key="step" :class="{ filled: step <= strength.score }" /></div>
    <span>{{ strength.label }}</span>
  </div>
</template>
<style scoped>
.password-strength { --strength-ink: #64748b; --strength-empty: #e2e8f0; color: var(--strength-ink); display: grid; gap: 5px; margin-top: 8px; font-size: 12px; line-height: 1.4; }
.strength-track { display: flex; gap: 4px; }
.strength-track span { flex: 1; height: 3px; border-radius: 2px; background: var(--strength-empty); transition: background-color 180ms ease-out; }
.strength-track .filled { background: var(--strength-fill); }
.strength-1 { --strength-fill: #d97706; }
.strength-2 { --strength-fill: #3b82f6; }
.strength-3 { --strength-fill: #059669; }
html[data-theme='dark'] .password-strength { --strength-ink: #a6b3c6; --strength-empty: #334155; }
html[data-theme='dark'] .strength-3 { --strength-fill: #34d399; }
@media (prefers-reduced-motion: reduce) { .strength-track span { transition: none; } }
</style>
