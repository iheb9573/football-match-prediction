# Démarrage Rapide : Football BI Predictor

**Résumé en 3 minutes pour les impatients !**

## C'est votre première fois avec React ?

Lisez d'abord : [SETUP_LOCAL.md](./SETUP_LOCAL.md) - C'est plus détaillé et expliqué étape par étape.

---

## Démarrage Rapide (≤ 5 min)

### 1. Prérequis
```bash
# Assurez-vous que Node.js est installé
node --version  # Doit afficher v18+
npm --version
```

### 2. Installer le projet
```bash
npm install
```

### 3. Lancer l'interface
```bash
npm run dev
```

### 4. Accéder à l'interface
Ouvrez votre navigateur : **http://localhost:3000**

Vous devriez voir un dashboard professionnel avec des graphiques ! 🎉

---

## Intégrer Votre Modèle Python

### Dans une autre fenêtre terminal :

**1. Créez votre API FastAPI**

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/predictions")
def get_predictions():
    # Retournez vos prédictions
    return [...]

@app.get("/api/statistics")
def get_statistics():
    # Retournez vos statistiques
    return {...}

@app.get("/api/simulations")
def get_simulations():
    # Retournez vos simulations Monte Carlo
    return {...}
```

**2. Installez FastAPI**

```bash
pip install fastapi uvicorn
```

**3. Lancez votre API**

```bash
uvicorn main:app --reload --port 8000
```

**4. Configurez l'URL**

Créez `.env.local` à la racine du projet React :

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**5. Redémarrez le frontend**

```bash
npm run dev
```

Voilà ! Votre interface est connectée à votre modèle ML ! 🚀

---

## Architecture en 30 secondes

```
FRONTEND (React)
├── http://localhost:3000
├── Dashboard des prédictions
└── Visualisations BI

         ↓

BACKEND (Python)
├── http://localhost:8000/api/predictions
├── http://localhost:8000/api/statistics
└── http://localhost:8000/api/simulations
```

---

## Commandes Principales

```bash
# Lancer le serveur React
npm run dev

# Compiler pour la production
npm run build

# Lancer la version production
npm start

# Vérifier la qualité du code
npm run lint
```

---

## Fichiers Importants

| Fichier | Purpose |
|---------|---------|
| `/app/page.tsx` | Dashboard principal |
| `/app/predictions/page.tsx` | Page des prédictions |
| `/app/simulations/page.tsx` | Page des simulations |
| `/app/statistics/page.tsx` | Page des statistiques |
| `/components/` | Composants réutilisables |
| `/app/api/` | API mockée (à remplacer par votre API Python) |
| `API_INTEGRATION_GUIDE.md` | Guide complet pour l'intégration |
| `SETUP_LOCAL.md` | Guide détaillé pour débutants |

---

## Dépannage Rapide

| Erreur | Solution |
|--------|----------|
| "Port 3000 déjà utilisé" | `npm run dev -- -p 3001` |
| "Module non trouvé" | `npm install` puis redémarrer |
| "API ne répond pas" | Vérifiez `NEXT_PUBLIC_API_URL` dans `.env.local` |
| "Graphiques vides" | Ouvrez F12 et vérifiez les erreurs console |

---

## Prochaines Étapes

1. **Intégrez votre modèle** - Voir `API_INTEGRATION_GUIDE.md`
2. **Personnalisez le design** - Tailwind CSS + composants
3. **Déployez** - `npm i -g vercel` puis `vercel`

---

## Liens Utiles

- **Guide complet** : [SETUP_LOCAL.md](./SETUP_LOCAL.md)
- **Intégration API** : [API_INTEGRATION_GUIDE.md](./API_INTEGRATION_GUIDE.md)
- **Documentation** : [README.md](./README.md)

---

**C'est tout ! Vous avez une interface professionnelle pour montrer votre modèle ML. 🎯**
