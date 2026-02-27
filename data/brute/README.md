# Données brutes préparées — Plan C (Serie A)

Ce dossier contient des fichiers CSV générés automatiquement à partir des datasets Serie A.

## Pourquoi Plan C ?

Les saisons récentes contiennent des statistiques riches (tirs, corners, fautes, cartons),
alors que les saisons anciennes (ex: années 90) ont souvent uniquement les colonnes "core"
(Date, équipes, buts, résultat) et beaucoup de colonnes 100% manquantes.

Plan C génère donc **2 datasets** :
1) **CORE** : utilisable sur toutes les saisons (colonnes stables).
2) **RICH** : utilisable sur saisons modernes (stats disponibles) + features temporelles (rolling).

## Fichiers générés

### 1) `seriea_core_all_seasons.csv`
- Contient : `Date, HomeTeam, AwayTeam, FTHG, FTAG, FTR, HTHG, HTAG, HTR, Season` (selon disponibilité)
- Objectif : modèle basique (ex: prédire FTR) sur toutes les saisons.

### 2) `seriea_rich_modern.csv`
- Contient CORE + stats additionnelles si disponibles :
  `HS, AS, HST, AST, HF, AF, HC, AC, HY, AY, HR, AR`
- Ajoute des features temporelles **sans fuite de données** :
  rolling mean sur les **5 derniers matchs** par équipe (home et away),
  calculé avec un `shift(1)` avant `rolling(...)` pour exclure le match courant.

## Remarques sur les colonnes

Les abréviations proviennent des datasets de football-data et sont des conventions courantes :
- FTHG/FTAG : buts à plein temps (home/away)
- HTHG/HTAG : buts à la mi-temps (home/away)
- HS/AS : tirs (home/away)
- HST/AST : tirs cadrés (home/away)
- HF/AF : fautes (home/away)
- HC/AC : corners (home/away)
- HY/AY : cartons jaunes (home/away)
- HR/AR : cartons rouges (home/away)
- FTR : résultat final (H=home win, D=draw, A=away win)

Certaines saisons peuvent avoir des colonnes absentes ou 100% manquantes (ex: Referee).
Ces colonnes sont supprimées automatiquement si elles sont entièrement NaN.

## Reproduire la génération

1) Vérifier le chemin des datasets dans le script :
   `DATASETS_DIR = ...\datasets\serie-a`

2) Lancer :
```bash
python plan_c_build_dataset.py



## Plan C — Build dataset (Serie A)

Le Plan C construit deux datasets propres à partir des fichiers bruts `datasets/serie-a/season-*.csv`.

### Outputs
Les fichiers sont enregistrés dans :

`data/brute/`

- `seriea_core_all_seasons.csv`  
  Colonnes : `Date, HomeTeam, AwayTeam, FTHG, FTAG, FTR, HTHG, HTAG, HTR, Season`

- `seriea_rich_modern.csv`  
  Même base + statistiques match : `HS, AS, HST, AST, HF, AF, HC, AC, HY, AY, HR, AR`  
  (Filtré uniquement sur les saisons où ces stats existent)

### Run
Activer l'environnement puis lancer :

```powershell
.venv\Scripts\Activate.ps1
python notebooks/nettoyage/plan_c_build_dataset.py
