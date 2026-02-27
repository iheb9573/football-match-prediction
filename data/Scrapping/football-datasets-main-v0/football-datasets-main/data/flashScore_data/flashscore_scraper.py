import re
import time
import random
import csv
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus, urljoin

import requests
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

# =========================
# Config
# =========================
BASE = "https://www.flashscore.com"
OUT_TEAMS = "teams.csv"
OUT_PLAYERS = "players.csv"
OUT_INJURIES = "injuries.csv"

# DataHub core datasets (CSV)
LEAGUES = {
    "EPL": "english-premier-league",
    "LaLiga": "spanish-la-liga",
    "SerieA": "italian-serie-a",
    "Bundesliga": "german-bundesliga",
    "Ligue1": "french-ligue-1",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
}

TIMEOUT = 25
MIN_DELAY = 0.6
MAX_DELAY = 1.4
MAX_RETRIES = 4


# =========================
# Helpers
# =========================
def sleep_polite():
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


def req(session: requests.Session, url: str) -> str:
    """HTTP GET with retry + backoff. Returns text HTML."""
    last_err = None
    for i in range(MAX_RETRIES):
        try:
            r = session.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            return r.text
        except Exception as e:
            last_err = e
            backoff = (2 ** i) + random.random()
            time.sleep(backoff)
    raise RuntimeError(f"Failed GET after retries: {url}\nLast error: {last_err}")


def normalize_team_name(name: str) -> str:
    return re.sub(r"\s+", " ", str(name).strip())


def extract_team_id_from_team_url(team_url: str) -> Optional[str]:
    # https://www.flashscore.com/team/real-madrid/W8mj7MDD/
    m = re.search(r"/team/[^/]+/([A-Za-z0-9]+)/", team_url)
    return m.group(1) if m else None


def extract_player_id_from_player_url(player_url: str) -> Optional[str]:
    # https://www.flashscore.com/player/alaba-david/hKx3nCTp/
    m = re.search(r"/player/[^/]+/([A-Za-z0-9]+)/", player_url)
    return m.group(1) if m else None


# =========================
# Flashscore search (team resolver)
# =========================
def resolve_team_url_flashscore(session: requests.Session, team_name: str) -> Optional[str]:
    """
    Tries to resolve a team name to a Flashscore team URL.

    Primary approach: use Flashscore's internal search page.
    If Flashscore blocks it or changes it, we fallback to a lightweight approach:
    - try to directly guess via slug (not perfect)
    - you can then manually fix unmatched teams in teams.csv
    """
    q = quote_plus(team_name)
    # Common search endpoints seen on Flashscore installations:
    candidates = [
        f"{BASE}/search/?q={q}",
        f"{BASE}/search/{q}/",
        f"{BASE}/ajax/search/?q={q}",
        f"{BASE}/ajax/search/?term={q}",
    ]

    for u in candidates:
        try:
            html = req(session, u)
            soup = BeautifulSoup(html, "lxml")

            # Look for /team/.../<ID>/ links
            for a in soup.select('a[href*="/team/"]'):
                href = a.get("href", "")
                if "/team/" in href:
                    full = urljoin(BASE, href)
                    if re.search(r"/team/[^/]+/[A-Za-z0-9]+/?", full):
                        if not full.endswith("/"):
                            full += "/"
                        return full
        except Exception:
            continue

    # Fallback: naive slug guess (will often fail; keeps pipeline running)
    slug = re.sub(r"[^a-z0-9]+", "-", team_name.lower()).strip("-")
    guessed = f"{BASE}/team/{slug}/"
    return None  # better to force manual fix than scrape wrong team


# =========================
# Scrape squad
# =========================
@dataclass
class SquadPlayer:
    team_id: str
    team_name: str
    player_name: str
    player_url: str
    squad_role: str  # Goalkeepers/Defenders/Midfielders/Forwards/Coach/etc.


def scrape_team_squad(session: requests.Session, team_name: str, team_url: str) -> Tuple[str, List[SquadPlayer]]:
    """
    Given a team page URL, scrape squad from /squad/.
    Returns team_id, list of SquadPlayer.
    """
    if not team_url.endswith("/"):
        team_url += "/"
    squad_url = urljoin(team_url, "squad/")

    html = req(session, squad_url)
    soup = BeautifulSoup(html, "lxml")
    team_id = extract_team_id_from_team_url(team_url) or ""

    players: List[SquadPlayer] = []

    # The squad page is structured with headings like "Goalkeepers", "Defenders", etc.
    # We parse by scanning text blocks and collecting player links.
    current_role = "Unknown"

    # A robust way: iterate over elements in body order
    body = soup.body or soup
    for el in body.descendants:
        if getattr(el, "name", None) in ("h2", "h3", "div"):
            text = (el.get_text(" ", strip=True) if hasattr(el, "get_text") else "").strip()
            if text in {"Goalkeepers", "Defenders", "Midfielders", "Forwards", "Coach"}:
                current_role = text

        if getattr(el, "name", None) == "a":
            href = el.get("href", "")
            name = el.get_text(" ", strip=True)
            if href and name and "/player/" in href:
                full = urljoin(BASE, href)
                if not full.endswith("/"):
                    full += "/"
                players.append(
                    SquadPlayer(
                        team_id=team_id,
                        team_name=team_name,
                        player_name=name,
                        player_url=full,
                        squad_role=current_role,
                    )
                )

    # Deduplicate by player_url
    uniq = {}
    for p in players:
        uniq[p.player_url] = p
    return team_id, list(uniq.values())


# =========================
# Scrape player profile + injury history
# =========================
def parse_player_header_block(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    """
    Extracts fields visible near the top of player page:
    name, position, team, age, birthdate, market value, contract expires.
    This matches what Flashscore shows on the player page header.
    """
    text = soup.get_text("\n", strip=True)

    # Name: the first "## Name" in HTML is usually an h2
    h2 = soup.find(["h1", "h2"])
    name = h2.get_text(" ", strip=True) if h2 else None

    # Position and (Team) often appear on same line like: "Defender (Real Madrid)"
    # We'll find that line by searching for "(...)" near the name
    pos = team = None
    m = re.search(r"\n([A-Za-z ]+)\s+\(([^)]+)\)\n", "\n" + text + "\n")
    if m:
        pos = m.group(1).strip()
        team = m.group(2).strip()

    # Age line: "Age: 33 (24.06.1992)"
    age = birthdate = None
    m = re.search(r"Age:\s*([0-9]{1,3})\s*\(([^)]+)\)", text)
    if m:
        age = m.group(1)
        birthdate = m.group(2)

    # Market value: "Market value: €4.0m"
    market_value = None
    m = re.search(r"Market value:\s*([^\n]+)", text)
    if m:
        market_value = m.group(1).strip()

    # Contract expires: "Contract expires: 30.06.2026"
    contract_expires = None
    m = re.search(r"Contract expires:\s*([0-9]{2}\.[0-9]{2}\.[0-9]{4})", text)
    if m:
        contract_expires = m.group(1)

    # Nationality: breadcrumb often includes country name
    # Example shows "Austria" in breadcrumb area on the player page.
    nationality = None
    crumbs = [a.get_text(" ", strip=True) for a in soup.select("a") if a.get_text(strip=True)]
    # heuristic: if there is a country flag image like /country_flags/at.png, use the linked country name near top
    # We'll take first country-like token from the top of the page text lines after "Football"
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    for i, ln in enumerate(lines[:40]):
        if ln == "Football" and i + 1 < len(lines[:40]):
            # next token may be country name
            cand = lines[i + 1]
            if 2 <= len(cand) <= 30:
                nationality = cand
                break

    return {
        "player_name_page": name,
        "position": pos,
        "team_on_page": team,
        "age": age,
        "birthdate": birthdate,
        "market_value": market_value,
        "contract_expires": contract_expires,
        "nationality": nationality,
    }


def scrape_player(session: requests.Session, player_url: str) -> Dict[str, Optional[str]]:
    html = req(session, player_url)
    soup = BeautifulSoup(html, "lxml")
    data = parse_player_header_block(soup)
    data["player_url"] = player_url
    data["player_id"] = extract_player_id_from_player_url(player_url)
    return data


def scrape_injury_history(session: requests.Session, player_url: str) -> List[Dict[str, Optional[str]]]:
    if not player_url.endswith("/"):
        player_url += "/"
    ih_url = urljoin(player_url, "injury-history/")

    html = req(session, ih_url)
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text("\n", strip=True)

    # We parse lines under "Injury History"
    # Table is "From Until Injury" then rows like "19.11.2025 19.12.2025 Muscle Injury"
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    out = []

    # Find header index
    idx = None
    for i, ln in enumerate(lines):
        if ln == "Injury History":
            idx = i
            break
    if idx is None:
        return out

    # After it, there is usually a header line: "From Until Injury"
    # Then rows. We'll scan next ~200 lines for date-date-injury patterns.
    row_re = re.compile(r"^([0-9]{2}\.[0-9]{2}\.[0-9]{4})\s+([0-9]{2}\.[0-9]{2}\.[0-9]{4})\s+(.+)$")
    for ln in lines[idx:idx + 250]:
        m = row_re.match(ln)
        if m:
            out.append(
                {
                    "player_url": player_url,
                    "player_id": extract_player_id_from_player_url(player_url),
                    "from": m.group(1),
                    "until": m.group(2),
                    "injury": m.group(3).strip(),
                }
            )
    return out


# =========================
# Load DataHub + build team list
# =========================
def load_teams_from_datahub() -> pd.DataFrame:
    all_rows = []
    for league, url in LEAGUES.items():
        df = pd.read_csv(url)
        # DataHub schemas: usually columns "HomeTeam", "AwayTeam"
        home_col = next((c for c in df.columns if c.lower() in {"hometeam", "home team"}), None)
        away_col = next((c for c in df.columns if c.lower() in {"awayteam", "away team"}), None)
        if not home_col or not away_col:
            raise ValueError(f"Unexpected columns for {league}: {df.columns.tolist()}")

        teams = pd.unique(pd.concat([df[home_col], df[away_col]], ignore_index=True).dropna())
        for t in teams:
            all_rows.append({"league": league, "team_name": normalize_team_name(t)})

    out = pd.DataFrame(all_rows).drop_duplicates().sort_values(["league", "team_name"]).reset_index(drop=True)
    return out


# =========================
# Main pipeline
# =========================
def main():
    session = requests.Session()

    print("1) Load teams from DataHub...")
    teams_df = load_teams_from_datahub()
    teams_df["flashscore_team_url"] = None
    teams_df["flashscore_team_id"] = None
    teams_df.to_csv(OUT_TEAMS, index=False, encoding="utf-8")
    print(f"   -> {len(teams_df)} teams found. Saved: {OUT_TEAMS}")

    print("\n2) Resolve teams to Flashscore URLs (best effort)...")
    resolved = []
    for i, row in tqdm(teams_df.iterrows(), total=len(teams_df)):
        team_name = row["team_name"]
        team_url = resolve_team_url_flashscore(session, team_name)
        sleep_polite()
        team_id = extract_team_id_from_team_url(team_url) if team_url else None
        resolved.append((team_url, team_id))

    teams_df["flashscore_team_url"] = [r[0] for r in resolved]
    teams_df["flashscore_team_id"] = [r[1] for r in resolved]
    teams_df.to_csv(OUT_TEAMS, index=False, encoding="utf-8")
    print(f"   -> Updated: {OUT_TEAMS}")

    unresolved = teams_df["flashscore_team_url"].isna().sum()
    if unresolved > 0:
        print(
            f"\n⚠️ {unresolved} teams not resolved automatically.\n"
            f"   Ouvre {OUT_TEAMS} et remplis manuellement 'flashscore_team_url' pour ces équipes,\n"
            f"   puis relance le script (il continuera)."
        )

    print("\n3) Scrape squads + players + injuries...")
    players_rows = []
    injuries_rows = []

    # Only teams with a resolved url
    ok_df = teams_df.dropna(subset=["flashscore_team_url"]).copy()

    for _, trow in tqdm(ok_df.iterrows(), total=len(ok_df)):
        team_name = trow["team_name"]
        team_url = trow["flashscore_team_url"]
        try:
            team_id, squad_players = scrape_team_squad(session, team_name, team_url)
            sleep_polite()
        except Exception as e:
            print(f"[WARN] Squad failed for {team_name}: {e}")
            continue

        for sp in squad_players:
            # Player profile
            try:
                pdata = scrape_player(session, sp.player_url)
                sleep_polite()
            except Exception as e:
                print(f"[WARN] Player page failed {sp.player_url}: {e}")
                pdata = {"player_url": sp.player_url, "player_id": extract_player_id_from_player_url(sp.player_url)}

            row = {
                "league": trow["league"],
                "team_name_dataset": team_name,
                "team_id": team_id,
                "team_url": team_url,
                "squad_role": sp.squad_role,
                "player_name_squad": sp.player_name,
                **pdata,
            }
            players_rows.append(row)

            # Injury history
            try:
                ih = scrape_injury_history(session, sp.player_url)
                sleep_polite()
                injuries_rows.extend(
                    [{**x, "league": trow["league"], "team_id": team_id, "team_name_dataset": team_name} for x in ih]
                )
            except Exception as e:
                print(f"[WARN] Injury history failed {sp.player_url}: {e}")

    players_df = pd.DataFrame(players_rows).drop_duplicates(subset=["player_url"])
    injuries_df = pd.DataFrame(injuries_rows)

    players_df.to_csv(OUT_PLAYERS, index=False, encoding="utf-8")
    injuries_df.to_csv(OUT_INJURIES, index=False, encoding="utf-8")

    print(f"\nDone.\n- Players:  {OUT_PLAYERS} ({len(players_df)})\n- Injuries: {OUT_INJURIES} ({len(injuries_df)})")


if __name__ == "__main__":
    main()