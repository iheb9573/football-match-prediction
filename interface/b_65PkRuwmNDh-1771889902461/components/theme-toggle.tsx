'use client'

import * as React from 'react'
import { Moon, Sun } from 'lucide-react'
import { useTheme } from 'next-themes'

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = React.useState(false)

  React.useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return (
      <button className="w-9 h-9 rounded-full bg-slate-700/50 flex items-center justify-center" aria-label="Toggle theme">
        <span className="w-4 h-4" />
      </button>
    )
  }

  const isDark = theme === 'dark'

  return (
    <button
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
      aria-label={isDark ? 'Passer en mode clair' : 'Passer en mode sombre'}
      className="relative w-9 h-9 rounded-full flex items-center justify-center overflow-hidden
        bg-slate-700/50 dark:bg-slate-700/50 hover:bg-slate-600/70 dark:hover:bg-slate-600/70
        border border-slate-500/30 dark:border-slate-500/30
        transition-all duration-300 hover:scale-110 hover:shadow-lg hover:shadow-blue-500/20
        group"
    >
      {/* Sun icon (visible in dark mode) */}
      <Sun
        size={16}
        className={`absolute transition-all duration-500 text-amber-400
          ${isDark
            ? 'rotate-0 scale-100 opacity-100'
            : '-rotate-90 scale-0 opacity-0'
          }`}
      />
      {/* Moon icon (visible in light mode) */}
      <Moon
        size={16}
        className={`absolute transition-all duration-500 text-blue-300
          ${isDark
            ? 'rotate-90 scale-0 opacity-0'
            : 'rotate-0 scale-100 opacity-100'
          }`}
      />
    </button>
  )
}
