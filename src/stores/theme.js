import { defineStore } from 'pinia'

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

    setTheme(theme) {
      if (theme !== LIGHT_THEME && theme !== DARK_THEME) return

      this.currentTheme = theme
      this.applyTheme()

      try {
        localStorage.setItem(STORAGE_KEY, theme)
      } catch (error) {
        // Ignore storage errors in private mode or restricted browsers.
      }
    },

    toggleTheme() {
      const nextTheme = this.currentTheme === DARK_THEME ? LIGHT_THEME : DARK_THEME
      this.setTheme(nextTheme)
    }
  }
})
