<script>
export default { props: { visible: Boolean }, emits: ['toggle'] };
</script>
<template>
  <button class="password-eye" type="button" :title="visible ? 'Скрыть пароль' : 'Показать пароль'" :aria-label="visible ? 'Скрыть пароль' : 'Показать пароль'" :aria-pressed="visible" @click="$emit('toggle')">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/><path v-if="visible" d="m3 3 18 18"/></svg>
  </button>
</template>
<style scoped>
.password-eye { position: absolute; right: 5px; top: 50%; transform: translateY(-50%); display: grid; place-items: center; width: 36px; height: 36px; border: 0; border-radius: 6px; background: transparent; color: #64748b; cursor: pointer; padding: 7px; }
.password-eye svg { width: 21px; height: 21px; }
.password-eye:focus-visible { outline: 2px solid #3b82f6; outline-offset: 1px; }
html[data-theme='dark'] .password-eye { color: #a6b3c6; }
@media (hover: hover) { .password-eye:hover { background: rgb(100 116 139 / .1); } }
</style>
