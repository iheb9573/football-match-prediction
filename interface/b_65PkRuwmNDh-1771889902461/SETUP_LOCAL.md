# Guide Complet : Lancer Football BI Predictor en Local

Bienvenue ! Ce guide vous explique comment lancer votre interface Football BI Predictor sur votre PC local. **C'est votre première fois avec React ? Pas de problème, suivez chaque étape !**

## 📋 Prérequis

Avant de commencer, assurez-vous d'avoir :

1. **Node.js** (version 18+) - Téléchargez depuis [nodejs.org](https://nodejs.org)
2. **Git** - Pour cloner/télécharger le projet
3. **Un éditeur de code** - Recommandé : [Visual Studio Code](https://code.visualstudio.com)

### Vérifier l'installation

Ouvrez votre terminal/PowerShell et tapez :

```bash
node --version
npm --version
```

Vous devriez voir des numéros de version (ex: v18.17.0).

---

## 🚀 Étape 1 : Installer le Projet

### Option A : Depuis le fichier ZIP (si vous avez un ZIP)

1. Téléchargez le ZIP du projet
2. Extrayez-le n'importe où sur votre PC (ex: `C:\Users\VotreNom\Documents\Football-BI`)
3. Ouvrez le terminal à cet endroit

### Option B : Depuis GitHub (recommandé si vous avez accès)

```bash
git clone https://votre-repo-url.git
cd Football-BI-Predictor
```

---

## 📦 Étape 2 : Installer les Dépendances

Une fois que vous êtes dans le dossier du projet, installez toutes les librairies nécessaires :

```bash
npm install
```

**Expliqué simplement :**
- `npm` est le gestionnaire de paquets Node.js
- `npm install` télécharge toutes les librairies listées dans `package.json`
- Cela peut prendre 2-5 minutes la première fois

Attendez la fin. Vous verrez à la fin : `added XXX packages in Ys`

---

## 🎯 Étape 3 : Comprendre la Structure du Projet

```
Football-BI-Predictor/
├── app/                    # Pages de votre application React
│   ├── page.tsx           # Dashboard principal
│   ├── predictions/       # Page des prédictions
│   ├── simulations/       # Page des simulations
│   ├── statistics/        # Page des statistiques
│   ├── layout.tsx         # Structure générale
│   ├── globals.css        # Styles globaux
│   └── api/               # Backend simulé (pour dev local)
│       ├── predictions/
│       ├── statistics/
│       └── simulations/
├── components/            # Composants réutilisables
│   ├── prediction-card.tsx
│   ├── stats-overview.tsx
│   ├── simulation-dashboard.tsx
│   ├── navbar.tsx
│   └── ui/               # Composants UI shadcn
├── package.json          # Configuration du projet
├── tsconfig.json         # Configuration TypeScript
├── next.config.mjs       # Configuration Next.js
└── SETUP_LOCAL.md        # Ce fichier !
```

**Points clés :**
- Les fichiers `.tsx` sont du **React avec TypeScript**
- `app/` = vos pages (Next.js génère les routes automatiquement)
- `api/` = votre backend local (à remplacer par votre API Python)
- `components/` = morceaux de UI réutilisables

---

## ▶️ Étape 4 : Lancer le Serveur de Développement

Toujours dans le terminal, à la racine du projet :

```bash
npm run dev
```

**Que se passe-t-il :**
1. Next.js compile votre code React
2. Vous verrez : `◌ Ready in XXXms`
3. Le serveur démarre sur `http://localhost:3000`

**Vous verrez quelque chose comme :**

```
> next dev

  ▲ Next.js 16.1.6
  - Local:        http://localhost:3000
  - Environments: .env.local

✓ Ready in 2.5s
```

---

## 🌐 Étape 5 : Accéder à Votre Interface

Maintenant, ouvrez votre navigateur et allez à :

```
http://localhost:3000
```

**Vous devriez voir :**
- Barre de navigation professionnelle avec 4 sections
- Dashboard avec les graphiques des statistiques
- Données d'exemple pour jouer et tester

### Navigation disponible :

1. **Dashboard** (`/`) - Vue d'ensemble des performances du modèle
2. **Prédictions** (`/predictions`) - Matchs à venir avec probabilités
3. **Simulations** (`/simulations`) - Monte Carlo et champion projections
4. **Statistiques** (`/statistics`) - EDA et feature importance (SHAP)

---

## 🔄 Étape 6 : Mode Développement en Temps Réel

Le serveur de développement de Next.js a une feature magique : **Hot Module Replacement (HMR)**

**Cela signifie :**
- Quand vous modifiez un fichier et sauvegardez, l'interface se rafraîchit **automatiquement**
- Pas besoin de relancer manuellement
- Parfait pour tester rapidement vos changements

**Essayez :**
1. Ouvrez `/app/page.tsx`
2. Changez le texte d'un titre
3. Sauvegardez (Ctrl+S)
4. Regardez votre navigateur se rafraîchir instantanément !

---

## 🔌 Étape 7 : Connecter Votre API Python

**Actuellement**, le projet utilise des données mockées dans `/app/api/`.

Pour connecter votre vrai modèle Python :

### Option A : API REST Python (FastAPI/Flask)

1. **Créez une API Python** avec vos endpoints :

```python
# exemple avec FastAPI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Autorisez les requêtes du frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/predictions")
def get_predictions():
    # Vos prédictions du modèle ML
    return predictions_data

@app.get("/api/statistics")
def get_statistics():
    # Vos statistiques
    return stats_data

@app.get("/api/simulations")
def get_simulations():
    # Vos simulations Monte Carlo
    return simulations_data
```

2. **Lancez votre API Python** (sur le port 8000 par ex) :

```bash
uvicorn main:app --reload
```

3. **Modifiez les appels React** pour pointer vers votre API :

Dans les fichiers pages (`/app/predictions/page.tsx`, etc.), remplacez :

```javascript
// Avant (données mockées)
const res = await fetch('/api/predictions')

// Après (votre API Python)
const res = await fetch('http://localhost:8000/api/predictions')
```

### Option B : Proxy via Next.js

Modifiez `/app/api/predictions/route.ts` pour appeler votre backend Python directement.

---

## 🆘 Étape 8 : Dépannage Courant

### ❌ Erreur : "Port 3000 already in use"

```bash
# Solution : Utilisez un autre port
npm run dev -- -p 3001
```

Accédez à `http://localhost:3001`

### ❌ Erreur : "Cannot find module"

```bash
# Réinstallez les dépendances
npm install

# Ou effacez le cache et réinstallez
rm -rf node_modules package-lock.json
npm install
```

### ❌ Erreur : "TypeError: Cannot read property 'map' of undefined"

C'est généralement un problème d'async/await. Vérifiez que :
1. Vous attendez bien `fetch()`
2. Votre API retourne du JSON valide
3. La structure des données correspond

### ❌ Graphiques ne s'affichent pas

Vérifiez la console du navigateur :
1. Ouvrez DevTools (F12 ou Ctrl+Shift+I)
2. Allez à l'onglet "Console"
3. Cherchez les erreurs rouges

---

## 📝 Étape 9 : Commandes Utiles

```bash
# Lancer le serveur de développement
npm run dev

# Construire pour la production
npm build

# Lancer la version production (après build)
npm start

# Linter le code
npm run lint

# Arrêter le serveur (dans le terminal)
# Tapez : Ctrl + C
```

---

## 🎓 Concepts React pour Débutants

### Fichiers `.tsx`

- **T** = TypeScript (une version typée de JavaScript)
- **SX** = JSX (syntaxe HTML dans JavaScript)

```tsx
// Exemple simple
export default function MonComponent() {
  return <h1>Bonjour React !</h1>
}
```

### Hooks React Utilisés

1. **`useState`** - Gérer l'état local

```tsx
const [count, setCount] = useState(0)
// count = valeur actuelle
// setCount = fonction pour la changer
```

2. **`useEffect`** - Exécuter du code au chargement

```tsx
useEffect(() => {
  // Code exécuté au chargement du composant
  fetchData()
}, []) // [] = exécuter une seule fois
```

---

## 🚀 Prochaines Étapes

### Après avoir compris la structure :

1. **Déployer en ligne** sur Vercel (gratuit)

```bash
npm i -g vercel
vercel
```

2. **Ajouter une vraie base de données** pour les résultats
3. **Implémenter l'authentification** pour les utilisateurs
4. **Créer des exportations PDF** des rapports

---

## 📚 Ressources Utiles

- **Next.js Docs** : https://nextjs.org/docs
- **React Docs** : https://react.dev
- **TypeScript Basics** : https://typescriptlang.org/docs
- **shadcn/ui** : https://ui.shadcn.com (composants UI utilisés)
- **Recharts** : https://recharts.org (graphiques utilisés)

---

## 💡 Conseils Pro

1. **Utilisez VS Code Extensions :**
   - "ES7+ React/Redux/React-Native snippets"
   - "Prettier" (formattage de code)
   - "ESLint"

2. **Hot Reload en Action :**
   - Sauvegardez votre fichier (Ctrl+S)
   - L'interface se met à jour en 100ms

3. **Console Utile :**
   - F12 pour ouvrir les DevTools
   - Onglet "Network" pour voir les appels API
   - Onglet "Console" pour les erreurs/logs

4. **Git pour le contrôle de version :**
```bash
git add .
git commit -m "Ajout des visualisations BI"
git push
```

---

## 📞 Besoin d'aide ?

Si vous rencontrez des problèmes :

1. Vérifiez que Node.js est bien installé
2. Vérifiez que vous êtes dans le bon dossier
3. Supprimez `node_modules` et refaites `npm install`
4. Relancez le serveur avec `npm run dev`

Bon développement ! 🎉
