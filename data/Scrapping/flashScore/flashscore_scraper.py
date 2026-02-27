"""
==============================================================================
  FLASHSCORE SCRAPER + ML DATASET BUILDER
  Scrape squad, player profiles & injury history from Flashscore
  then merge with match results from datahub.io for ML training
==============================================================================

REQUIREMENTS:
    pip install selenium webdriver-manager pandas requests tqdm

NOTE: Flashscore is heavily JS-rendered → we use Selenium with headless Chrome.
      Flashscore also blocks bots aggressively; we add random delays and
      realistic headers. For large-scale use consider residential proxies.
"""

import os
import re
import time
import json
import random
import logging
import requests
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from datetime import datetime

# Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# ─── CONFIG ────────────────────────────────────────────────────────────────────

OUTPUT_DIR = Path("flashscore_data")
OUTPUT_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(OUTPUT_DIR / "scraper.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

WAIT_MIN = 2.5   # seconds between requests (min)
WAIT_MAX = 5.0   # seconds between requests (max)

# ─── TEAMS PER LEAGUE ──────────────────────────────────────────────────────────
# Format: (team_name, flashscore_slug, flashscore_id)
# These are the top clubs across the 5 major European leagues.
# You can extend this list freely.

TEAMS = {
    # ── Premier League ──────────────────────────────────────────────────────
    "premier_league": [
        ("Arsenal",          "arsenal",           "W8mj7MDD"),  # placeholder IDs
        ("Chelsea",          "chelsea",           "GbTVnKga"),
        ("Liverpool",        "liverpool",         "YnoCHDBm"),
        ("Manchester City",  "manchester-city",   "h0BuXXur"),
        ("Manchester United","manchester-united",  "bBfMo8GJ"),
        ("Tottenham",        "tottenham",         "dL1ej7XS"),
        ("Newcastle",        "newcastle",         "YVmFmNZJ"),
        ("Aston Villa",      "aston-villa",       "fGjG0Msf"),
        ("West Ham",         "west-ham",          "8pFI4eMT"),
        ("Brighton",         "brighton",          "nhbzFe8e"),
    ],
    # ── La Liga ─────────────────────────────────────────────────────────────
    "la_liga": [
        ("Real Madrid",      "real-madrid",       "W8mj7MDD"),
        ("Barcelona",        "barcelona",         "rXVWxQ5q"),
        ("Atletico Madrid",  "atletico-madrid",   "Wkgon0Bp"),
        ("Sevilla",          "sevilla",           "nfTqWQ3k"),
        ("Real Sociedad",    "real-sociedad",     "QsHoLqNH"),
        ("Villarreal",       "villarreal",        "W2bJpGbH"),
        ("Athletic Club",    "athletic-club",     "EqKbHqXs"),
        ("Real Betis",       "real-betis",        "KjLhxmGo"),
        ("Valencia",         "valencia",          "GEPZiXaM"),
        ("Osasuna",          "osasuna",           "QCbXJKgs"),
    ],
    # ── Serie A ─────────────────────────────────────────────────────────────
    "serie_a": [
        ("Juventus",         "juventus",          "bBfLOmBJ"),
        ("AC Milan",         "ac-milan",          "YnoCHKBm"),
        ("Inter Milan",      "inter-milan",       "tW9fOarK"),
        ("Napoli",           "napoli",            "hLbXiGYT"),
        ("Roma",             "roma",              "GbKLnXCp"),
        ("Lazio",            "lazio",             "bsZCxmJR"),
        ("Fiorentina",       "fiorentina",        "nKqLXHBm"),
        ("Atalanta",         "atalanta",          "YiLOzHBm"),
        ("Torino",           "torino",            "mLbXiGZT"),
        ("Bologna",          "bologna",           "KjLhxmGs"),
    ],
    # ── Bundesliga ──────────────────────────────────────────────────────────
    "bundesliga": [
        ("Bayern Munich",    "bayern-munich",     "lIGBgO3h"),
        ("Borussia Dortmund","borussia-dortmund",  "YVmFmNXJ"),
        ("RB Leipzig",       "rb-leipzig",        "KjLhxmGb"),
        ("Bayer Leverkusen", "bayer-leverkusen",  "WkgonsBp"),
        ("Eintracht Frankfurt","eintracht-frankfurt","GEPZiXqM"),
        ("Wolfsburg",        "wolfsburg",         "tW9fOqrK"),
        ("Borussia Monchengladbach","monchengladbach","hLbXiGXT"),
        ("Freiburg",         "freiburg",          "mLbXiGXT"),
        ("Union Berlin",     "union-berlin",      "YiLOzXBm"),
        ("Mainz",            "mainz",             "bsZCxmJX"),
    ],
    # ── Ligue 1 ─────────────────────────────────────────────────────────────
    "ligue_1": [
        ("PSG",              "paris-sg",          "hLbXiGYX"),
        ("Marseille",        "marseille",         "YnoCHXBm"),
        ("Lyon",             "lyon",              "GbTVnKXa"),
        ("Monaco",           "monaco",            "W8mj7MXD"),
        ("Lille",            "lille",             "rXVWxQ5X"),
        ("Nice",             "nice",              "WkgonXBp"),
        ("Rennes",           "rennes",            "GEPZiXXM"),
        ("Lens",             "lens",              "tW9fOXrK"),
        ("Strasbourg",       "strasbourg",        "hLbXiGXT"),
        ("Montpellier",      "montpellier",       "mLbXiGYT"),
    ],
}

# ─── DATAHUB MATCH RESULTS ─────────────────────────────────────────────────────

DATAHUB_URLS = {
    "premier_league": "https://datahub.io/core/english-premier-league/r/0.csv",
    "la_liga":        "https://datahub.io/core/spanish-la-liga/r/0.csv",
    "serie_a":        "https://datahub.io/core/italian-serie-a/r/0.csv",
    "bundesliga":     "https://datahub.io/core/german-bundesliga/r/0.csv",
    "ligue_1":        "https://datahub.io/core/french-ligue-1/r/0.csv",
}

# ══════════════════════════════════════════════════════════════════════════════
#  SELENIUM DRIVER SETUP
# ══════════════════════════════════════════════════════════════════════════════

def build_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
    })
    return driver


def rand_sleep():
    time.sleep(random.uniform(WAIT_MIN, WAIT_MAX))


def accept_cookies(driver):
    """Dismiss Flashscore cookie banner if present."""
    try:
        btn = WebDriverWait(driver, 6).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        btn.click()
        time.sleep(1)
    except TimeoutException:
        pass


# ══════════════════════════════════════════════════════════════════════════════
#  1. SCRAPE SQUAD PAGE  →  list of (player_name, player_slug, player_id)
# ══════════════════════════════════════════════════════════════════════════════

def scrape_squad(driver, team_slug: str, team_id: str) -> list[dict]:
    url = f"https://www.flashscore.com/team/{team_slug}/{team_id}/squad/"
    log.info(f"  Squad page: {url}")
    driver.get(url)
    accept_cookies(driver)
    rand_sleep()

    players = []
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.squad__playerName, .playerTable__player a"))
        )
    except TimeoutException:
        log.warning(f"  Timeout loading squad for {team_slug}")
        return players

    # Try multiple CSS selectors (Flashscore changes its markup)
    anchors = driver.find_elements(By.CSS_SELECTOR, "a.squad__playerName")
    if not anchors:
        anchors = driver.find_elements(By.CSS_SELECTOR, ".playerTable__player a")
    if not anchors:
        anchors = driver.find_elements(By.CSS_SELECTOR, "a[href*='/player/']")

    seen = set()
    for a in anchors:
        href = a.get_attribute("href") or ""
        # href pattern: /player/lastname-firstname/PLAYERID/
        m = re.search(r"/player/([^/]+)/([^/]+)/?", href)
        if m and m.group(2) not in seen:
            seen.add(m.group(2))
            players.append({
                "player_name": a.text.strip(),
                "player_slug": m.group(1),
                "player_id":   m.group(2),
            })

    log.info(f"  → {len(players)} players found")
    return players


# ══════════════════════════════════════════════════════════════════════════════
#  2. SCRAPE PLAYER PROFILE  →  personal info + stats
# ══════════════════════════════════════════════════════════════════════════════

def scrape_player_profile(driver, player_slug: str, player_id: str) -> dict:
    url = f"https://www.flashscore.com/player/{player_slug}/{player_id}/"
    driver.get(url)
    rand_sleep()

    data = {
        "player_slug": player_slug,
        "player_id":   player_id,
        "full_name":   None,
        "nationality": None,
        "position":    None,
        "date_of_birth": None,
        "age":         None,
        "height_cm":   None,
        "market_value": None,
    }

    try:
        WebDriverWait(driver, 12).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".playerHeaderBox, .player__infoValue"))
        )
    except TimeoutException:
        return data

    # Name
    for sel in [".player__name", "h2.playerHeaderBox__name", ".playerHeader__nameWrapper"]:
        try:
            data["full_name"] = driver.find_element(By.CSS_SELECTOR, sel).text.strip()
            break
        except NoSuchElementException:
            pass

    # Info rows  (label → value pairs)
    labels = driver.find_elements(By.CSS_SELECTOR, ".player__infoLabel, .playerInfoItem__title")
    values = driver.find_elements(By.CSS_SELECTOR, ".player__infoValue, .playerInfoItem__value")
    for lbl, val in zip(labels, values):
        k = lbl.text.strip().lower()
        v = val.text.strip()
        if "nation" in k:
            data["nationality"] = v
        elif "position" in k:
            data["position"] = v
        elif "birth" in k or "age" in k:
            # might be "01.01.1995 (29)" → parse
            m = re.match(r"(\d{2}\.\d{2}\.\d{4})\s*(?:\((\d+)\))?", v)
            if m:
                data["date_of_birth"] = m.group(1)
                data["age"] = int(m.group(2)) if m.group(2) else None
        elif "height" in k:
            m = re.search(r"(\d+)", v)
            if m:
                data["height_cm"] = int(m.group(1))
        elif "value" in k or "market" in k:
            data["market_value"] = v

    return data


# ══════════════════════════════════════════════════════════════════════════════
#  3. SCRAPE INJURY HISTORY
# ══════════════════════════════════════════════════════════════════════════════

def scrape_injury_history(driver, player_slug: str, player_id: str) -> list[dict]:
    url = f"https://www.flashscore.com/player/{player_slug}/{player_id}/injury-history/"
    driver.get(url)
    rand_sleep()

    injuries = []
    try:
        WebDriverWait(driver, 12).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".injuryTable, .playerInjury__row, table.tableSectionContent")
            )
        )
    except TimeoutException:
        return injuries  # no injury data or page failed to load

    # Rows
    rows = driver.find_elements(By.CSS_SELECTOR, ".playerInjury__row, .injuryTable tr")
    for row in rows:
        cells = row.find_elements(By.CSS_SELECTOR, "td, .playerInjury__cell")
        if len(cells) >= 3:
            injuries.append({
                "player_slug":  player_slug,
                "player_id":    player_id,
                "season":       cells[0].text.strip() if len(cells) > 0 else None,
                "injury_type":  cells[1].text.strip() if len(cells) > 1 else None,
                "date_from":    cells[2].text.strip() if len(cells) > 2 else None,
                "date_to":      cells[3].text.strip() if len(cells) > 3 else None,
                "games_missed": cells[4].text.strip() if len(cells) > 4 else None,
            })

    return injuries


# ══════════════════════════════════════════════════════════════════════════════
#  4. DOWNLOAD MATCH RESULTS FROM DATAHUB
# ══════════════════════════════════════════════════════════════════════════════

def download_match_results() -> dict[str, pd.DataFrame]:
    results = {}
    for league, url in DATAHUB_URLS.items():
        log.info(f"Downloading match results: {league}")
        try:
            df = pd.read_csv(url)
            df["league"] = league
            results[league] = df
            path = OUTPUT_DIR / f"matches_{league}.csv"
            df.to_csv(path, index=False)
            log.info(f"  → {len(df)} matches saved to {path}")
        except Exception as e:
            log.error(f"  Failed to download {league}: {e}")
    return results


# ══════════════════════════════════════════════════════════════════════════════
#  5. ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════════════

def run_scraper(leagues_to_scrape: list[str] = None):
    """
    Main entry point.
    leagues_to_scrape: subset of TEAMS keys, or None for all.
    """
    if leagues_to_scrape is None:
        leagues_to_scrape = list(TEAMS.keys())

    # ── Download match results first (no Selenium needed) ──────────────────
    match_dfs = download_match_results()

    driver = build_driver()
    all_squads    = []
    all_profiles  = []
    all_injuries  = []

    try:
        for league in leagues_to_scrape:
            teams = TEAMS.get(league, [])
            log.info(f"\n{'='*60}")
            log.info(f"League: {league.upper()}  ({len(teams)} teams)")
            log.info('='*60)

            for team_name, team_slug, team_id in tqdm(teams, desc=league):
                log.info(f"\nTeam: {team_name}")

                # 1. Squad
                players = scrape_squad(driver, team_slug, team_id)
                for p in players:
                    p["team_name"]  = team_name
                    p["team_slug"]  = team_slug
                    p["league"]     = league
                all_squads.extend(players)

                # Save checkpoint after each team
                pd.DataFrame(all_squads).to_csv(OUTPUT_DIR / "squads.csv", index=False)

                # 2. Profile + injuries per player
                for p in tqdm(players, desc=f"  Players ({team_name})", leave=False):
                    slug = p["player_slug"]
                    pid  = p["player_id"]

                    profile = scrape_player_profile(driver, slug, pid)
                    profile.update({
                        "team_name": team_name,
                        "league":    league,
                    })
                    all_profiles.append(profile)

                    injuries = scrape_injury_history(driver, slug, pid)
                    all_injuries.extend(injuries)

                    # Checkpoint
                    pd.DataFrame(all_profiles).to_csv(OUTPUT_DIR / "player_profiles.csv", index=False)
                    pd.DataFrame(all_injuries).to_csv(OUTPUT_DIR / "injury_history.csv",  index=False)

    finally:
        driver.quit()

    # ── Final saves ────────────────────────────────────────────────────────
    squads_df   = pd.DataFrame(all_squads)
    profiles_df = pd.DataFrame(all_profiles)
    injuries_df = pd.DataFrame(all_injuries)

    squads_df.to_csv(  OUTPUT_DIR / "squads.csv",          index=False)
    profiles_df.to_csv(OUTPUT_DIR / "player_profiles.csv", index=False)
    injuries_df.to_csv(OUTPUT_DIR / "injury_history.csv",  index=False)

    log.info("\n✅ Scraping complete.")
    log.info(f"   Squads    : {len(squads_df)} rows   → {OUTPUT_DIR/'squads.csv'}")
    log.info(f"   Profiles  : {len(profiles_df)} rows → {OUTPUT_DIR/'player_profiles.csv'}")
    log.info(f"   Injuries  : {len(injuries_df)} rows → {OUTPUT_DIR/'injury_history.csv'}")

    return squads_df, profiles_df, injuries_df, match_dfs


# ══════════════════════════════════════════════════════════════════════════════
#  6. FEATURE ENGINEERING FOR ML
# ══════════════════════════════════════════════════════════════════════════════

def build_ml_dataset(
    squads_df:    pd.DataFrame,
    profiles_df:  pd.DataFrame,
    injuries_df:  pd.DataFrame,
    match_dfs:    dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """
    Merge match results with aggregated player features per team.
    Returns a flat DataFrame ready for ML training.
    """
    log.info("\nBuilding ML feature dataset …")

    # ── Injury risk score per player ────────────────────────────────────────
    if not injuries_df.empty:
        inj_count = (
            injuries_df.groupby("player_id")
            .size()
            .reset_index(name="injury_count")
        )
    else:
        inj_count = pd.DataFrame(columns=["player_id", "injury_count"])

    # ── Merge profiles with squad assignments ──────────────────────────────
    merged = squads_df.merge(profiles_df, on=["player_id", "player_slug"], how="left")
    merged = merged.merge(inj_count,      on="player_id",                  how="left")
    merged["injury_count"] = merged["injury_count"].fillna(0)

    # ── Aggregate per team ─────────────────────────────────────────────────
    # Numeric cols to aggregate
    num_cols = ["age", "height_cm", "injury_count"]
    for c in num_cols:
        if c not in merged.columns:
            merged[c] = None
    merged[num_cols] = merged[num_cols].apply(pd.to_numeric, errors="coerce")

    team_features = merged.groupby(["team_name", "league"]).agg(
        squad_size       = ("player_id",     "count"),
        avg_age          = ("age",           "mean"),
        avg_height_cm    = ("height_cm",     "mean"),
        total_injuries   = ("injury_count",  "sum"),
        avg_injuries     = ("injury_count",  "mean"),
    ).reset_index()

    # Position distribution
    if "position" in merged.columns:
        pos = (
            merged.groupby(["team_name", "position"])
            .size()
            .unstack(fill_value=0)
            .add_prefix("pos_")
            .reset_index()
        )
        team_features = team_features.merge(pos, on="team_name", how="left")

    # ── Match results ──────────────────────────────────────────────────────
    all_matches = pd.concat(match_dfs.values(), ignore_index=True) if match_dfs else pd.DataFrame()

    if all_matches.empty:
        log.warning("No match results downloaded — ML dataset will contain only team features.")
        team_features.to_csv(OUTPUT_DIR / "ml_team_features.csv", index=False)
        return team_features

    # Normalise column names  (datahub uses HomeTeam/AwayTeam/FTHG/FTAG/FTR)
    col_map = {}
    for c in all_matches.columns:
        cl = c.lower()
        if cl in ("hometeam", "home_team", "home"):     col_map[c] = "home_team"
        elif cl in ("awayteam", "away_team", "away"):   col_map[c] = "away_team"
        elif cl in ("fthg", "hg", "home_goals"):        col_map[c] = "home_goals"
        elif cl in ("ftag", "ag", "away_goals"):        col_map[c] = "away_goals"
        elif cl in ("ftr", "result"):                   col_map[c] = "result"
        elif cl in ("date",):                           col_map[c] = "date"
    all_matches = all_matches.rename(columns=col_map)

    # Ensure result column exists
    if "result" not in all_matches.columns and "home_goals" in all_matches.columns:
        all_matches["result"] = all_matches.apply(
            lambda r: "H" if r["home_goals"] > r["away_goals"]
                      else ("A" if r["home_goals"] < r["away_goals"] else "D"),
            axis=1
        )

    # Encode result as numeric target  H=1  D=0  A=-1
    result_map = {"H": 1, "D": 0, "A": -1}
    if "result" in all_matches.columns:
        all_matches["target"] = all_matches["result"].map(result_map)

    # Join home team features
    tf_home = team_features.add_prefix("home_").rename(columns={"home_team_name": "home_team"})
    tf_away = team_features.add_prefix("away_").rename(columns={"away_team_name": "away_team"})

    ml_df = all_matches.merge(tf_home, on="home_team", how="left")
    ml_df = ml_df.merge(tf_away,       on="away_team", how="left")

    # Drop rows with no target
    if "target" in ml_df.columns:
        ml_df = ml_df.dropna(subset=["target"])

    out_path = OUTPUT_DIR / "ml_dataset.csv"
    ml_df.to_csv(out_path, index=False)
    log.info(f"✅ ML dataset: {len(ml_df)} matches × {ml_df.shape[1]} features → {out_path}")

    # ── Quick summary ──────────────────────────────────────────────────────
    log.info(f"\nFeature columns:\n{list(ml_df.columns)}")

    return ml_df


# ══════════════════════════════════════════════════════════════════════════════
#  7. SAMPLE ML TRAINING (Random Forest baseline)
# ══════════════════════════════════════════════════════════════════════════════

def train_baseline_model(ml_df: pd.DataFrame):
    """Train a quick RandomForest baseline and print accuracy."""
    try:
        from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
        from sklearn.model_selection import train_test_split, cross_val_score
        from sklearn.preprocessing import LabelEncoder
        from sklearn.metrics import classification_report
        import numpy as np
    except ImportError:
        log.warning("scikit-learn not installed — skipping baseline model.")
        return

    log.info("\nTraining baseline RandomForest model …")

    feature_cols = [c for c in ml_df.columns if c.startswith(("home_avg", "away_avg",
                    "home_total", "away_total", "home_squad", "away_squad",
                    "home_pos_", "away_pos_"))]

    if not feature_cols:
        log.warning("No numeric features found — check team name matching between Flashscore and datahub.")
        return

    df = ml_df[feature_cols + ["target"]].dropna()
    if len(df) < 50:
        log.warning(f"Too few complete rows ({len(df)}) to train — check name matching.")
        return

    X = df[feature_cols].values
    y = df["target"].astype(int).values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    clf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    log.info("\n" + classification_report(y_test, y_pred, target_names=["Away Win", "Draw", "Home Win"]))

    # Feature importances
    imp = pd.Series(clf.feature_importances_, index=feature_cols).sort_values(ascending=False)
    log.info(f"\nTop 10 features:\n{imp.head(10)}")

    # Save model
    try:
        import pickle
        with open(OUTPUT_DIR / "baseline_rf_model.pkl", "wb") as f:
            pickle.dump(clf, f)
        log.info(f"Model saved to {OUTPUT_DIR / 'baseline_rf_model.pkl'}")
    except Exception as e:
        log.warning(f"Could not save model: {e}")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Flashscore → ML pipeline")
    parser.add_argument(
        "--leagues",
        nargs="+",
        choices=list(TEAMS.keys()) + ["all"],
        default=["all"],
        help="Leagues to scrape (default: all)"
    )
    parser.add_argument(
        "--skip-scraping",
        action="store_true",
        help="Skip scraping and load existing CSV files"
    )
    parser.add_argument(
        "--train",
        action="store_true",
        help="Train baseline ML model after scraping"
    )
    args = parser.parse_args()

    leagues = list(TEAMS.keys()) if "all" in args.leagues else args.leagues

    if args.skip_scraping:
        log.info("Loading existing CSV files …")
        squads_df   = pd.read_csv(OUTPUT_DIR / "squads.csv")          if (OUTPUT_DIR/"squads.csv").exists()          else pd.DataFrame()
        profiles_df = pd.read_csv(OUTPUT_DIR / "player_profiles.csv") if (OUTPUT_DIR/"player_profiles.csv").exists() else pd.DataFrame()
        injuries_df = pd.read_csv(OUTPUT_DIR / "injury_history.csv")  if (OUTPUT_DIR/"injury_history.csv").exists()  else pd.DataFrame()
        match_dfs   = download_match_results()
    else:
        squads_df, profiles_df, injuries_df, match_dfs = run_scraper(leagues)

    ml_df = build_ml_dataset(squads_df, profiles_df, injuries_df, match_dfs)

    if args.train:
        train_baseline_model(ml_df)

    print(f"\n{'='*60}")
    print("ALL DONE — output files:")
    for f in sorted(OUTPUT_DIR.iterdir()):
        size = f.stat().st_size / 1024
        print(f"  {f.name:40s}  {size:8.1f} KB")
    print('='*60)
