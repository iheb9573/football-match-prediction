# Football BI Predictor

Une interface **professionnelle et interactive** de Business Intelligence + Machine Learning pour prédire les résultats de matchs de football de manière **probabiliste** et **explicable**.

## 🎯 Fonctionnalités

### 📊 Dashboard Principal
- Vue d'ensemble des performances du modèle ML
- Métriques de précision, rappel, F1-score et AUC-ROC
- Visualisations interactives avec Recharts

### ⚡ Prédictions de Matchs
- Affichage des matchs à venir avec probabilités (Domicile / Match Nul / Extérieur)
- Analyse détaillée par match : xG, force offensive/défensive, historique H2H
- Filtrage par ligue
- Indicateurs de confiance du modèle

### 🏆 Simulations Monte Carlo
- Probabilités de champion (100k+ simulations)
- Top 4 des équipes
- Évolution de la probabilité leader au fil de la saison
- Intervalles de confiance 95%

### 📈 Statistiques & EDA
- Distribution des résultats
- Précision par ligue
- Feature importance (SHAP) - Explainability du modèle
- Analyse de confiance par tranche
- Statistiques par ligue

## 🏗️ Architecture

```
Frontend (React/Next.js 16)
├── Pages
│   ├── Dashboard (/)
│   ├── Predictions (/predictions)
│   ├── Simulations (/simulations)
│   └── Statistics (/statistics)
├── Composants réutilisables
└── API Mock (pour dev local)

        ↓↓↓ À connecter ↓↓↓

Backend (Python ML Model)
├── FastAPI / Flask
├── Modèle de prédiction (Random Forest, XGBoost, etc.)
├── Simulateur Monte Carlo
└── Base de données (optionnel)
```

## 🚀 Démarrage Rapide

### Pour les débutants React

**Lisez le guide complet** : [SETUP_LOCAL.md](./SETUP_LOCAL.md)

### Démarrage rapide (résumé)

```bash
# 1. Installer Node.js si ce n'est pas fait
# https://nodejs.org (version 18+)

# 2. Installer les dépendances
npm install

# 3. Lancer le serveur de développement
npm run dev

# 4. Accéder à l'interface
# http://localhost:3000
```

## 📦 Technologies Utilisées

- **Next.js 16** - Framework React full-stack
- **React 19.2** - UI library
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - Composants UI
- **Recharts** - Visualisations / Graphiques
- **Lucide Icons** - Icônes

## 🔌 Intégration de Votre API Python

### 1. Créez votre API avec FastAPI

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/predictions")
def get_predictions():
    # Retournez vos prédictions du modèle ML
    return {
        "predictions": [...]
    }

@app.get("/api/statistics")
def get_statistics():
    # Retournez les performances du modèle
    return {
        "accuracyByLeague": [...],
        "modelPerformance": {...},
        # ... autres stats
    }

@app.get("/api/simulations")
def get_simulations():
    # Retournez vos simulations Monte Carlo
    return {
        "championshipWinners": [...],
        "topFourProbabilities": [...]
    }
```

### 2. Lancez votre API Python

```bash
uvicorn main:app --reload --port 8000
```

### 3. Configurez l'URL de l'API

Créez un fichier `.env.local` à la racine :

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Les composants React utiliseront automatiquement votre API

Les appels API sont centralisés dans `/lib/api-config.ts` pour faciliter le changement d'URL.

## 📊 Structure des Données Attendues

### Prédictions

```typescript
{
  id: number,
  match: {
    date: "2024-02-24T15:00:00Z",
    homeTeam: "Paris Saint-Germain",
    awayTeam: "Lyon",
    league: "Ligue 1",
    stadium: "Parc des Princes"
  },
  probabilities: {
    home: 0.58,
    draw: 0.26,
    away: 0.16
  },
  prediction: "H", // 'H' | 'D' | 'A'
  confidence: 0.85,
  xG_home: 2.1,
  xG_away: 0.8,
  features: {
    homeFormRating: 4.2,
    awayFormRating: 2.8,
    homeAttack: 8.5,
    homeDefense: 7.2,
    awayAttack: 6.1,
    awayDefense: 6.8,
    headToHead: "PSG leads 15-3"
  }
}
```

### Statistiques

Voir `/lib/api-config.ts` pour la structure complète des types TypeScript.

### Simulations

Voir `/lib/api-config.ts` pour la structure complète.

## 🛠️ Développement

### Ajouter une nouvelle page

```bash
# Créez le dossier et fichier
mkdir app/ma-page
touch app/ma-page/page.tsx
```

```tsx
// app/ma-page/page.tsx
export default function MaPage() {
  return <h1>Ma nouvelle page</h1>
}
```

La route est automatiquement disponible à `/ma-page`

### Ajouter un composant

```tsx
// components/mon-composant.tsx
export function MonComposant() {
  return <div>Mon composant réutilisable</div>
}
```

```tsx
// Dans une page
import { MonComposant } from '@/components/mon-composant'

export default function Page() {
  return <MonComposant />
}
```

### Utiliser les hooks React

```tsx
'use client'

import { useState, useEffect } from 'react'

export default function MonComponent() {
  const [data, setData] = useState(null)

  useEffect(() => {
    // Code exécuté au chargement
    fetchData()
  }, [])

  return <div>{/* JSX ici */}</div>
}
```

## 📝 Scripts npm

```bash
npm run dev        # Lancer le serveur de développement
npm run build      # Compiler pour la production
npm start          # Lancer la version production
npm run lint       # Vérifier la qualité du code
```

## 🎨 Personnalisation du Design

### Couleurs

Modifiez `/app/globals.css` pour changer le thème de couleur.

### Tailwind CSS

Modifiez `tailwind.config.ts` pour étendre les styles.

## 📱 Responsive Design

L'interface est entièrement responsive :
- Mobile (< 640px)
- Tablet (640px - 1024px)
- Desktop (> 1024px)

## 🚀 Déploiement

### Déployer sur Vercel (recommandé - gratuit)

```bash
npm install -g vercel
vercel
```

### Déployer ailleurs

```bash
npm run build
npm start
```

## 📚 Ressources

- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev)
- [TypeScript Docs](https://typescriptlang.org/docs)
- [shadcn/ui](https://ui.shadcn.com)
- [Recharts](https://recharts.org)
- [Tailwind CSS](https://tailwindcss.com)

## 💡 Conseils

1. **Toujours utiliser le guide SETUP_LOCAL.md pour commencer**
2. **Les données mockées dans `/app/api/` sont pour le développement**
3. **Remplacez-les par votre API Python en production**
4. **Utilisez VS Code avec l'extension ESLint**
5. **Sauvegardez régulièrement avec Git**

## 📞 Support

Si vous avez des questions sur React ou Next.js :
- Consultez [SETUP_LOCAL.md](./SETUP_LOCAL.md)
- Vérifiez la console (F12) pour les erreurs
- Lisez les commentaires dans le code

## 📄 Licence

Ce projet est créé pour valoriser votre travail ML. Utilisez-le librement !

---

**Bon développement ! 🚀**

Votre interface Football BI Predictor est prête à montrer le pouvoir de votre modèle ML. 🎯
