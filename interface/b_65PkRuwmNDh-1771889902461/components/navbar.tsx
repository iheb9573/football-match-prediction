'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { BarChart3, Trophy, TrendingUp, Zap } from 'lucide-react'

export function Navbar() {
  const pathname = usePathname()

  const links = [
    { href: '/', label: 'Dashboard', icon: BarChart3 },
    { href: '/predictions', label: 'Prédictions', icon: Zap },
    { href: '/simulations', label: 'Simulations', icon: Trophy },
    { href: '/statistics', label: 'Statistiques', icon: TrendingUp }
  ]

  return (
    <nav className="sticky top-0 z-50 border-b border-slate-700 bg-slate-900/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 font-bold text-xl hover:opacity-80 transition-opacity">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <BarChart3 size={20} className="text-white" />
            </div>
            <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Football BI
            </span>
          </Link>

          <div className="flex items-center gap-8">
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
                      ? 'text-blue-400 border-b-2 border-blue-400 pb-1'
                      : 'text-slate-400 hover:text-slate-200'
                  )}
                >
                  <Icon size={18} />
                  {link.label}
                </Link>
              )
            })}
          </div>

          <div className="text-xs text-slate-500">
            ML Powered • Probabilistic • Explainable
          </div>
        </div>
      </div>
    </nav>
  )
}
