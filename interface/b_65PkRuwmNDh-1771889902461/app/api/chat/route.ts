import { NextRequest, NextResponse } from 'next/server'
import * as fs from 'fs'
import * as path from 'path'

const BACKEND_URL = process.env.BACKEND_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'
const SPORTS_DB_BASE = 'https://www.thesportsdb.com/api/v1/json/3'

// ─── Utility: safe fetch with timeout ─────────────────────────────────────────
async function safeFetch(url: string, options?: RequestInit): Promise<unknown> {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 5000)
    try {
        const res = await fetch(url, { ...options, signal: controller.signal, cache: 'no-store' })
        if (!res.ok) return null
        return res.json()
    } catch {
        return null
    } finally {
        clearTimeout(timeout)
    }
}

// ─── Read local CSV file ───────────────────────────────────────────────────────
function readLocalCSV(relativePath: string): string[][] | null {
    try {
        const projectRoot = path.resolve(process.cwd(), '..', '..', '..', '..')
        const csvPath = path.join(projectRoot, relativePath)
        if (!fs.existsSync(csvPath)) return null
        const content = fs.readFileSync(csvPath, 'utf-8')
        const lines = content.trim().split('\n')
        return lines.map(line => line.split(',').map(cell => cell.replace(/^"|"$/g, '').trim()))
    } catch {
        return null
    }
}

// ─── Parse clean matches CSV for team history ─────────────────────────────────
function getTeamHistory(teamName: string, leagueCode?: string): string {
    const data = readLocalCSV('data/processed/football_bi/matches_clean.csv')
    if (!data || data.length < 2) return ''

    const headers = data[0]
    const hitIdx = (name: string) => headers.indexOf(name)
    const homeIdx = hitIdx('home_team')
    const awayIdx = hitIdx('away_team')
    const resultIdx = hitIdx('full_time_result')
    const dateIdx = hitIdx('match_date')
    const leagueIdx = hitIdx('league_code')
    const hgIdx = hitIdx('home_goals')
    const agIdx = hitIdx('away_goals')

    const teamLower = teamName.toLowerCase()
    const matches = data.slice(1).filter(row => {
        const home = (row[homeIdx] || '').toLowerCase()
        const away = (row[awayIdx] || '').toLowerCase()
        const league = (row[leagueIdx] || '').toLowerCase()
        const teamMatch = home.includes(teamLower) || away.includes(teamLower) ||
            teamLower.includes(home) || teamLower.includes(away)
        if (leagueCode) return teamMatch && league.includes(leagueCode.toLowerCase())
        return teamMatch
    })

    if (matches.length === 0) return ''

    // Sort by date descending, take last 10
    const sorted = matches
        .filter(r => r[dateIdx])
        .sort((a, b) => new Date(b[dateIdx]).getTime() - new Date(a[dateIdx]).getTime())
        .slice(0, 10)

    let wins = 0, draws = 0, losses = 0, goalsFor = 0, goalsAgainst = 0
    const recentResults: string[] = []

    sorted.forEach(row => {
        const isHome = (row[homeIdx] || '').toLowerCase().includes(teamLower)
        const result = row[resultIdx]
        const hg = parseInt(row[hgIdx]) || 0
        const ag = parseInt(row[agIdx]) || 0

        if (isHome) {
            goalsFor += hg
            goalsAgainst += ag
            if (result === 'H') { wins++; recentResults.push('✅ V') }
            else if (result === 'D') { draws++; recentResults.push('🔶 N') }
            else { losses++; recentResults.push('❌ D') }
        } else {
            goalsFor += ag
            goalsAgainst += hg
            if (result === 'A') { wins++; recentResults.push('✅ V') }
            else if (result === 'D') { draws++; recentResults.push('🔶 N') }
            else { losses++; recentResults.push('❌ D') }
        }
    })

    const total = wins + draws + losses
    return `📊 **Historique ${teamName}** (${total} derniers matchs dans nos données)\n` +
        `- Bilan : **${wins}V** / ${draws}N / ${losses}D\n` +
        `- Buts : ${goalsFor} marqués, ${goalsAgainst} encaissés\n` +
        `- Forme récente : ${recentResults.slice(0, 5).join(' ')}\n` +
        `- Avg buts/match : ${(goalsFor / Math.max(total, 1)).toFixed(2)} marqués`
}

// ─── Web: get squad/players from TheSportsDB ──────────────────────────────────
async function getSquadFromWeb(teamName: string): Promise<string> {
    try {
        // Search team
        const searchUrl = `${SPORTS_DB_BASE}/searchteams.php?t=${encodeURIComponent(teamName)}`
        const searchResult = await safeFetch(searchUrl) as { teams?: { idTeam: string; strTeam: string; strLeague: string }[] } | null
        if (!searchResult?.teams?.length) {
            return `Je n'ai pas trouvé l'équipe "${teamName}" dans la base de données sportive.`
        }

        const team = searchResult.teams[0]
        const teamId = team.idTeam

        // Get players
        const playersUrl = `${SPORTS_DB_BASE}/lookup_all_players.php?id=${teamId}`
        const playersResult = await safeFetch(playersUrl) as { player?: { strPlayer: string; strPosition: string; strNationality: string; dateBorn: string }[] } | null

        if (!playersResult?.player?.length) {
            return `J'ai trouvé ${team.strTeam} (${team.strLeague}) mais je n'ai pas accès à l'effectif détaillé.`
        }

        const players = playersResult.player.slice(0, 20)
        const byPosition: Record<string, string[]> = {}
        players.forEach(p => {
            const pos = p.strPosition || 'Autre'
            if (!byPosition[pos]) byPosition[pos] = []
            byPosition[pos].push(`${p.strPlayer} (${p.strNationality || '?'})`)
        })

        let reply = `⚽ **Effectif ${team.strTeam}** (Ligue: ${team.strLeague})\n*Source: TheSportsDB*\n\n`
        for (const [pos, list] of Object.entries(byPosition)) {
            reply += `**${pos}:** ${list.join(', ')}\n`
        }
        return reply
    } catch {
        return `Impossible de récupérer l'effectif depuis le web pour "${teamName}".`
    }
}

// ─── FastAPI: predict match ────────────────────────────────────────────────────
async function predictMatchFromAPI(homeTeam: string, awayTeam: string, leagueCode: string): Promise<string> {
    try {
        const res = await safeFetch(`${BACKEND_URL}/api/predictions/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ home_team: homeTeam, away_team: awayTeam, league_code: leagueCode }),
        }) as { prediction?: string; probabilities?: { home: number; draw: number; away: number }; confidence?: number; xG_home?: number; xG_away?: number; features?: { headToHead?: string }; topExplanations?: { feature: string; value: number; effect: string }[] } | null

        if (!res || !res.prediction) {
            return `⚠️ Je n'ai pas pu obtenir la prédiction du modèle. Vérifiez que l'API FastAPI est lancée sur \`http://127.0.0.1:8000\` avec \`python code/09_run_api.py\`.`
        }

        const winnerLabel = res.prediction === 'H'
            ? `🏠 **${homeTeam}** gagne à domicile`
            : res.prediction === 'A'
                ? `✈️ **${awayTeam}** gagne à l'extérieur`
                : `🤝 **Match Nul**`

        const probs = res.probabilities
        const reply = [
            `🤖 **Prédiction du modèle Extra Trees**`,
            `**${homeTeam} vs ${awayTeam}**\n`,
            `**Résultat prédit :** ${winnerLabel}`,
            `**Confiance :** ${Math.round((res.confidence || 0) * 100)}%\n`,
            `**Probabilités :**`,
            `- 🏠 Domicile : **${Math.round((probs?.home || 0) * 100)}%**`,
            `- 🤝 Nul : ${Math.round((probs?.draw || 0) * 100)}%`,
            `- ✈️ Extérieur : ${Math.round((probs?.away || 0) * 100)}%\n`,
            `**xG estimé :** ${homeTeam} ${res.xG_home?.toFixed(2)} — ${awayTeam} ${res.xG_away?.toFixed(2)}`,
            res.features?.headToHead ? `**H2H :** ${res.features.headToHead}` : '',
            res.topExplanations?.length
                ? `\n**Facteurs déterminants :**\n${res.topExplanations.map(e => `- ${e.feature} : ${e.effect}`).join('\n')}`
                : '',
            `\n*Prédiction basée sur le score ELO, la forme récente et les points/match.*`,
        ].filter(Boolean).join('\n')

        return reply
    } catch {
        return `⚠️ Erreur lors de la prédiction. L'API FastAPI doit être lancée.`
    }
}

// ─── FastAPI: champion probabilities ──────────────────────────────────────────
async function getChampionProbs(leagueCode?: string): Promise<string> {
    const endpoint = leagueCode
        ? `${BACKEND_URL}/api/simulations?league_code=${leagueCode}`
        : `${BACKEND_URL}/api/simulations`
    const data = await safeFetch(endpoint) as { championshipWinners?: { team: string; probability: number }[] } | null

    if (!data?.championshipWinners?.length) {
        return `⚠️ Simulations non disponibles. Lancez d'abord le pipeline avec \`python code/08_run_all.py\`.`
    }

    const top5 = data.championshipWinners.slice(0, 6)
    const league = leagueCode || 'toutes ligues'
    let reply = `🏆 **Probabilités Champion — ${league}** (Monte Carlo)\n\n`
    top5.forEach((t, i) => {
        const pct = (t.probability * 100).toFixed(1)
        const bar = '█'.repeat(Math.round(t.probability * 20)).padEnd(20, '░')
        reply += `${i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i + 1}.`} **${t.team}** ${bar} ${pct}%\n`
    })
    reply += `\n*Basé sur ${data.championshipWinners[0] ? '300+' : '?'} simulations Monte Carlo.*`
    return reply
}

// ─── FastAPI: model statistics ─────────────────────────────────────────────────
async function getModelStats(): Promise<string> {
    const data = await safeFetch(`${BACKEND_URL}/api/statistics`) as {
        modelPerformance?: { precision: number; recall: number; f1Score: number; auc_roc: number }
        topFeatures?: { feature: string; importance: number }[]
    } | null

    if (!data?.modelPerformance) {
        return `⚠️ Statistiques non disponibles. L'API FastAPI doit être lancée.`
    }

    const m = data.modelPerformance
    const features = data.topFeatures?.slice(0, 5) || []

    return [
        `📈 **Statistiques du Modèle ML (Extra Trees)**\n`,
        `| Métrique | Valeur |`,
        `|---|---|`,
        `| Précision | **${(m.precision * 100).toFixed(1)}%** |`,
        `| Rappel | **${(m.recall * 100).toFixed(1)}%** |`,
        `| F1-Score | **${(m.f1Score * 100).toFixed(1)}%** |`,
        `| AUC-ROC | **${(m.auc_roc * 100).toFixed(1)}%** |`,
        features.length ? `\n**Top features :**\n${features.map(f => `- ${f.feature}: ${(f.importance * 100).toFixed(1)}%`).join('\n')}` : '',
        `\n*3 classes : Victoire DOM / NUL / Victoire EXT • Split temporel strict*`,
    ].filter(Boolean).join('\n')
}

// ─── FastAPI: available leagues & teams ───────────────────────────────────────
async function getLeagues(): Promise<string> {
    const data = await safeFetch(`${BACKEND_URL}/api/leagues`) as { items?: { league_code: string; league_name: string }[] } | null
    if (!data?.items) return `⚠️ API non disponible.`
    const list = data.items.map(l => `- **${l.league_code}** : ${l.league_name}`).join('\n')
    return `🌍 **Ligues disponibles dans la plateforme :**\n${list}\n\n*Chaque ligue couvre les saisons 1993-2026.*`
}

async function getTeams(leagueCode: string): Promise<string> {
    const data = await safeFetch(`${BACKEND_URL}/api/teams/${leagueCode}`) as { items?: string[] } | null
    if (!data?.items?.length) return `⚠️ Aucune équipe trouvée pour "${leagueCode}".`
    const list = data.items.join(', ')
    return `⚽ **Équipes de ${leagueCode} (saison actuelle) :**\n${list}`
}

// ─── Intent detection ─────────────────────────────────────────────────────────
type Intent =
    | 'predict'
    | 'champion'
    | 'stats'
    | 'history'
    | 'squad'
    | 'leagues'
    | 'teams'
    | 'explain'
    | 'greeting'
    | 'unknown'

function detectIntent(message: string): { intent: Intent; entities: Record<string, string> } {
    const msg = message.toLowerCase()

    // Predict match
    const predictPatterns = ['prédi', 'predi', 'qui gagne', 'qui va gagner', 'match entre', 'vs', 'contre',
        'résultat', 'resultat', 'pronostic', 'outcome', 'winner']
    if (predictPatterns.some(p => msg.includes(p))) {
        // Try to extract league
        const leagueMap: Record<string, string> = {
            'premier league': 'EPL', 'epl': 'EPL', 'angleterre': 'EPL',
            'la liga': 'LaLiga', 'laliga': 'LaLiga', 'espagne': 'LaLiga',
            'serie a': 'SerieA', 'italie': 'SerieA',
            'bundesliga': 'Bundesliga', 'allemagne': 'Bundesliga',
            'ligue 1': 'Ligue1', 'ligue1': 'Ligue1', 'france': 'Ligue1',
        }
        let leagueCode = 'EPL'
        for (const [key, code] of Object.entries(leagueMap)) {
            if (msg.includes(key)) { leagueCode = code; break }
        }
        return { intent: 'predict', entities: { leagueCode } }
    }

    // Champion
    if (['champion', 'titre', 'gagner la ligue', 'gagner le championnat', 'vainqueur',
        'simulation', 'classement final', 'probabilit'].some(p => msg.includes(p))) {
        const leagueMap: Record<string, string> = {
            'premier league': 'EPL', 'epl': 'EPL',
            'la liga': 'LaLiga', 'espagne': 'LaLiga',
            'serie a': 'SerieA',
            'bundesliga': 'Bundesliga',
            'ligue 1': 'Ligue1', 'france': 'Ligue1',
        }
        let leagueCode = ''
        for (const [key, code] of Object.entries(leagueMap)) {
            if (msg.includes(key)) { leagueCode = code; break }
        }
        return { intent: 'champion', entities: { leagueCode } }
    }

    // Stats
    if (['accuracy', 'précision', 'precision', 'performance', 'f1', 'statistique', 'stat ',
        'auc', 'modèle', 'modele', 'résultat du modèle', 'metric'].some(p => msg.includes(p))) {
        return { intent: 'stats', entities: {} }
    }

    // Historique match CSV
    if (['historique', 'bilan', 'résultats passé', 'classement', 'last match', 'derniers match',
        'passé', 'derni'].some(p => msg.includes(p))) {
        return { intent: 'history', entities: {} }
    }

    // Squad / players (web)
    if (['joueurs', 'effectif', 'squad', 'compo', 'who plays', 'les joueurs de', 'joueur de',
        'roster', 'liste des joueurs'].some(p => msg.includes(p))) {
        return { intent: 'squad', entities: {} }
    }

    // Leagues
    if (['ligue', 'championnat', 'disponible', 'couvr', 'quelles ligue'].some(p => msg.includes(p))) {
        return { intent: 'leagues', entities: {} }
    }

    // Teams
    if (['équipe', 'equipe', 'club', 'team'].some(p => msg.includes(p))) {
        return { intent: 'teams', entities: {} }
    }

    // Explain
    if (['elo', 'comment fonctionne', 'explique', 'comment le modèle', 'monte carlo',
        'extra tree', 'feature', 'fuite', 'leakage', 'prétraitement', 'preprocessing'].some(p => msg.includes(p))) {
        return { intent: 'explain', entities: {} }
    }

    // Greetings
    if (['bonjour', 'salut', 'hello', 'bonsoir', 'allo', 'coucou', 'hi ', 'hey'].some(p => msg.includes(p))) {
        return { intent: 'greeting', entities: {} }
    }

    return { intent: 'unknown', entities: {} }
}

// ─── Extract team name from message ───────────────────────────────────────────
function extractTeamName(message: string): string {
    // Remove common trigger words and extract the rest
    const cleaned = message
        .replace(/joueurs de|effectif de|squad de|compo de|les joueurs de|historique de|bilan de|résultats de/gi, '')
        .replace(/[?,!.]/g, '')
        .trim()
    return cleaned
}

function extractTeamPair(message: string): { home: string; away: string } | null {
    // Try "X vs Y", "X contre Y", "X - Y"
    const patterns = [
        /([A-Za-zÀ-ÿ\s]+?)\s+(?:vs?\.?|contre|versus|-)\s+([A-Za-zÀ-ÿ\s]+)/i,
    ]
    for (const p of patterns) {
        const m = message.match(p)
        if (m) return { home: m[1].trim(), away: m[2].trim() }
    }
    return null
}

// ─── Explain responses ─────────────────────────────────────────────────────────
const EXPLAIN_RESPONSES: Record<string, string> = {
    elo: `🎯 **Score ELO** — système de rating adapté du jeu d'échecs.\n\n- Chaque équipe commence à **1500 ELO**\n- Après un match : \`elo_nouveau = elo_ancien + 20 × (résultat_réel − résultat_attendu)\`\n- Une victoire contre une meilleure équipe rapporte plus de points\n- +60 points d'avantage domicile\n- En début de saison, l'ELO est partiellement réinitialisé : \`0.75 × elo_précédent + 0.25 × 1500\``,
    'monte carlo': `🎲 **Simulation Monte Carlo** (championnat)\n\n1. On prend l'état réel du classement (matchs joués)\n2. Pour chaque match restant : on calcule P(H), P(D), P(A) via ELO + forme + PPG\n3. On tire un résultat aléatoire selon ces probabilités\n4. On répète **300 fois**\n5. Probabilité de titre = nombre de fois 1er / 300`,
    'extra tree': `🌲 **Extra Trees Classifier** (modèle choisi)\n\n- Similaire au Random Forest mais les seuils de split sont **totalement aléatoires**\n- Moins de variance, meilleure généralisation sur données bruitées\n- **500 arbres**, max_depth=20, class_weight='balanced_subsample'\n- Sélectionné car meilleur **F1-macro** sur la validation temporelle`,
    default: `🔬 **Comment fonctionne la plateforme ?**\n\n1. **Données** : 58 467 matchs depuis football-data.co.uk (1993-2026)\n2. **Features** : ELO, forme récente (5 matchs), points/match, repos, différentiels\n3. **Modèle** : Extra Trees — split temporel strict (pas de random split)\n4. **API** : FastAPI → prédictions probabilistes (H/D/A)\n5. **Simulations** : Monte Carlo pour probabilités de championnat\n\nTapez "ELO", "Monte Carlo" ou "Extra Trees" pour plus de détails.`,
}

function getExplainResponse(message: string): string {
    const msg = message.toLowerCase()
    if (msg.includes('elo')) return EXPLAIN_RESPONSES.elo
    if (msg.includes('monte carlo') || msg.includes('simulation')) return EXPLAIN_RESPONSES['monte carlo']
    if (msg.includes('extra tree') || msg.includes('modèle') || msg.includes('modele')) return EXPLAIN_RESPONSES['extra tree']
    return EXPLAIN_RESPONSES.default
}

// ─── Gemini LLM Generator ──────────────────────────────────────────────────────
async function generateGeminiResponse(userMessage: string, contextData: string, intent: string): Promise<string> {
    const apiKey = 'AIzaSyBllfvI7cCBBZp6P8eJGgv2pDRYzOdGJxg'
    const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`

    let promptText = ''
    if (intent === 'unknown' || intent === 'greeting' || !contextData) {
        promptText = `Tu es "Football BI Chatbot", un expert en football et data science, intégré à une plateforme qui utilise un modèle Extra Trees et des simulations Monte Carlo. L'utilisateur te dit : "${userMessage}". Réponds de manière utile, polie et très concise. Utilise du Markdown (gras, emojis). Si c'est pour une prédiction en direct, rappelle-lui le format : "Prédis Equipe A vs Equipe B en [Ligue]".`
    } else {
        promptText = `Tu es "Football BI Chatbot", l'assistant IA d'une plateforme de prédiction footballistique.
L'utilisateur a demandé : "${userMessage}"
Intention détectée par le backend : ${intent}

Voici les données brutes extraites par le système interne (Modèles ML locaux, CSV) :
---
${contextData}
---

MISSION : Formule une belle réponse naturelle, claire et engageante pour l'utilisateur en te basant STRICTEMENT sur ces données brutes. 
- N'invente pas de statistiques ou de prédictions, tu dois utiliser uniquement celles du texte ci-dessus.
- Met en valeur les probabilités, la confiance du modèle et les scores avec du gras et des emojis.
- Utilise des listes à puces si c'est pertinent.
- Ne commence pas par "Voici la réponse", réponds directement comme si tu venais de faire l'analyse.
`
    }

    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ contents: [{ role: 'user', parts: [{ text: promptText }] }] })
        })
        const data = await res.json()
        return data?.candidates?.[0]?.content?.parts?.[0]?.text || contextData || "Désolé, problème de génération."
    } catch (e) {
        console.error("Gemini:", e)
        return contextData || "Erreur IA."
    }
}

// ─── Main handler ──────────────────────────────────────────────────────────────
export async function POST(request: NextRequest) {
    try {
        const { message } = await request.json() as { message: string }
        if (!message?.trim()) {
            return NextResponse.json({ reply: 'Posez-moi une question sur le football !' })
        }

        const { intent, entities } = detectIntent(message)

        let reply = ''

        switch (intent) {
            case 'greeting':
                reply = `⚽ **Bonjour !** Je suis le chatbot Football BI.\n\nJe peux vous aider avec :\n- 🤖 **Prédictions** de matchs (modèle ML réel)\n- 🏆 **Probabilités champion** (Monte Carlo)\n- 📊 **Statistiques** du modèle\n- 📋 **Historique** d'une équipe (données CSV)\n- 👥 **Effectif** d'une équipe (web)\n\nEssayez : *"Prédis Arsenal vs Chelsea en EPL"* ou *"Joueurs du Real Madrid"*`
                break

            case 'predict': {
                const pair = extractTeamPair(message)
                if (!pair) {
                    reply = `Pour une prédiction, précisez le format :\n**"[équipe domicile] vs [équipe extérieur] en [ligue]"**\n\nEx: *"Prédis Arsenal vs Chelsea en EPL"*\n\nLigues disponibles : EPL, LaLiga, SerieA, Bundesliga, Ligue1`
                } else {
                    reply = await predictMatchFromAPI(pair.home, pair.away, entities.leagueCode || 'EPL')
                }
                break
            }

            case 'champion':
                reply = await getChampionProbs(entities.leagueCode || undefined)
                break

            case 'stats':
                reply = await getModelStats()
                break

            case 'history': {
                const teamName = extractTeamName(message)
                const history = getTeamHistory(teamName)
                if (history) {
                    reply = history
                } else {
                    reply = `Je n'ai pas trouvé de données historiques pour "${teamName}" dans nos fichiers CSV.\n\n*Les données CSV couvrent : EPL, LaLiga, SerieA, Bundesliga, Ligue1 depuis 1993.*`
                }
                break
            }

            case 'squad': {
                const teamName = extractTeamName(message)
                reply = await getSquadFromWeb(teamName)
                break
            }

            case 'leagues':
                reply = await getLeagues()
                break

            case 'teams': {
                const leagueMap: Record<string, string> = {
                    'premier': 'EPL', 'epl': 'EPL', 'angleterre': 'EPL',
                    'liga': 'LaLiga', 'espagne': 'LaLiga',
                    'serie': 'SerieA', 'italie': 'SerieA',
                    'bundesliga': 'Bundesliga', 'allemagne': 'Bundesliga',
                    'ligue': 'Ligue1', 'france': 'Ligue1',
                }
                let code = 'EPL'
                const msg = message.toLowerCase()
                for (const [key, val] of Object.entries(leagueMap)) {
                    if (msg.includes(key)) { code = val; break }
                }
                reply = await getTeams(code)
                break
            }

            case 'explain':
                reply = getExplainResponse(message)
                break

            default:
                reply = `⚽ Je suis spécialisé en **football et prédiction de matchs**.\n\nVoici ce que je sais faire :\n- *"Prédis Arsenal vs Chelsea en EPL"* → prédiction ML\n- *"Champion de la Premier League ?"* → probabilités Monte Carlo\n- *"Stats du modèle"* → métriques Extra Trees\n- *"Historique de Arsenal"* → données CSV locales\n- *"Joueurs du Real Madrid"* → effectif depuis le web\n- *"Comment fonctionne l'ELO ?"* → explication`
        }

        // On passe les données locales (reply) et le message utilisateur à Gemini
        const finalReply = await generateGeminiResponse(message, reply, intent)

        return NextResponse.json({ reply: finalReply, intent })
    } catch (error) {
        console.error('Chat error:', error)
        return NextResponse.json(
            { reply: '⚠️ Une erreur est survenue. Réessayez.' },
            { status: 500 }
        )
    }
}
