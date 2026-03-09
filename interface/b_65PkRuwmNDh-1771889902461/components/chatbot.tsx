'use client'

import * as React from 'react'
import { MessageCircle, X, Send, Bot, User, Loader2, Sparkles } from 'lucide-react'

interface Message {
    id: string
    role: 'user' | 'assistant'
    content: string
    timestamp: Date
}

const QUICK_SUGGESTIONS = [
    '⚽ Prédis Arsenal vs Chelsea en EPL',
    '🏆 Champion de la Premier League ?',
    '📊 Stats du modèle ML',
    '👥 Joueurs du Real Madrid',
    '📋 Historique de Arsenal',
    'ℹ️ Comment fonctionne l\'ELO ?',
]

function TypingIndicator() {
    return (
        <div className="flex items-end gap-2 mb-4">
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0 shadow">
                <Bot size={14} className="text-white" />
            </div>
            <div className="bg-card border border-border rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
                <div className="flex gap-1 items-center h-4">
                    <span className="typing-dot w-2 h-2 rounded-full bg-muted-foreground block" />
                    <span className="typing-dot w-2 h-2 rounded-full bg-muted-foreground block" />
                    <span className="typing-dot w-2 h-2 rounded-full bg-muted-foreground block" />
                </div>
            </div>
        </div>
    )
}

function MessageBubble({ message }: { message: Message }) {
    const isUser = message.role === 'user'

    // Simple markdown-ish renderer
    const renderContent = (text: string) => {
        const lines = text.split('\n')
        return lines.map((line, i) => {
            // Bold: **text**
            const withBold = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // Italic: *text*
            const withItalic = withBold.replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Code: `text`
            const withCode = withItalic.replace(/`(.*?)`/g, '<code class="bg-muted px-1 rounded text-xs font-mono">$1</code>')
            // List items
            const isList = line.startsWith('- ')
            const content = isList ? withCode.replace(/^- /, '') : withCode

            if (isList) {
                return (
                    <div key={i} className="flex gap-2 items-start">
                        <span className="text-blue-500 mt-0.5 flex-shrink-0">•</span>
                        <span dangerouslySetInnerHTML={{ __html: content }} />
                    </div>
                )
            }
            if (line === '') return <div key={i} className="h-2" />
            return <p key={i} dangerouslySetInnerHTML={{ __html: content }} />
        })
    }

    return (
        <div className={`flex items-end gap-2 mb-4 ${isUser ? 'flex-row-reverse' : ''}`}>
            {/* Avatar */}
            <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 shadow
        ${isUser
                    ? 'bg-gradient-to-br from-blue-500 to-blue-700'
                    : 'bg-gradient-to-br from-blue-500 to-purple-600'
                }`}>
                {isUser ? <User size={14} className="text-white" /> : <Bot size={14} className="text-white" />}
            </div>

            {/* Bubble */}
            <div className={`max-w-[82%] rounded-2xl px-4 py-3 shadow-sm text-sm leading-relaxed space-y-1
        ${isUser
                    ? 'bg-gradient-to-br from-blue-500 to-blue-700 text-white rounded-br-sm'
                    : 'bg-card border border-border text-foreground rounded-bl-sm'
                }`}
            >
                {renderContent(message.content)}
                <p className={`text-[10px] mt-1 ${isUser ? 'text-blue-200' : 'text-muted-foreground'}`}>
                    {message.timestamp.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                </p>
            </div>
        </div>
    )
}

export function Chatbot() {
    const [open, setOpen] = React.useState(false)
    const [messages, setMessages] = React.useState<Message[]>([
        {
            id: 'welcome',
            role: 'assistant',
            content: '⚽ **Bonjour !** Je suis le chatbot Football BI.\n\nJe peux vous aider avec :\n- 🤖 **Prédictions** de matchs (via le modèle ML)\n- 🏆 **Probabilités champion** (Monte Carlo)\n- 📊 **Stats** du modèle\n- 📋 **Historique** d\'équipe (données locales)\n- 👥 **Effectif** d\'une équipe (web)\n\nCliquez une suggestion ou posez votre question !',
            timestamp: new Date(),
        }
    ])
    const [input, setInput] = React.useState('')
    const [loading, setLoading] = React.useState(false)
    const [showSuggestions, setShowSuggestions] = React.useState(true)
    const [unread, setUnread] = React.useState(0)
    const messagesEndRef = React.useRef<HTMLDivElement>(null)
    const inputRef = React.useRef<HTMLInputElement>(null)

    React.useEffect(() => {
        if (open) {
            messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
            setUnread(0)
            setTimeout(() => inputRef.current?.focus(), 100)
        }
    }, [messages, open])

    const sendMessage = React.useCallback(async (text: string) => {
        const trimmed = text.trim()
        if (!trimmed || loading) return

        const userMsg: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: trimmed,
            timestamp: new Date(),
        }

        setMessages(prev => [...prev, userMsg])
        setInput('')
        setLoading(true)
        setShowSuggestions(false)

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: trimmed }),
            })
            const data = await res.json() as { reply?: string }
            const reply = data.reply || 'Désolé, je n\'ai pas pu répondre. Réessayez.'

            const botMsg: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: reply,
                timestamp: new Date(),
            }
            setMessages(prev => [...prev, botMsg])
            if (!open) setUnread(n => n + 1)
        } catch {
            setMessages(prev => [...prev, {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: '⚠️ Erreur réseau. Vérifiez votre connexion.',
                timestamp: new Date(),
            }])
        } finally {
            setLoading(false)
        }
    }, [loading, open])

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            sendMessage(input)
        }
    }

    return (
        <>
            {/* Floating Button */}
            <button
                onClick={() => { setOpen(o => !o); setUnread(0) }}
                aria-label="Ouvrir le chatbot Football BI"
                className={`fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full shadow-2xl
          bg-gradient-to-br from-blue-500 to-purple-600
          flex items-center justify-center
          hover:scale-110 active:scale-95 transition-all duration-200
          hover:shadow-blue-500/40`}
            >
                {open ? (
                    <X size={22} className="text-white" />
                ) : (
                    <>
                        <MessageCircle size={24} className="text-white" />
                        {unread > 0 && (
                            <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full text-white text-xs flex items-center justify-center font-bold">
                                {unread}
                            </span>
                        )}
                    </>
                )}
            </button>

            {/* Chat Window */}
            {open && (
                <div className="fixed bottom-24 right-6 z-50 chatbot-slide-up
          w-[380px] max-w-[calc(100vw-2rem)]
          bg-background border border-border rounded-2xl shadow-2xl dark:shadow-blue-900/30
          flex flex-col overflow-hidden"
                    style={{ height: '520px' }}
                >
                    {/* Header */}
                    <div className="bg-gradient-to-r from-blue-600 to-purple-700 px-4 py-3 flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center">
                            <Sparkles size={18} className="text-white" />
                        </div>
                        <div className="flex-1">
                            <h3 className="text-white font-semibold text-sm">Football BI Chatbot</h3>
                            <p className="text-blue-100 text-xs">ML • CSV • Web</p>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                            <span className="text-blue-100 text-xs">En ligne</span>
                        </div>
                    </div>

                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto px-4 py-4 space-y-1 bg-background/80">
                        {messages.map(msg => (
                            <MessageBubble key={msg.id} message={msg} />
                        ))}
                        {loading && <TypingIndicator />}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Quick suggestions */}
                    {showSuggestions && (
                        <div className="px-3 py-2 border-t border-border bg-muted/30">
                            <p className="text-xs text-muted-foreground mb-2">Suggestions rapides :</p>
                            <div className="flex gap-2 overflow-x-auto pb-1" style={{ scrollbarWidth: 'none' }}>
                                {QUICK_SUGGESTIONS.map((s, i) => (
                                    <button
                                        key={i}
                                        onClick={() => sendMessage(s.replace(/^[⚽🏆📊👥📋ℹ️] /, ''))}
                                        className="flex-shrink-0 text-xs bg-card border border-border hover:border-blue-500/50
                      hover:bg-blue-500/10 transition-colors rounded-full px-3 py-1.5 text-foreground"
                                    >
                                        {s}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Input */}
                    <div className="px-3 py-3 border-t border-border bg-background flex items-center gap-2">
                        <input
                            ref={inputRef}
                            type="text"
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Posez une question football..."
                            disabled={loading}
                            className="flex-1 text-sm bg-muted border border-border rounded-full px-4 py-2
                text-foreground placeholder:text-muted-foreground
                focus:outline-none focus:ring-2 focus:ring-blue-500/50
                disabled:opacity-50 transition-all"
                        />
                        <button
                            onClick={() => sendMessage(input)}
                            disabled={!input.trim() || loading}
                            aria-label="Envoyer"
                            className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-purple-600
                flex items-center justify-center flex-shrink-0
                disabled:opacity-40 hover:scale-105 active:scale-95 transition-transform"
                        >
                            {loading ? (
                                <Loader2 size={16} className="text-white animate-spin" />
                            ) : (
                                <Send size={16} className="text-white" />
                            )}
                        </button>
                    </div>
                </div>
            )}
        </>
    )
}
