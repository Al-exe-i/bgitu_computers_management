import { defineStore } from 'pinia'
import { nextTick } from 'vue'

const STORAGE_KEY = 'app-theme'
const LIGHT_THEME = 'light'
const DARK_THEME = 'dark'

function getSystemTheme() {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return LIGHT_THEME
  }

  return window.matchMedia('(prefers-color-scheme: dark)').matches
      ? DARK_THEME
      : LIGHT_THEME
}

function applyThemeToDocument(theme) {
  if (typeof document === 'undefined') return

  document.documentElement.setAttribute('data-theme', theme)
  document.documentElement.style.colorScheme = theme
}

function prefersReducedMotion() {
  return typeof window !== 'undefined'
      && typeof window.matchMedia === 'function'
      && window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

function supportsViewTransitions() {
  return typeof document !== 'undefined'
      && typeof document.startViewTransition === 'function'
}

export const useThemeStore = defineStore('theme', {
  state: () => ({
    currentTheme: LIGHT_THEME,
    initialized: false
  }),

  getters: {
    isDark: (state) => state.currentTheme === DARK_THEME
  },

  actions: {
    initTheme() {
      if (this.initialized) {
        this.applyTheme()
        return
      }

      let theme = null

      try {
        theme = localStorage.getItem(STORAGE_KEY)
      } catch (error) {
        theme = null
      }

      if (theme !== LIGHT_THEME && theme !== DARK_THEME) {
        theme = getSystemTheme()
      }

      this.currentTheme = theme
      this.initialized = true
      this.applyTheme()
    },

    applyTheme() {
      applyThemeToDocument(this.currentTheme)
    },

    // Применяет тему и сохраняет выбор (без анимации)
    commitTheme(theme) {
      this.currentTheme = theme
      this.applyTheme()

      try {
        localStorage.setItem(STORAGE_KEY, theme)
      } catch (error) {
        // Ignore storage errors in private mode or restricted browsers.
      }
    },

    setTheme(theme, origin = null) {
      if (theme !== LIGHT_THEME && theme !== DARK_THEME) return
      if (theme === this.currentTheme) return

      // Браузеры без View Transitions API и режим «меньше движения» — переключаем мгновенно
      if (!supportsViewTransitions() || prefersReducedMotion()) {
        this.commitTheme(theme)
        return
      }

      // Точка, из которой «расходится» новая тема (центр кнопки-переключателя)
      const x = origin && Number.isFinite(origin.x) ? origin.x : window.innerWidth - 56
      const y = origin && Number.isFinite(origin.y) ? origin.y : 24
      const radius = Math.hypot(
        Math.max(x, window.innerWidth - x),
        Math.max(y, window.innerHeight - y)
      )

      const root = document.documentElement
      root.style.setProperty('--theme-vt-x', `${x}px`)
      root.style.setProperty('--theme-vt-y', `${y}px`)
      root.style.setProperty('--theme-vt-r', `${radius}px`)

      // Обновляем DOM внутри перехода и ждём перерисовку Vue (смена логотипа, классов is-dark),
      // чтобы «новый» снимок захватил уже актуальную тему
      document.startViewTransition(async () => {
        this.commitTheme(theme)
        await nextTick()
      })
    },

    toggleTheme(origin = null) {
      const nextTheme = this.currentTheme === DARK_THEME ? LIGHT_THEME : DARK_THEME
      this.setTheme(nextTheme, origin)
    }
  }
})
