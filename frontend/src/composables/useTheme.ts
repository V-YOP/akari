import { computed, onMounted, watch } from 'vue'
import { useDark, useToggle } from '@vueuse/core'

export function useTheme() {
  const isDark = useDark({
    storageKey: 'akari-theme',
    valueDark: 'dark',
    valueLight: 'light'
  })

  const toggleTheme = useToggle(isDark)

  const theme = computed(() => isDark.value ? 'dark' : 'light')

  // Apply theme class to document element
  onMounted(() => {
    const updateThemeClass = () => {
      document.documentElement.className = theme.value
    }
    updateThemeClass()
    watch(isDark, updateThemeClass)
  })

  return {
    isDark,
    theme,
    toggleTheme
  }
}