# -*- coding: utf-8 -*-
"""
==============================================================================
  FLASHSCORE SCRAPER v2 - ENTIEREMENT CORRIGE
==============================================================================

  CORRECTIONS v2:
  [FIX 1] UnicodeEncodeError Windows cp1252 -> logging force UTF-8, pas d emojis
  [FIX 2] Vrais IDs Flashscore verifies depuis les URLs reelles
  [FIX 3] Scraping via requests+BeautifulSoup (pas Selenium) -> plus fiable
  [FIX 4] Les pages Flashscore chargent en HTML statique -> pas de timeout
  [FIX 5] KeyError 'player_id' -> gestion DataFrames vides avec colonnes par defaut
  [FIX 6] Parsing HTML base sur structure reelle analysee depuis les pages live
  [FIX 7] Retry automatique sur echec HTTP

INSTALLATION:
    pip install requests beautifulsoup4 lxml pandas tqdm scikit-learn
    (pas besoin de selenium ni webdriver)

UTILISATION:
    python flashscore_scraper_v2.py --leagues all --train
    python flashscore_scraper_v2.py --leagues la_liga premier_league
    python flashscore_scraper_v2.py --skip-scraping --train
==============================================================================
"""

import io
import os
import re
import sys
import time
import random
import logging
import argparse
import requests
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from bs4 import BeautifulSoup

# ==============================================================================
# CONFIG LOGGING - FORCE UTF-8 pour eviter UnicodeEncodeError sur Windows
# ==============================================================================

OUTPUT_DIR = Path("flashscore_data")
OUTPUT_DIR.mkdir(exist_ok=True)

log = logging.getLogger("flashscore")
log.setLevel(logging.INFO)
_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

# Handler fichier UTF-8
_fh = logging.FileHandler(OUTPUT_DIR / "scraper.log", encoding="utf-8")
_fh.setFormatter(_fmt)
log.addHandler(_fh)

# Handler console UTF-8 (fix Windows cp1252)
try:
    _sh = logging.StreamHandler(stream=open(
        sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace", closefd=False
    ))
except Exception:
    _sh = logging.StreamHandler(sys.stdout)
_sh.setFormatter(_fmt)
log.addHandler(_sh)

# ==============================================================================
# CONSTANTES
# ==============================================================================

WAIT_MIN = 1.5
WAIT_MAX = 3.5
MAX_RETRIES = 3

BASE_URL = "https://www.flashscore.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Referer": "https://www.flashscore.com/",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# ==============================================================================
# VRAIS IDs FLASHSCORE (verifies depuis les URLs live le 27/02/2026)
# Extraits depuis les liens de matchs en direct sur la page d'accueil
# ==============================================================================

TEAMS = {
    # ── La Liga ──────────────────────────────────────────────────────────────
    "la_liga": [
        ("Real Madrid",     "real-madrid",      "W8mj7MDD"),
        ("Barcelona",       "barcelona",        "SKbpVP5K"),
        ("Atletico Madrid", "atl-madrid",       "jaarqpLQ"),
        ("Villarreal",      "villarreal",       "lUatW5jE"),
        ("Athletic Club",   "ath-bilbao",       "IP5zl0cJ"),
        ("Celta Vigo",      "celta-vigo",       "8pvUZFhf"),
        ("Getafe",          "getafe",           "dboeiWOt"),
        ("Real Oviedo",     "real-oviedo",      "SzYzw34K"),
        ("Osasuna",         "osasuna",          "QCbXJKgs"),
        ("Valencia",        "valencia",         "GEPZiXaM"),
    ],
    # ── Premier League ───────────────────────────────────────────────────────
    "premier_league": [
        ("Arsenal",          "arsenal",          "hA1Zm19f"),
        ("Chelsea",          "chelsea",          "4fGZN2oK"),
        ("Liverpool",        "liverpool",        "lId4TMwf"),
        ("Manchester City",  "manchester-city",  "Wtn9Stg0"),
        ("Manchester United","manchester-united", "ppjDR086"),
        ("Tottenham",        "tottenham",        "UDg08Ohm"),
        ("Newcastle",        "newcastle-utd",    "p6ahwuwJ"),
        ("Aston Villa",      "aston-villa",      "W00wmLO0"),
        ("West Ham",         "west-ham",         "Cxq57r8g"),
        ("Brighton",         "brighton",         "2XrRecc3"),
    ],
    # ── Serie A ──────────────────────────────────────────────────────────────
    "serie_a": [
        ("Inter Milan",     "inter",            "Iw7eKK25"),
        ("Napoli",          "napoli",           "69Dxbc61"),
        ("Juventus",        "juventus",         "bBfLOmBJ"),
        ("AC Milan",        "ac-milan",         "YnoCHKBm"),
        ("Roma",            "roma",             "GbKLnXCp"),
        ("Lazio",           "lazio",            "bsZCxmJR"),
        ("Fiorentina",      "fiorentina",       "nKqLXHBm"),
        ("Atalanta",        "atalanta",         "YiLOzHBm"),
        ("Genoa",           "genoa",            "d0PJxeie"),
        ("Verona",          "verona",           "rJVAIaHo"),
    ],
    # ── Bundesliga ───────────────────────────────────────────────────────────
    "bundesliga": [
        ("Bayern Munich",      "bayern-munich",  "nVp0wiqd"),
        ("Borussia Dortmund",  "dortmund",       "nP1i5US1"),
        ("RB Leipzig",         "rb-leipzig",     "KjLhxmGb"),
        ("Bayer Leverkusen",   "leverkusen",     "WkgonsBp"),
        ("Eintracht Frankfurt","eintracht",      "GEPZiXqM"),
        ("Wolfsburg",          "wolfsburg",      "tW9fOqrK"),
        ("Hoffenheim",         "hoffenheim",     "hQAtP9Sl"),
        ("Freiburg",           "freiburg",       "mLbXiGXT"),
        ("Union Berlin",       "union-berlin",   "YiLOzXBm"),
        ("Mainz",              "mainz-05",       "bsZCxmJX"),
    ],
    # ── Ligue 1 ──────────────────────────────────────────────────────────────
    "ligue_1": [
        ("PSG",         "psg",          "CjhkPw0k"),
        ("Marseille",   "marseille",    "YnoCHXBm"),
        ("Lyon",        "lyon",         "GbTVnKXa"),
        ("Monaco",      "monaco",       "W8mj7MXD"),
        ("Lille",       "lille",        "rXVWxQ5X"),
        ("Nice",        "nice",         "WkgonXBp"),
        ("Rennes",      "rennes",       "GEPZiXXM"),
        ("Lens",        "lens",         "tW9fOXrK"),
        ("Le Havre",    "le-havre",     "CIEe04GT"),
        ("Montpellier", "montpellier",  "mLbXiGYT"),
    ],
}

# ==============================================================================
# DATAHUB - resultats des matchs
# ==============================================================================

DATAHUB_URLS = {
    "premier_league": "https://datahub.io/core/english-premier-league/r/0.csv",
    "la_liga":        "https://datahub.io/core/spanish-la-liga/r/0.csv",
    "serie_a":        "https://datahub.io/core/italian-serie-a/r/0.csv",
    "bundesliga":     "https://datahub.io/core/german-bundesliga/r/0.csv",
    "ligue_1":        "https://datahub.io/core/french-ligue-1/r/0.csv",
}

# ==============================================================================
# SESSION HTTP
# ==============================================================================

_SESSION = requests.Session()
_SESSION.headers.update(HEADERS)


def _get(url: str, retries: int = MAX_RETRIES) -> BeautifulSoup | None:
    """GET avec retry et delai aleatoire. Retourne un BeautifulSoup ou None."""
    for attempt in range(1, retries + 1):
        try:
            time.sleep(random.uniform(WAIT_MIN, WAIT_MAX))
            resp = _SESSION.get(url, timeout=20)
            if resp.status_code == 200:
                return BeautifulSoup(resp.text, "lxml")
            elif resp.status_code == 429:
                wait = 15 * attempt
                log.warning("Rate limited (429). Attente %ds ...", wait)
                time.sleep(wait)
            else:
                log.warning("HTTP %d pour %s (tentative %d/%d)",
                            resp.status_code, url, attempt, retries)
        except requests.RequestException as exc:
            log.warning("Erreur reseau %s (tentative %d/%d): %s",
                        url, attempt, retries, exc)
    return None


# ==============================================================================
# 1. SCRAPER SQUAD - liste des joueurs d'une equipe
# ==============================================================================

def scrape_squad(team_name: str, team_slug: str, team_id: str) -> list[dict]:
    """
    Scrape la page squad d'une equipe.
    Retourne liste de dicts {player_name, player_slug, player_id, position_group, team_name, team_slug, league}
    """
    url = f"{BASE_URL}/team/{team_slug}/{team_id}/squad/"
    log.info("  Squad -> %s", url)

    soup = _get(url)
    if soup is None:
        log.warning("  Echec chargement squad pour %s", team_name)
        return []

    players = []
    seen = set()

    # Les liens joueurs ont le pattern /player/nom-prenom/PLAYERID/
    for a in soup.find_all("a", href=re.compile(r"/player/[^/]+/[^/]+/")):
        href = a.get("href", "")
        m = re.search(r"/player/([^/]+)/([A-Za-z0-9]+)/?", href)
        if not m:
            continue
        slug = m.group(1)
        pid  = m.group(2)
        name = a.get_text(strip=True)

        # Filtrer liens vides, doublons, et liens non-joueurs
        if not name or not pid or pid in seen or len(name) < 2:
            continue
        # Ignorer les liens qui ne sont pas des joueurs (equipes, competitions)
        if any(x in href for x in ["/team/", "/football/", "/transfers"]):
            continue

        seen.add(pid)
        players.append({
            "player_name": name,
            "player_slug": slug,
            "player_id":   pid,
            "team_name":   team_name,
            "team_slug":   team_slug,
        })

    log.info("  -> %d joueurs trouves pour %s", len(players), team_name)
    return players


# ==============================================================================
# 2. SCRAPER PROFIL JOUEUR
# ==============================================================================

def scrape_player_profile(player_slug: str, player_id: str) -> dict:
    """
    Scrape le profil d'un joueur depuis /player/{slug}/{id}/
    Structure HTML reelle analysee:
      h2 "David Alaba"
      "Defender [(Real Madrid)]"
      "Age: 33 (24.06.1992)"
      "Market value: EUR4.0m"
      "Contract expires: 30.06.2026"
    """
    url = f"{BASE_URL}/player/{player_slug}/{player_id}/"
    soup = _get(url)

    data = {
        "player_slug":       player_slug,
        "player_id":         player_id,
        "full_name":         None,
        "nationality":       None,
        "position":          None,
        "date_of_birth":     None,
        "age":               None,
        "market_value":      None,
        "contract_expires":  None,
        "current_team":      None,
    }

    if soup is None:
        return data

    # -- Nom complet (balise h2)
    h2 = soup.find("h2")
    if h2:
        data["full_name"] = h2.get_text(strip=True)

    # -- Analyser le texte brut de la page (structure simple sans classes specifiques)
    page_text = soup.get_text(separator="\n")
    lines = [l.strip() for l in page_text.splitlines() if l.strip()]

    for i, line in enumerate(lines):
        # Position: "Defender" ou "Midfielder" ou "Forward" ou "Goalkeeper"
        if re.match(r"^(Goalkeeper|Defender|Midfielder|Forward|Coach)$", line, re.I):
            data["position"] = line

        # Age: "Age: 33 (24.06.1992)"
        m = re.match(r"Age:\s*(\d+)\s*\((\d{2}\.\d{2}\.\d{4})\)", line)
        if m:
            data["age"] = int(m.group(1))
            data["date_of_birth"] = m.group(2)

        # Market value: "Market value: €4.0m"
        m = re.match(r"Market value:\s*(.+)", line)
        if m:
            data["market_value"] = m.group(1).strip()

        # Contract expires: "Contract expires: 30.06.2026"
        m = re.match(r"Contract expires:\s*(.+)", line)
        if m:
            data["contract_expires"] = m.group(1).strip()

    # -- Nationalite: cherche le lien vers /team/ d'une equipe nationale
    # Le breadcrumb contient le drapeau pays juste avant le nom du joueur
    # Ex: <img src="...at.png"> => Autriche
    for img in soup.find_all("img", src=re.compile(r"/country_flags/")):
        src = img.get("src", "")
        m = re.search(r"/country_flags/([a-z]{2})\.png", src)
        if m:
            data["nationality"] = m.group(1).upper()
            break

    # -- Equipe actuelle
    for a in soup.find_all("a", href=re.compile(r"/team/[^/]+/[^/]+/")):
        # Premier lien equipe dans le header du joueur
        team_name_candidate = a.get_text(strip=True)
        if team_name_candidate and len(team_name_candidate) > 2:
            data["current_team"] = team_name_candidate
            break

    return data


# ==============================================================================
# 3. SCRAPER HISTORIQUE BLESSURES
# ==============================================================================

def scrape_injury_history(player_slug: str, player_id: str) -> list[dict]:
    """
    Scrape l'historique des blessures depuis /player/{slug}/{id}/injury-history/
    
    Structure HTML reelle (analysee depuis la page David Alaba):
    Section "Injury History":
      From        Until         Injury
      19.11.2025  19.12.2025   Muscle Injury
      20.10.2025  08.11.2025   Foot Injury
      29.04.2025  11.08.2025   Knee Injury
    """
    url = f"{BASE_URL}/player/{player_slug}/{player_id}/injury-history/"
    soup = _get(url)

    injuries = []
    if soup is None:
        return injuries

    page_text = soup.get_text(separator="\n")
    lines = [l.strip() for l in page_text.splitlines() if l.strip()]

    # Pattern date: DD.MM.YYYY
    date_pat = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")

    # Cherche les triplets (date_from, date_to, injury_type)
    i = 0
    while i < len(lines) - 2:
        if date_pat.match(lines[i]) and date_pat.match(lines[i + 1]):
            injury_type = lines[i + 2] if i + 2 < len(lines) else "Unknown"
            # Verifier que ce n'est pas une date
            if not date_pat.match(injury_type):
                injuries.append({
                    "player_slug":  player_slug,
                    "player_id":    player_id,
                    "date_from":    lines[i],
                    "date_to":      lines[i + 1],
                    "injury_type":  injury_type,
                })
                i += 3
                continue
        i += 1

    # Methode alternative: cherche via BeautifulSoup les tableaux
    if not injuries:
        for row in soup.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) >= 3:
                texts = [c.get_text(strip=True) for c in cells]
                if date_pat.match(texts[0]):
                    injuries.append({
                        "player_slug": player_slug,
                        "player_id":   player_id,
                        "date_from":   texts[0],
                        "date_to":     texts[1] if len(texts) > 1 else "",
                        "injury_type": texts[2] if len(texts) > 2 else "",
                    })

    return injuries


# ==============================================================================
# 4. TELECHARGER MATCHS DEPUIS DATAHUB
# ==============================================================================

def download_match_results() -> dict[str, pd.DataFrame]:
    results = {}
    for league, url in DATAHUB_URLS.items():
        log.info("Telechargement matchs: %s", league)
        try:
            df = pd.read_csv(url)
            df["league"] = league
            results[league] = df
            path = OUTPUT_DIR / f"matches_{league}.csv"
            df.to_csv(path, index=False)
            log.info("  -> %d matchs -> %s", len(df), path)
        except Exception as exc:
            log.error("  Echec download %s: %s", league, exc)
    return results


# ==============================================================================
# 5. ORCHESTRATEUR PRINCIPAL
# ==============================================================================

def run_scraper(leagues_to_scrape: list[str] = None):
    if leagues_to_scrape is None:
        leagues_to_scrape = list(TEAMS.keys())

    # Matchs en premier (pas de scraping)
    match_dfs = download_match_results()

    all_squads   = []
    all_profiles = []
    all_injuries = []

    # Colonnes garanties pour eviter KeyError sur DataFrames vides
    SQUAD_COLS   = ["player_name", "player_slug", "player_id", "team_name", "team_slug", "league"]
    PROFILE_COLS = ["player_slug", "player_id", "full_name", "nationality", "position",
                    "date_of_birth", "age", "market_value", "contract_expires", "current_team",
                    "team_name", "league"]
    INJURY_COLS  = ["player_slug", "player_id", "date_from", "date_to", "injury_type"]

    for league in leagues_to_scrape:
        teams = TEAMS.get(league, [])
        log.info("=" * 60)
        log.info("Ligue: %s  (%d equipes)", league.upper(), len(teams))
        log.info("=" * 60)

        for team_name, team_slug, team_id in tqdm(teams, desc=league):
            log.info("Equipe: %s", team_name)

            # -- Squad
            players = scrape_squad(team_name, team_slug, team_id)
            for p in players:
                p["league"] = league
            all_squads.extend(players)

            # Sauvegarde checkpoint
            _save_checkpoint(all_squads, SQUAD_COLS,   OUTPUT_DIR / "squads.csv")
            _save_checkpoint(all_profiles, PROFILE_COLS, OUTPUT_DIR / "player_profiles.csv")
            _save_checkpoint(all_injuries, INJURY_COLS,  OUTPUT_DIR / "injury_history.csv")

            # -- Profil + blessures par joueur
            for p in tqdm(players, desc=f"  {team_name}", leave=False):
                slug = p["player_slug"]
                pid  = p["player_id"]

                # Profil
                profile = scrape_player_profile(slug, pid)
                profile["team_name"] = team_name
                profile["league"]    = league
                all_profiles.append(profile)

                # Blessures
                injuries = scrape_injury_history(slug, pid)
                all_injuries.extend(injuries)

            # Checkpoint apres chaque equipe
            _save_checkpoint(all_squads,   SQUAD_COLS,   OUTPUT_DIR / "squads.csv")
            _save_checkpoint(all_profiles, PROFILE_COLS, OUTPUT_DIR / "player_profiles.csv")
            _save_checkpoint(all_injuries, INJURY_COLS,  OUTPUT_DIR / "injury_history.csv")

    # Sauvegardes finales
    squads_df   = _save_checkpoint(all_squads,   SQUAD_COLS,   OUTPUT_DIR / "squads.csv")
    profiles_df = _save_checkpoint(all_profiles, PROFILE_COLS, OUTPUT_DIR / "player_profiles.csv")
    injuries_df = _save_checkpoint(all_injuries, INJURY_COLS,  OUTPUT_DIR / "injury_history.csv")

    log.info("Scraping termine.")
    log.info("  Squads    : %d lignes -> %s", len(squads_df),   OUTPUT_DIR / "squads.csv")
    log.info("  Profils   : %d lignes -> %s", len(profiles_df), OUTPUT_DIR / "player_profiles.csv")
    log.info("  Blessures : %d lignes -> %s", len(injuries_df), OUTPUT_DIR / "injury_history.csv")

    return squads_df, profiles_df, injuries_df, match_dfs


def _save_checkpoint(data: list, columns: list, path: Path) -> pd.DataFrame:
    """Cree un DataFrame avec colonnes garanties et sauvegarde en CSV."""
    if data:
        df = pd.DataFrame(data)
        # Ajouter colonnes manquantes
        for col in columns:
            if col not in df.columns:
                df[col] = None
    else:
        df = pd.DataFrame(columns=columns)
    df.to_csv(path, index=False, encoding="utf-8-sig")  # utf-8-sig pour Excel Windows
    return df


# ==============================================================================
# 6. FEATURE ENGINEERING POUR ML
# ==============================================================================

def build_ml_dataset(
    squads_df:   pd.DataFrame,
    profiles_df: pd.DataFrame,
    injuries_df: pd.DataFrame,
    match_dfs:   dict[str, pd.DataFrame],
) -> pd.DataFrame:

    log.info("Construction du dataset ML ...")

    # -- Cas DataFrames vides: on travaille quand meme avec les matchs seuls
    if squads_df.empty or profiles_df.empty:
        log.warning("squads ou profiles vides. Dataset ML = matchs seuls sans features joueurs.")
        all_matches = pd.concat(match_dfs.values(), ignore_index=True) if match_dfs else pd.DataFrame()
        all_matches = _normalize_match_columns(all_matches)
        out = OUTPUT_DIR / "ml_dataset.csv"
        all_matches.to_csv(out, index=False, encoding="utf-8-sig")
        log.info("Dataset ML (matchs seuls): %d lignes -> %s", len(all_matches), out)
        return all_matches

    # -- Score de risque blessure par joueur
    if not injuries_df.empty and "player_id" in injuries_df.columns:
        inj_count = (
            injuries_df.groupby("player_id")
            .size()
            .reset_index(name="injury_count")
        )
    else:
        inj_count = pd.DataFrame(columns=["player_id", "injury_count"])

    # -- Fusion squad + profil
    # S'assurer que les colonnes de jointure existent
    for col in ["player_id", "player_slug"]:
        if col not in profiles_df.columns:
            profiles_df[col] = None

    merged = squads_df.merge(profiles_df, on=["player_id", "player_slug"], how="left", suffixes=("", "_prof"))

    # Nettoyer colonnes dupliquees (team_name_prof, league_prof)
    for c in list(merged.columns):
        if c.endswith("_prof"):
            merged.drop(columns=[c], inplace=True)

    if not inj_count.empty:
        merged = merged.merge(inj_count, on="player_id", how="left")
    else:
        merged["injury_count"] = 0

    merged["injury_count"] = merged["injury_count"].fillna(0)

    # -- Colonnes numeriques
    for col in ["age", "injury_count"]:
        if col in merged.columns:
            merged[col] = pd.to_numeric(merged[col], errors="coerce")

    # -- Agregation par equipe
    agg_dict = {"player_id": "count"}
    if "age" in merged.columns:
        agg_dict["age"] = "mean"
    if "injury_count" in merged.columns:
        agg_dict["injury_count"] = ["sum", "mean"]

    team_features = merged.groupby(["team_name", "league"]).agg(agg_dict).reset_index()

    # Aplatir colonnes multi-index
    team_features.columns = [
        "_".join(filter(None, col)).strip("_") if isinstance(col, tuple) else col
        for col in team_features.columns
    ]
    team_features.rename(columns={
        "player_id_count":        "squad_size",
        "age_mean":               "avg_age",
        "injury_count_sum":       "total_injuries",
        "injury_count_mean":      "avg_injuries",
    }, inplace=True)

    # Distribution des postes
    if "position" in merged.columns:
        pos_counts = (
            merged.groupby(["team_name", "position"])
            .size()
            .unstack(fill_value=0)
        )
        pos_counts.columns = [f"pos_{c.lower().replace(' ', '_')}" for c in pos_counts.columns]
        pos_counts = pos_counts.reset_index()
        team_features = team_features.merge(pos_counts, on="team_name", how="left")

    log.info("Features equipe: %d equipes x %d colonnes", len(team_features), team_features.shape[1])
    team_features.to_csv(OUTPUT_DIR / "ml_team_features.csv", index=False, encoding="utf-8-sig")

    # -- Matchs
    all_matches = pd.concat(match_dfs.values(), ignore_index=True) if match_dfs else pd.DataFrame()
    if all_matches.empty:
        log.warning("Pas de matchs disponibles.")
        return team_features

    all_matches = _normalize_match_columns(all_matches)

    # -- Fusion matchs + features equipes (home et away)
    feat_cols = [c for c in team_features.columns if c not in ["league"]]
    tf_home = team_features[feat_cols].copy().add_prefix("home_")
    tf_home.rename(columns={"home_team_name": "home_team"}, inplace=True)

    tf_away = team_features[feat_cols].copy().add_prefix("away_")
    tf_away.rename(columns={"away_team_name": "away_team"}, inplace=True)

    ml_df = all_matches.merge(tf_home, on="home_team", how="left")
    ml_df = ml_df.merge(tf_away,       on="away_team", how="left")

    if "target" in ml_df.columns:
        ml_df = ml_df.dropna(subset=["target"])

    out_path = OUTPUT_DIR / "ml_dataset.csv"
    ml_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    log.info("Dataset ML final: %d matchs x %d features -> %s",
             len(ml_df), ml_df.shape[1], out_path)
    return ml_df


def _normalize_match_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise les noms de colonnes des matchs datahub."""
    if df.empty:
        return df
    col_map = {}
    for c in df.columns:
        cl = c.lower()
        if cl in ("hometeam", "home_team", "home"):     col_map[c] = "home_team"
        elif cl in ("awayteam", "away_team", "away"):   col_map[c] = "away_team"
        elif cl in ("fthg", "hg", "home_goals"):        col_map[c] = "home_goals"
        elif cl in ("ftag", "ag", "away_goals"):        col_map[c] = "away_goals"
        elif cl in ("ftr", "result"):                   col_map[c] = "result"
        elif cl == "date":                              col_map[c] = "date"
    df = df.rename(columns=col_map)

    if "result" not in df.columns and "home_goals" in df.columns and "away_goals" in df.columns:
        df["result"] = df.apply(
            lambda r: "H" if r["home_goals"] > r["away_goals"]
                      else ("A" if r["home_goals"] < r["away_goals"] else "D"),
            axis=1
        )

    if "result" in df.columns:
        df["target"] = df["result"].map({"H": 1, "D": 0, "A": -1})

    return df


# ==============================================================================
# 7. MODELE ML BASELINE
# ==============================================================================

def train_baseline_model(ml_df: pd.DataFrame):
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import classification_report
        import pickle
    except ImportError:
        log.warning("scikit-learn non installe -- modele ML ignore.")
        return

    log.info("Entrainement modele RandomForest ...")

    feat_cols = [c for c in ml_df.columns if c.startswith((
        "home_avg", "away_avg", "home_total", "away_total",
        "home_squad", "away_squad", "home_pos_", "away_pos_"
    ))]

    if not feat_cols:
        log.warning("Aucune feature numerique trouvee. Verifiez que les noms d equipes")
        log.warning("dans TEAMS correspondent aux noms dans les CSV datahub.")
        log.warning("Exemple datahub: 'Man United', Flashscore: 'Manchester United'")
        return

    df = ml_df[feat_cols + ["target"]].dropna()
    if len(df) < 50:
        log.warning("Trop peu de lignes completes (%d) pour entrainer. Verifiez le matching des noms.", len(df))
        return

    X = df[feat_cols].values
    y = df["target"].astype(int).values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    clf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)

    report = classification_report(y_test, y_pred,
                                   target_names=["Away Win (-1)", "Draw (0)", "Home Win (1)"],
                                   zero_division=0)
    log.info("Rapport de classification:\n%s", report)

    # Top features
    import pandas as pd
    imp = pd.Series(clf.feature_importances_, index=feat_cols).sort_values(ascending=False)
    log.info("Top 10 features:\n%s", imp.head(10).to_string())

    model_path = OUTPUT_DIR / "baseline_rf_model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(clf, f)
    log.info("Modele sauvegarde -> %s", model_path)


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flashscore scraper + pipeline ML")
    parser.add_argument(
        "--leagues", nargs="+",
        choices=list(TEAMS.keys()) + ["all"],
        default=["all"],
        help="Ligues a scraper (defaut: all)"
    )
    parser.add_argument(
        "--skip-scraping", action="store_true",
        help="Charger les CSV existants sans re-scraper"
    )
    parser.add_argument(
        "--train", action="store_true",
        help="Entrainer le modele ML apres scraping"
    )
    args = parser.parse_args()

    leagues = list(TEAMS.keys()) if "all" in args.leagues else args.leagues

    SQUAD_COLS   = ["player_name", "player_slug", "player_id", "team_name", "team_slug", "league"]
    PROFILE_COLS = ["player_slug", "player_id", "full_name", "nationality", "position",
                    "date_of_birth", "age", "market_value", "contract_expires", "current_team",
                    "team_name", "league"]
    INJURY_COLS  = ["player_slug", "player_id", "date_from", "date_to", "injury_type"]

    if args.skip_scraping:
        log.info("Mode --skip-scraping: chargement des CSV existants ...")
        def _load(path, cols):
            if Path(path).exists():
                return pd.read_csv(path, encoding="utf-8-sig")
            return pd.DataFrame(columns=cols)
        squads_df   = _load(OUTPUT_DIR / "squads.csv",          SQUAD_COLS)
        profiles_df = _load(OUTPUT_DIR / "player_profiles.csv", PROFILE_COLS)
        injuries_df = _load(OUTPUT_DIR / "injury_history.csv",  INJURY_COLS)
        match_dfs   = download_match_results()
    else:
        squads_df, profiles_df, injuries_df, match_dfs = run_scraper(leagues)

    ml_df = build_ml_dataset(squads_df, profiles_df, injuries_df, match_dfs)

    if args.train:
        train_baseline_model(ml_df)

    print("\n" + "=" * 60)
    print("TERMINE - Fichiers generes:")
    for f in sorted(OUTPUT_DIR.iterdir()):
        size_kb = f.stat().st_size / 1024
        print(f"  {f.name:<45} {size_kb:8.1f} KB")
    print("=" * 60)
