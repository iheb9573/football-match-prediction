'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { BarChart3, Trophy, TrendingUp, Zap } from 'lucide-react'
import { ThemeToggle } from '@/components/theme-toggle'

export function Navbar() {
  const pathname = usePathname()

  const links = [
    { href: '/', label: 'Dashboard', icon: BarChart3 },
    { href: '/predictions', label: 'Prédictions', icon: Zap },
    { href: '/simulations', label: 'Simulations', icon: Trophy },
    { href: '/statistics', label: 'Statistiques', icon: TrendingUp }
  ]

  return (
    <nav className="sticky top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur-md transition-colors duration-300">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 font-bold text-xl hover:opacity-80 transition-opacity">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/30">
              <BarChart3 size={20} className="text-white" />
            </div>
            <span className="bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">
              Football BI
            </span>
          </Link>

          <div className="flex items-center gap-6">
            {links.map((link) => {
              const Icon = link.icon
              const isActive = pathname === link.href
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={cn(
                    'flex items-center gap-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'text-blue-500 dark:text-blue-400 border-b-2 border-blue-500 dark:border-blue-400 pb-1'
                      : 'text-muted-foreground hover:text-foreground'
                  )}
                >
                  <Icon size={18} />
                  {link.label}
                </Link>
              )
            })}
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground hidden sm:block">
              ML • BI • Probabilistic
            </span>
            <ThemeToggle />
          </div>
        </div>
      </div>
    </nav>
  )
}
